from uuid import uuid4
from usdm4.api.study import Study
from usdm4.api.narrative_content import NarrativeContent
from usdm4.api.study_title import StudyTitle as USDMStudyTitle
from usdm_db.cross_reference import CrossReference
from usdm_db.errors_and_logging.errors_and_logging import ErrorsAndLogging
from usdm_db.document.utility import get_soup
from fhir.resources.composition import CompositionSection
from fhir.resources.narrative import Narrative
from fhir.resources.codeableconcept import CodeableConcept


class ToFHIR:
    EMPTY_DIV = '<div xmlns="http://www.w3.org/1999/xhtml"></div>'

    class LogicError(Exception):
        pass

    def __init__(self, study: Study, uuid: uuid4, extra: dict = {}):
        self.study = study
        print(f"KLASS: {type(self.study)}")
        self._uuid = uuid
        self._title_page = extra["title_page"]
        self._miscellaneous = extra["miscellaneous"]
        self._amendment = extra["amendment"]
        self._errors_and_logging = ErrorsAndLogging()
        self._cross_ref = CrossReference(study, self._errors_and_logging)
        self.study_version = study.versions[0]
        # print(f"KLASS: {type(self.study_version)}")
        self.study_design = self.study_version.studyDesigns[0]
        # print(f"KLASS: {type(self.study_design)}")
        self.protocol_document_version = self.study.documentedBy[0].versions[0]
        self.doc_title = self._get_official_title()

    def _content_to_section(self, content: NarrativeContent) -> CompositionSection:
        content_text = self._section_item(content)
        div = self._translate_references(content_text)
        # text = self._add_section_heading(content, div)
        text = str(div)
        text = self._remove_line_feeds(text)
        narrative = Narrative(status="generated", div=text)
        title = self._format_section_title(content.sectionTitle)
        code = CodeableConcept(text=f"section{content.sectionNumber}-{title}")
        title = content.sectionTitle if content.sectionTitle else "&nbsp;"
        # section = CompositionSection(title=f"{title}", code=code, text=narrative, section=[])
        section = self._composition_section(f"{title}", code, narrative)
        # if not narrative:
        #  print(f"EMPTY: {code.text}, {title}, {narrative}, {div}")
        if self._composition_section_no_text(section) and not content.childIds:
            return None
        else:
            for id in content.childIds:
                content = next(
                    (x for x in self.protocol_document_version.contents if x.id == id),
                    None,
                )
                child = self._content_to_section(content)
                if child:
                    section.section.append(child)
            return section

    def _section_item(self, content: NarrativeContent) -> str:
        return next(
            (
                x.text
                for x in self.study_version.narrativeContentItems
                if x.id == content.contentItemId
            ),
            "",
        )

    def _format_section_title(self, title: str) -> str:
        return title.lower().strip().replace(" ", "-")

    def _clean_section_number(self, section_number: str) -> str:
        return section_number[:-1] if section_number.endswith(".") else section_number

    def _translate_references(self, content_text: str):
        soup = get_soup(content_text, self._errors_and_logging)
        for ref in soup(["usdm:ref"]):
            try:
                attributes = ref.attrs
                instance = self._cross_ref.get(attributes["klass"], attributes["id"])
                value = self._resolve_instance(instance, attributes["attribute"])
                translated_text = self._translate_references(value)
                self._replace_and_highlight(ref, translated_text)
            except Exception as e:
                self._errors_and_logging.exception(
                    f"Exception raised while attempting to translate reference '{attributes}' while generating the FHIR message, see the logs for more info",
                    e,
                )
                self._replace_and_highlight(ref, "Missing content: exception")
        self._errors_and_logging.debug(
            f"Translate references from {content_text} => {get_soup(str(soup), self._errors_and_logging)}"
        )
        return get_soup(str(soup), self._errors_and_logging)

    def _resolve_instance(self, instance, attribute):
        dictionary = self._get_dictionary(instance)
        value = str(getattr(instance, attribute))
        soup = get_soup(value, self._errors_and_logging)
        for ref in soup(["usdm:tag"]):
            try:
                attributes = ref.attrs
                if dictionary:
                    entry = next(
                        (
                            item
                            for item in dictionary.parameterMaps
                            if item.tag == attributes["name"]
                        ),
                        None,
                    )
                    if entry:
                        self._replace_and_highlight(
                            ref, get_soup(entry.reference, self._errors_and_logging)
                        )
                    else:
                        self._errors_and_logging.error(
                            f"Missing dictionary entry while attempting to resolve reference '{attributes}' while generating the FHIR message"
                        )
                        self._replace_and_highlight(
                            ref, "Missing content: missing dictionary entry"
                        )
                else:
                    self._errors_and_logging.error(
                        f"Missing dictionary while attempting to resolve reference '{attributes}' while generating the FHIR message"
                    )
                    self._replace_and_highlight(
                        ref, "Missing content: missing dictionary"
                    )
            except Exception as e:
                self._errors_and_logging.exception(
                    f"Failed to resolve reference '{attributes} while generating the FHIR message",
                    e,
                )
                self._replace_and_highlight(ref, "Missing content: exception")
        return str(soup)

    def _replace_and_highlight(self, ref, text):
        ref.replace_with(text)

    def _get_dictionary(self, instance):
        try:
            return self._cross_ref.get(
                "SyntaxTemplateDictionary", instance.dictionaryId
            )
        except:
            return None

    def _add_section_heading(self, content: NarrativeContent, div) -> str:
        DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
        text = str(div)
        text = text.replace(
            DIV_OPEN_NS,
            f"{DIV_OPEN_NS}<p>{content.sectionNumber} {content.sectionTitle}</p>",
        )
        return text

    def _remove_line_feeds(self, div: str) -> str:
        text = div.replace("\n", "")
        return text

    def _get_official_title(self) -> USDMStudyTitle:
        title = self._get_title("Official Study Title")
        return title.text if title else ""

    def _get_title(self, title_type) -> USDMStudyTitle:
        for title in self.study_version.titles:
            if title.type.decode == title_type:
                return title
        return None

    def _composition_section_no_text(self, section):
        return section.text is None

    def _composition_section(self, title, code, narrative):
        # print(f"NARRATIVE: {narrative.div[0:50]}")
        narrative.div = self._clean_tags(narrative.div)
        if narrative.div == self.EMPTY_DIV:
            # print("EMPTY")
            return CompositionSection(title=f"{title}", code=code, section=[])
        else:
            return CompositionSection(
                title=f"{title}", code=code, text=narrative, section=[]
            )

    def _clean_tags(self, content):
        # print(f"Cleaning")
        before = content
        soup = get_soup(content, self._errors_and_logging)
        # 'ol' tag with 'type' attribute
        for ref in soup("ol"):
            try:
                attributes = ref.attrs
                if "type" in attributes:
                    ref.attrs = {}
            except Exception as e:
                self._errors_and_logging.exception(
                    "Exception raised cleaning 'ol' tags", e
                )
        # Styles
        for ref in soup("style"):
            try:
                ref.extract()
            except Exception as e:
                self._errors_and_logging.exception(
                    "Exception raised cleaning 'script' tags", e
                )
        # Images
        # for ref in soup('img'):
        #   try:
        #     ref.extract()
        #   except Exception as e:
        #     self._errors_and_logging.exception(f"Exception raised cleaning 'img' tags", e)
        # Empty 'p' tags
        for ref in soup("p"):
            try:
                if len(ref.get_text(strip=True)) == 0:
                    ref.extract()
            except Exception as e:
                self._errors_and_logging.exception(
                    "Exception raised cleaning empty 'p' tags", e
                )
        after = str(soup)
        # if before != after:
        #   print(f"Cleaning modified")
        return after
