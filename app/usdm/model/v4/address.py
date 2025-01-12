from usdm_model.address import Address


def set_text(self: Address) -> None:
    text = ""
    for attr in ["line", "city", "district", "state", "postalCode"]:
        text = _concat(text, self.__getattribute__(attr))
    self.text = _concat(text, self.country.decode) if self.country else text


@staticmethod
def _concat(text, value):
    if text:
        return text + ", " + value if value else text
    else:
        return value if value else ""


setattr(Address, "set_text", set_text)
