from uuid import uuid4


class URNUUID:
    @classmethod
    def generate(cls, value: str = None) -> str:
        return f"urn:uuid:{value}" if value else f"urn:uuid:{uuid4()}"
