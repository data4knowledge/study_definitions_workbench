import json
from pathlib import Path
import shutil
import os

path = "mount/datafiles"


def make_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def read_json(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def get_study_name(filepath):
    study = read_json(filepath)
    return study["study"]["name"]


def list_and_copy(path):
    key_file = "usdm.json"
    to_be_copied = ["usdm.json", "extra.yaml", "fhir_v2.json"]
    for entry in path.iterdir():
        if entry.is_file():
            if entry.name == key_file:
                dir_name = get_study_name(entry)
                dir = Path(f"data/{dir_name}")
                make_dir(dir)
                for file_name in to_be_copied:
                    src = Path(f"{path}/{file_name}")
                    dest = Path(f"data/{dir_name}/{file_name}")
                    try:
                        shutil.copyfile(src, dest)
                        print(f"File {src} copied to {dest}")
                    except Exception as e:
                        print(f"Exception raised copying file {e}")
        elif entry.is_dir():
            list_and_copy(entry)


list_and_copy(Path(path))
