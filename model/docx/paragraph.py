class Paragraph():

  def __init__(self, text: str):
    self.text = text.strip()

  def to_html(self):
    return f"<p>{self.text}</p>"

