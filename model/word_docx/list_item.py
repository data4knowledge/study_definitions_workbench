from d4kms_generic import application_logger

class ListItem():

  def __init__(self, text: str, level: int):
    self.text = text
    self.level = level

  def to_html(self):
    return f"{self.text}"

  def __str__(self):
    return f"[text='{self.text}', level='{self.level}']"
  

