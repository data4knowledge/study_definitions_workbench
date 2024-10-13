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

def restructure_study_list(data: list) -> dict:
  result = {}
  for k in data[0].keys():
    result[k] = tuple(d[k] for d in data)
  return result

def title_page_study_list_headings() -> list:
  return [
    ('Sponsor Confidentiality Statement', 'sponosr_confidentiality'), 
    ('Full Title:', 'full_title'), 
    ('Trial Acronym:', 'acronym'),
    ('Sponsor Protocol Identifier:', 'sponsor_protocol_identifier'), 
    ('Original Protocol:', 'original_protocol'),
    ('Version Number:', 'version_number'),
    ('Version Date:', 'version_date'),
    ('Amendment Identifier:', 'amendment_identifier'),
    ('Amendment Scope:', 'amendment_scope'),
    ('Compound Code(s):', 'compound_codes'),
    ('Compound Name(s):', 'compound_names'),
    ('Trial Phase:', 'trial_phase'),
    ('Short Title:', 'short_title'),
    ('Sponsor Name and Address:', 'sponsor_name'),
    ('', ''),
    ('Manufacturer Name and Address:', 'manufacturer_name_and_address'),
    ('Regulatory Agency Identifier Number(s):', 'regulatory_agency_identifiers'),
    ('Sponsor Approval:', 'sponsor_approval_date')
  ]