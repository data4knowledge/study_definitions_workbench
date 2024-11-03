from usdm_model.study_design import StudyDesign
from usdm_model.activity import Activity

def soa(self: StudyDesign, timeline_name: str) -> list:
  timeline = next((x for x in self.scheduleTimelines if x.name == timeline_name), None)
  return (True, timeline.soa()) if timeline else (False, None)


def first_activity(self: StudyDesign) -> Activity:
  return next((x for x in self.activities if not x.previousId and x.nextId), None)

setattr(StudyDesign, 'soa', soa)
setattr(StudyDesign, 'first_activity', first_activity)
