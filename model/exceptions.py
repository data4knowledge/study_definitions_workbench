class FindException(Exception):

  def __init__(self, cls, id):
    self.msg = f"Failed to find '{cls.__name__}' with id '{id}'."

  def __str__(self):
    return self.msg