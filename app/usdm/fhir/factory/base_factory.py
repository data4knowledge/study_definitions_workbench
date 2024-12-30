class BaseFactory():

  def fix_id(self, value: str) -> str:
    return value.replace('_', '-')