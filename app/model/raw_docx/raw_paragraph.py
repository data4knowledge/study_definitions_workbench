import re

class RawParagraph():

  def __init__(self, text: str):
    self.text = text.strip()
    self.klasses = []

  def to_html(self) -> str:
    klass_list = ' '.join(self.klasses)
    open_tag = f'<p class="{klass_list}">' if self.klasses else '<p>'
    return f"{open_tag}{self.text}</p>"

  def find(self, text: str) -> bool:
    return True if text in self.text else False

  def find_at_start(self, text: str) -> bool:
    return True if self.text.upper().startswith(text.upper()) else False

  def add_class(self, klass) -> None:
    self.klasses.append(klass)

  def add_span(self, text: str, klass: str) -> None:
    print(f"SPAN 1: {self.text}")
    new_str = f'<span class="{klass}">{text}</span>'
    self.text = new_str + self.text[len(text):]
    print(f"SPAN 2: {self.text}")
