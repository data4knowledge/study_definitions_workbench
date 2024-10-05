from d4kms_generic.service_environment import ServiceEnvironment
from d4kms_generic.logger import application_logger

def root_url() -> str:
  se = ServiceEnvironment()
  return se.get('ROOT_URL')

def single_user() -> bool:
  se = ServiceEnvironment()
  single = se.get('SINGLE_USER')
  application_logger.info(f"Single user mode '{single}'")
  return single.upper() in ['TRUE', 'Y', 'YES']