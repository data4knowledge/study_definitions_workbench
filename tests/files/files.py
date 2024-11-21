import json

def write_json(full_path, content):
  with open(full_path, 'w', encoding='utf-8') as f:
    f.write(json.dumps(json.loads(content), indent=2))

def read_json(full_path):  
  with open(full_path, 'r') as f:
    return json.dumps(json.load(f)) # Odd, but doing it for consistency of processing

