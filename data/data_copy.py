import json
from pathlib import Path
import shutil
import os

path = "mount/datafiles"

def make_dir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)

def read_json(filename):
  with open(filename, 'r') as f:
    data = json.load(f)
  return data

def get_study_name(filepath):
  study = read_json(filepath)
  return study['study']['name']

def list_and_copy(path=Path('.')):
  for entry in path.iterdir():
    if entry.is_file():
      if str(entry).endswith('usdm.json'):
        name = get_study_name(entry)
        dir = Path(f'data/{name}')
        make_dir(dir)
        dest = Path(f'data/{name}/usdm.json')
        shutil.copyfile(entry, dest)
        print(f'File {entry} copied to {dest}')
    elif entry.is_dir():
      list_and_copy(entry)
 
list_and_copy(Path(path))


