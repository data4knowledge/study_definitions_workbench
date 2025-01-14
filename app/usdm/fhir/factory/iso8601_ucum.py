import re


class ISO8601ToUCUM:
    @classmethod
    def convert(cls, value: str) -> dict:
        """Converts an ISO8601 duration value to the equivalent UCUM value.
        Returns a dictionary with fields 'value', 'code' and 'system'
        """
        result = {}
        match = re.search(r"^P(?P<value>\d+)(?P<unit>[Y|M|W|D])", value)
        if match:
            result = match.groupdict()
            result["unit"] = result["unit"].lower()
            result["system"] = "http://unitsofmeasure.org"
        match = re.search(r"^PT(?P<value>\d+)H", value)
        if match:
            result = match.groupdict()
            result["unit"] = "h"
            result["system"] = "http://unitsofmeasure.org"
        return result
