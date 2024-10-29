import re 
from pydantic import BaseModel
from app.model.database_tables import User as UserDB
from app.model.exceptions import FindException
from sqlalchemy.orm import Session
from d4kms_generic.logger import application_logger

class UserBase(BaseModel):
  identifier: str
  email: str
  display_name: str
  is_active: bool

class UserCreate(UserBase):
  pass

class User(UserBase):
  id: int
  
  class Config:
    from_attributes = True

  @classmethod
  def create(cls, identifier: str, email: str, display_name: str, session: Session) -> 'User':
    valid, validation = cls._is_valid(identifier=identifier, email=email, display_name=display_name)
    if valid:
      db_item = UserDB(identifier=identifier, email=email, display_name=display_name)
      session.add(db_item)
      session.commit()
      session.refresh(db_item)
      return cls(**db_item.__dict__), validation
    else:
      return None, validation
  
  @classmethod
  def find(cls, id: int, session: Session) -> 'User':
    db_item = session.query(UserDB).filter(UserDB.id == id).first()
    if db_item:
      return cls(**db_item.__dict__) 
    else:
      application_logger.error(f"Failed to find User with id '{id}'")
      raise FindException(cls, id)
    
  @classmethod
  def find_by_email(cls, email: str, session: Session):
    db_item = session.query(UserDB).filter(UserDB.email == email).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def find_by_identifier(cls, identifier: str, session: Session):
    db_item = session.query(UserDB).filter(UserDB.identifier == identifier).first()
    return cls(**db_item.__dict__) if db_item else None

  @classmethod
  def endpoints_page(cls, page: int, size: int, user_id: int, session: Session) -> list[dict]:
    page = page if page >= 1 else 1
    size = size if size > 0 else 10
    skip = (page - 1) * size
    user = session.query(UserDB).filter(UserDB.id == user_id).first()
    count = len(user.endpoints)
    data = user.endpoints[skip:skip+size]
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
    result = {'items': results, 'page': page, 'size': size, 'filter': '', 'count': count }
    return result

  @classmethod
  def check(cls, info: dict, session: Session):
    present_in_db = True
    #validation = cls.valid()
    user = cls.find_by_identifier(info['sub'], session)
    if not user:
      #print(f"USER: Not in DB")
      present_in_db = False
      dn = re.sub(r'[^a-zA-Z0-9]', '', info['nickname'])
      email = info['email'] if 'email' in info else 'No email'
      display_name = dn if dn else 'No display name'
      user, validation = cls.create(info['sub'], email, display_name, session)
    return user, present_in_db
  
  @classmethod
  def debug(cls, session: Session) -> list[dict]:
    count = session.query(UserDB).count()
    data = session.query(UserDB).all()
    results = []
    for db_item in data:
      results.append(db_item.__dict__)
      results[-1].pop('_sa_instance_state')
    result = {'items': results, 'count': count }
    return result

  def update_display_name(self, display_name: str, session: Session) -> 'User':
    db_item = session.query(UserDB).filter(UserDB.id == self.id).first()
    valid, validation = self.__class__._is_valid(db_item.identifier, db_item.email, display_name)
    if valid:
      db_item.display_name = display_name
      session.commit()
      session.refresh(db_item)
      return self.__class__(**db_item.__dict__), validation
    else:
      return None, validation
  
  @classmethod
  def valid(cls):
    return {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}}

  @staticmethod
  def _is_valid(identifier: str, email: str, display_name: str) -> tuple['UserDB', dict]:
    dn_validation = bool(re.match('[a-zA-Z0-9 ]+$', display_name))
    validation = {
      'display_name': {'valid': dn_validation, 'message': 'A display name should only contain alphanumeric characters or spaces' if not dn_validation else None},
      'email': {'valid': True, 'message': ''},
      'identifier': {'valid': True, 'message': ''}
    }
    valid = all(value['valid'] == True for value in validation.values())
    return valid, validation
