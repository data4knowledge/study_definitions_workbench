from usdm_model.study_title import StudyTitle


def is_official(self: StudyTitle) -> bool:
    return True if self.type.decode == "Official Study Title" else False


def is_acronym(self: StudyTitle) -> bool:
    return True if self.type.decode == "Study Acronym" else False


def is_short(self: StudyTitle) -> bool:
    return True if self.type.decode == "Brief Study Title" else False


setattr(StudyTitle, "is_official", is_official)
setattr(StudyTitle, "is_acronym", is_acronym)
setattr(StudyTitle, "is_short", is_short)
