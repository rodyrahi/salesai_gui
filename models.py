from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    sub = Column(String, unique=True, index=True)  # Google unique ID
    name = Column(String)
    email = Column(String, unique=True, index=True)
    picture = Column(String)
