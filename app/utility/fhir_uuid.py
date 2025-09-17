import re

def extract_uuid(text: str) -> str:
    refs = re.findall(
        r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", text
    )
    return refs[0] if refs else None