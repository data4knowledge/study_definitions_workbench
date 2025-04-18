from app.model.raw_docx.raw_section import RawSection
from d4k_ms_base.logger import application_logger


class RawDocument:
    def __init__(self):
        self.sections = []
        self._levels = [0, 0, 0, 0, 0, 0]
        self._section_number_mapping = {}
        self._section_title_mapping = {}
        section = RawSection(None, None, 1)
        self.add(section, False)  # No section number increment

    def add(self, section: RawSection, increment=True):
        if increment:
            self._inc_section_number(section.level)
            section.number = self._get_section_number(section.level)
        self._section_number_mapping[section.number] = section
        self._section_title_mapping[section.title] = section
        self.sections.append(section)

    def current_section(self) -> RawSection:
        return self.sections[-1]

    def section_by_ordinal(self, ordinal: int) -> RawSection:
        if 1 >= ordinal <= len(self.sections):
            return self.sections[ordinal - 1]
        else:
            application_logger.error(
                f"Could not find section in ordinal position '{ordinal}'"
            )
            return None

    def section_by_number(self, section_number: str) -> RawSection:
        if section_number in self._section_number_mapping:
            return self._section_number_mapping[section_number]
        else:
            application_logger.error(
                f"Could not find section with number '{section_number}'"
            )
            return None

    def section_by_title(self, section_title: str) -> RawSection:
        if section_title in self._section_title_mapping:
            return self._section_title_mapping[section_title]
        else:
            application_logger.error(
                f"Could not find section with title '{section_title}'"
            )
            return None

    def _inc_section_number(self, level: int) -> None:
        try:
            self._levels[level] += 1
            for index in range(level + 1, len(self._levels)):
                self._levels[index] = 0
        except Exception as e:
            application_logger.exception(
                f"Failed to increment section number from levels '{self._levels}'", e
            )

    def _get_section_number(self, level: int) -> str:
        try:
            return ".".join(str(x) for x in self._levels[1 : level + 1])
        except Exception as e:
            application_logger.exception(
                f"Failed get section number from levels '{self._levels}'", e
            )
