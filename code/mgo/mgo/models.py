from pyramid.security import (
    Allow,
    Everyone,
    )

from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Person(Base):
    __tablename__ = 'People'
    id = Column(Integer, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)
    age = Column(Integer)
    department = Column(Text)
    college = Column(Text)

    def __json__(self, request):
        return { 
            'id':self.id, 
            'first_name' : self.first_name, 
            'last_name' : self.last_name, 
            'age': self.age, 
            'department':self.department,
            'college':self.college,
            }

class Account(Base):
    __tablename__ = 'Accounts'
    id = Column(Integer, primary_key=True)
    username = Column(Text)
    password = Column(Text)

class RootFactory(object):
    __acl__ = [ (Allow, Everyone, 'view'),
                (Allow, 'group:editors', 'edit') ]
    def __init__(self, request):
        pass