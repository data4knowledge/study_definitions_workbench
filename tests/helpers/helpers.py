import re

def fix_uuid(text):
  refs = re.findall(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', text)
  for ref in refs:
    text = text.replace(ref, 'FAKE-UUID')  
  return text