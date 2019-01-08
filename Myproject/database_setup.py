import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class dept(Base):
    __tablename__ = 'dept'

    dept_id = Column(Integer, primary_key=True)
    Deptname = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'dept_id': self.dept_id,
            'Deptname': self.Deptname,
            
        }


class students(Base):
    __tablename__ = 'students'

    name = Column(String(80), nullable=False)
    stdid = Column(Integer, primary_key=True)
   
    dept_id = Column(Integer, ForeignKey('dept.dept_id'))
    dept = relationship(dept)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'stdid': self.stdid,
            
        }


engine = create_engine('sqlite:///deptmenu.db')


Base.metadata.create_all(engine)
