from d4kms_generic.service_environment import ServiceEnvironment

def server_environment() -> str:
  se = ServiceEnvironment()
  name = se.get('ROOT_URL')
  if 'staging' in name:
    return 'STAGING'
  elif 'd4k-sdw' in name:
    return 'PRODUCTION'
  elif 'localhost' in name:
    return 'DEVELOPMENT'
  else:
    return name