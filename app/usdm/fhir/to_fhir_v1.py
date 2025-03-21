import datetime
from app.usdm.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference


class ToFHIRV1(ToFHIR):
    class LogicError(Exception):
        pass

    def to_fhir(self):
        try:
            sections = []
            content = self.protocol_document_version.contents[0]
            more = True
            while more:
                section = self._content_to_section(content)
                if section:
                    sections.append(section)
                content = next(
                    (
                        x
                        for x in self.protocol_document_version.contents
                        if x.id == content.nextId
                    ),
                    None,
                )
                more = True if content else False
            type_code = CodeableConcept(text="EvidenceReport")
            date_now = datetime.datetime.now(tz=datetime.timezone.utc)
            date_str = date_now.isoformat()
            author = Reference(display="USDM")
            composition = Composition(
                title=self.doc_title,
                type=type_code,
                section=sections,
                date=date_str,
                status="preliminary",
                author=[author],
            )
            identifier = Identifier(
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )
            bundle_entry = BundleEntry(
                resource=composition, fullUrl="https://www.example.com/Composition/1234"
            )
            bundle = Bundle(
                id=None,
                entry=[bundle_entry],
                type="document",
                identifier=identifier,
                timestamp=date_str,
            )
            return bundle.json()
        except Exception as e:
            self._errors_and_logging.exception(
                "Exception raised generating FHIR content. See logs for more details",
                e,
            )
            return None
