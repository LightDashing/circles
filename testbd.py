from sqlalchemy import Column, INTEGER, Text, ForeignKey, VARCHAR, DateTime, Boolean, ARRAY
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TestTable(Base):
    __tablename__ = "testtable"
    id = Column(INTEGER, autoincrement=True, primary_key=True)
    strings = Column(ARRAY(VARCHAR(128)))


engine = create_engine('postgresql://postgres:***REMOVED***@localhost/postgres')
session = Session(bind=engine)
# session.add(TestTable(strings=["first_link", "second_link"]))
# session.commit()

# engine = create_engine('sqlite:///test.db')
#Base.metadata.create_all(engine)
