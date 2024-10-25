from d4kms_generic.service_environment import ServiceEnvironment
from d4kms_generic.logger import application_logger

def single_user() -> bool:
  se = ServiceEnvironment()
  single = se.get('SINGLE_USER')
  application_logger.info(f"Single user mode '{single}'")
  return single.upper() in ['TRUE', 'Y', 'YES']

def file_picker() -> dict:
  se = ServiceEnvironment()
  picker = se.get('FILE_PICKER')
  application_logger.info(f"File picker '{picker}'")
  return {'browser': picker.upper() == 'BROWSER', 'os': picker.upper() == 'OS', 'pfda': picker.upper() == 'PFDA'} 

  