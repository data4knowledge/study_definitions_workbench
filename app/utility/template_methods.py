from app.utility.environment import *

def server_name() -> str:
  name = root_url()
  if 'staging' in name:
    return 'STAGING'
  elif 'd4k-sdw' in name:
    return 'PRODUCTION'
  elif 'localhost' in name:
    return 'DEVELOPMENT'
  elif 'prism' in name:
    return 'PRISM'
  else:
    return name
  
def single_multiple() -> str:  
  return 'SINGLE' if single_user() else 'MULTIPLE'
