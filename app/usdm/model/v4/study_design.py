from usdm_model.study_design import StudyDesign
from usdm_model.activity import Activity
from usdm_model.study_epoch import StudyEpoch
from usdm_model.encounter import Encounter
from usdm_model.schedule_timeline import ScheduleTimeline
from app.usdm.model.v4.schedule_timeline import *


def soa(self: StudyDesign, timeline_name: str) -> list:
    timeline = next(
        (x for x in self.scheduleTimelines if x.name == timeline_name), None
    )
    return timeline.soa() if timeline else None


def main_soa(self: StudyDesign) -> list:
    timeline = next((x for x in self.scheduleTimelines if x.mainTimeline), None)
    return timeline.soa() if timeline else None


def first_activity(self: StudyDesign) -> Activity:
    return next((x for x in self.activities if not x.previousId and x.nextId), None)


def find_activity(self: StudyDesign, id: str) -> Activity:
    return next((x for x in self.activities if x.id == id), None)


def activity_list(self: StudyDesign) -> list:
    items = []
    item = self.first_activity()
    while item:
        items.append(item)
        item = self.find_activity(item.nextId)
    return items


def find_epoch(self: StudyDesign, id: str) -> StudyEpoch:
    return next((x for x in self.epochs if x.id == id), None)


def find_encounter(self: StudyDesign, id: str) -> Encounter:
    return next((x for x in self.encounters if x.id == id), None)


def find_timeline(self: StudyDesign, id: str) -> ScheduleTimeline:
    return next((x for x in self.scheduleTimelines if x.id == id), None)


setattr(StudyDesign, "soa", soa)
setattr(StudyDesign, "main_soa", main_soa)
setattr(StudyDesign, "first_activity", first_activity)
setattr(StudyDesign, "find_activity", find_activity)
setattr(StudyDesign, "activity_list", activity_list)
setattr(StudyDesign, "find_epoch", find_epoch)
setattr(StudyDesign, "find_encounter", find_encounter)
setattr(StudyDesign, "find_timeline", find_timeline)
