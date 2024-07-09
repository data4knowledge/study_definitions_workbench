from pydantic import BaseModel

class StudyBase(BaseModel):
  name: str

class StudyCreate(StudyBase):
  pass

class Study(StudyBase):
  id: int
  owner_id: int

  class Config:
      orm_mode = True