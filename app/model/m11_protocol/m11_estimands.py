from usdm_excel.globals import Globals
from app.model.raw_docx.raw_docx import RawDocx

# from app.model.raw_docx.raw_table import RawTable
from d4k_ms_base.logger import application_logger
from app.model.m11_protocol.m11_utility import *


class M11IEstimands:
    def __init__(self, raw_docx: RawDocx, globals: Globals):
        self._globals = globals
        self._raw_docx = raw_docx
        self._id_manager = self._globals.id_manager
        self._cdisc_ct_library = self._globals.cdisc_ct_library
        self.objectives = []

    def process(self):
        self.objectives = self._primary_objectives()

    def _primary_objectives(self):
        objectives = []
        main_section = self._raw_docx.target_document.section_by_number("3.1")
        if main_section:
            main_has_content = main_section.has_content()
            if main_has_content:
                application_logger.error(
                    "Invalid M11 document. Section 3.1 contains content when it should be empty."
                )
            else:
                sections = True
                section_number = 1
                while sections:
                    sub_section = self._raw_docx.target_document.section_by_number(
                        f"3.1.{section_number}"
                    )
                    if sub_section:
                        paras = sub_section.paragraphs()
                        if paras:
                            objective = {
                                "objective": sub_section.paragraphs()[0].to_html(),
                                "population": "",
                                "treatment": "",
                                "endpoint": "",
                                "population_summary": "",
                                "i_event": "",
                                "strategy": "",
                            }
                            tables = sub_section.tables()
                            if tables:
                                table = tables[0]
                                keys = {
                                    "population": "Population",
                                    "treatment": "Treatment",
                                    "endpoint": "Endpoint",
                                    "population_summary": "Population-Level Summary",
                                }
                                for key, text in keys.items():
                                    item = table_get_row(table, text)
                                    if item:
                                        objective[key] = item
                                        application_logger.info(
                                            f"Found estimands {key} -> {item}"
                                        )
                                item, index = table.find_row("Intercurrent Event")
                                if item:
                                    item, index = table.next(index)
                                    objective["i_event"] = item.cells[0].to_html()
                                    objective["strategy"] = item.cells[1].to_html()
                                    application_logger.info(
                                        "Found estimands event and strategy"
                                    )
                            objectives.append(objective)
                        section_number += 1
                    else:
                        sections = False
        else:
            application_logger.error(
                "Invalid M11 document. Section 3.1 is not present."
            )
        return objectives
