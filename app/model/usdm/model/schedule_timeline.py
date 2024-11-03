from usdm_model.schedule_timeline import ScheduleTimeline
from usdm_model.study_design import StudyDesign
from usdm_model.scheduled_instance import ScheduledActivityInstance
from usdm_model.timing import Timing
from d4kms_generic.logger import application_logger

def first_timepoint(self: ScheduleTimeline) -> ScheduledActivityInstance:
  return next((x for x in self.instances if not x.previousId and x.nextId), None)

def find_timepoint(self: ScheduleTimeline, id: str) -> ScheduledActivityInstance:
  return next((x for x in self.instances if x.id == id), None)

def timepoint_list(self: ScheduleTimeline) -> list:
  items = []
  item = self.first_timepoint()
  while item:
    items.append(item)
    item = self.find_timepoint(item.nextId)
  return items

def find_timing_from(self: ScheduleTimeline, id: str) -> Timing:
  return next((x for x in self.timings if x.relativeFromScheduledInstanceId == id), None)

def soa(self: ScheduleTimeline, study_design: StudyDesign) -> list:

  # Activities
  activity_order = study_design.activity_list()

  # Epochs and Visits
  ai = []
  timepoints = self.timepoint_list()
  for timepoint in timepoints:
    timing = self.find_timing_from(timepoint.id)
    encounter = study_design.find_encounter(timepoint.id)
    epoch = study_design.find_epoch(timepoint.id)
    entry = {
      'instance': timepoint,
      'timing': timing,
      'epoch': epoch,
      'encounter': encounter
    }
    ai.append(entry)

  # Blank row
  visit_row = {}
  for item in ai:
    visit_row[item['instance'].id] = ''
  
  # Activities
  activities = {}
  for activity in activity_order:
    activities[activity.name] = visit_row.copy()
    for timepoint in timepoints:
      if activity.id in timepoint.activityIds:
        activities[activity.name][timepoint.id] = "X" 
  
  # Return the results
  labels = []
  for item in ai:
    label = item['encounter'].label if item['encounter'].label else item['instance'].label
    labels.append(label)
  results = []
  results.append([""] + [item['epoch'].label for item in ai])
  results.append([""] + labels)
  results.append([""] + [item['instance'].label for item in ai])
  results.append([""] + [item['instance'].windowLabel for item in ai])
  for activity in activity_order:
    if activity.name in activities:
      data = activities[activity.name]
      label = activity.label if activity.label else activity.name
      results.append([{'name': label, 'uuid': activity['uuid']}] + list(data.values()))
  return results

setattr(ScheduleTimeline, 'first_timepoint', first_timepoint)
setattr(ScheduleTimeline, 'find_timepoint', find_timepoint)
setattr(ScheduleTimeline, 'timepoint_list', timepoint_list)
setattr(ScheduleTimeline, 'find_timing_from', find_timing_from)
setattr(ScheduleTimeline, 'soa', soa)
