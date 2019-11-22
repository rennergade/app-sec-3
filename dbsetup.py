import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


def get_date():
    return datetime.datetime.now()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    password = Column(String(256), nullable=False)
    twofa = Column(String(256), nullable=False)

class Log(Base):
    __tablename__ = 'log'

    username = Column(String(64), nullable=False)
    id = Column(Integer, primary_key=True)
    logtype = Column(String(16), nullable=False)
    time = Column(Date, default=get_date)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

class Spell(Base):
    __tablename__ = 'results'

    username = Column(String(64), nullable=False)
    id = Column(Integer, primary_key=True)
    subtext = Column(Text, nullable=False)
    restext = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



engine = create_engine('sqlite:///spell.db')


Base.metadata.create_all(engine)
