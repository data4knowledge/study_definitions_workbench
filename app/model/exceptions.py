class FindException(Exception):
    def __init__(self, cls, id):
        self.msg = f"Failed to find '{cls.__name__}' with id '{id}'."

    def __str__(self):
        return self.msg


class USDMLoadException(Exception):
    """A stored or uploaded file failed to load into the usdm4 model.

    ``problems`` holds one readable line per validation error, each
    naming the field path and the reason (e.g. ``study.id: Input should
    be a valid UUID ...``)."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        self.msg = "; ".join(problems)

    def __str__(self):
        return self.msg
