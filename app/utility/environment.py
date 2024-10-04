from d4kms_generic.service_environment import ServiceEnvironment

def root_url() -> str:
  se = ServiceEnvironment()
  return se.get('ROOT_URL')

def single_user() -> bool:
  se = ServiceEnvironment()
  return bool(se.get('SINGLE_USER'))