import json
import yaml


def write_json(full_path, content):
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(json.loads(content), indent=2)
        )  # Content expected to be string, no formatting


def read_json(full_path):
    with open(full_path, "r") as f:
        return json.dumps(json.load(f), indent=2)  # Return pretty printed version


def read_excel(full_path):
    with open(full_path, "rb") as f:
        return f.read()


def read_word(full_path):
    with open(full_path, "rb") as f:
        return f.read()


def read_yaml(full_path):
    data = open(full_path)
    return yaml.load(data, Loader=yaml.FullLoader)


def write_yaml(full_path, data):
    with open(full_path, "w") as f:
        return yaml.dump(data, f, default_flow_style=False)
