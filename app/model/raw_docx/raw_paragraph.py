class RawParagraph():

  def __init__(self, text: str):
    self.text = text.strip()
    self.klasses = []

  def to_html(self):
    klass_list = ' '.join(self.klasses)
    open_tag = f'<p class="{klass_list}">' if self.klasses else '<p>'
    return f"{open_tag}{self.text}</p>"

  def find(self, text):
    return True if text in self.text else False

  def add_class(self, klass):
    self.klasses.append(klass)