import datetime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import (
    Index, Column, Boolean, String, Integer, Float, Unicode, DateTime, Binary, ForeignKey,
    create_engine
)
from sqlalchemy.orm import sessionmaker, relationship, backref

def initialize(fname):
    engine = create_engine('sqlite:///%s' % fname)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

Base = declarative_base()

# Common mixin class that stores some shared columns or tablename defination
class SpookMixin(object):

	@declared_attr
	def __tablename__(cls):
	    return cls.__name__.lower()

	id = Column(Integer, primary_key=True)
	created_at = Column(DateTime, default=datetime.datetime.now, index=True)

class Click(SpookMixin, Base):
	button = Column(String(32), nullable=False)
	x = Column(Integer, nullable=False)
	y = Column(Integer, nullable=False)

	def __init__(self, button, x, y):
		self.button = button
		self.x = x
		self.y = y


	def __repr__(self):
		return "<Click (%d, %d), (%s)>" % (self.x, self.y, self.button)

class Idle(SpookMixin, Base):
	idle_time = Column(Float, nullable=False)
	mode = Column(String(32), nullable=False)
	def __init__(self, idle_time, mode):
		self.mode = mode
		self.idle_time = idle_time

	def __repr__(self):
		if self.mode == "keyboard":
			return "<Keyboard Idle for %fs>" % (self.idle_time)
		elif self.mode == "mouse":
			return "<Mouse Idle for %fs>" % (self.idle_time)

class Ditrigraph(SpookMixin, Base):
	ditrigraph = Column(String(32), nullable=False)
	mode = Column(String(32), nullable=False)

	def __init__(self, ditrigraph, mode):
		self.ditrigraph = ditrigraph
		self.mode = mode

	def __repr__(self):
		if self.mode == "digraph":
			return "<Got %s : %s>" % (self.mode, self.ditrigraph)
		elif self.mode == "trigraph":
			return "<Got %s : %s>" % (self.mode, self.ditrigraph)

class Move(SpookMixin, Base):
	time = Column(Float, nullable=False)
	nrmoves = Column(Integer, nullable=False)

	def __init__(self, time, nrmoves):
		self.time = time
		self.nrmoves = nrmoves


	def __repr__(self):
		return "<Move for %fs and %d distance>" % (self.time, self.nrmoves)

class Keys(SpookMixin, Base):
	text = Column(Binary, nullable=False)
	holding = Column(Boolean, nullable=False)
	time = Column(Float)

	def __init__(self, text, holding, args):
		self.text = text
		self.holding = holding
		if self.holding:
			self.time = args[0]
	def __repr__(self):
		if self.holding:
			return "<Key %s hold for %f>" % (self.text, self.time)
		else:
			return "<Key %s pressed>" % (self.text)