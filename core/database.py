from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class Database:
	def __init__(self):
		self.base = declarative_base()
		self.db   = create_engine("sqlite:///data.db")

database = Database()
session  = sessionmaker(database.db)()

class Settings(database.base):
	__tablename__ = 'settings'

	name         = Column(String,  primary_key=True)
	replace      = Column(Boolean, default=True)
	anonymity    = Column(String,  default='none')
	edit_time    = Column(Intger,  default=60)
	dead_time    = Column(Integer, default=0)
	dead_message = Column(String,  default=None)
	file_limit   = Column(Integer, default=-1)

class SettingsRepository:
	def add(self, str: name):
		session.add(Settings(name=name))
		session.commit()
	def set(self, str: name, replace: bool = None, anonymity: str = None, edit_time: int = None, dead_time: int = None, dead_message: str = None, file_limit: int = None):
		s = self.get(name)
		s_replace      = replace      if replace      else s.replace
		s_anonymity    = anonymity    if anonymity    else s.anonymity
		s_edit_time    = edit_time    if edit_time    else s.edit_time
		s_dead_time    = dead_time    if dead_time    else s.dead_time
		s_dead_message = dead_message if dead_message else s.dead_message
		s_file_limit   = file_limit   if file_limit   else s.file_limit
		session.query(Settings).filter(Settings.name==name).update({
			Settings.replace      : s_replace,
			Settings.anonymity    : s_anonymity,
			Settings.edit_time    : s_edit_time,
			Settings.dead_time    : s_dead_time,
			Settings.dead_message : s_dead_message,
			Settings.file_limit   : s_file_limit,
		})
		session.commit()

class Wormhole(database.base):
	__tablename__ = 'wormholes'

	id       = Column(BigInteger, primary_key=True)
	settings = Column(String,     foreignKey('settings.name', ondelete='CASCADE'))
	readonly = Column(Boolean,    default=False)
	nickname = Column(String,     default=None)
	cooldown = Column(Integer,    default=None)
	messages = Column(Integer,    default=0)

class WormholeRepository:
	def add(self, id: int):
		session.add(Wormhole(id=id))
		session.commit()
	def getAll(self):
		return session.query(Wormhole)
	def get(self, id: int):
		return session.query(Wormhole).filter(Wormhole.id==id).one_or_none()
	def set(self, id: int, nickname: str = None, cooldown: int = None, readonly: bool = None, message: int = None):
		g = self.get(id)
		g_nickname = nickname if nickname else g.nickname
		g_cooldown = cooldown if cooldown else g.cooldown
		g_readonly = readonly if readonly else g.readonly
		g_messages = messages if messages else g.messages
		session.query(Wormhole).filter(Wormhole.id==id).update({
			Wormhole.nickname : g_nickname,
			Wormhole.cooldown : g_cooldown,
			Wormhole.readonly : g_readonly,
			Wormhole.messages : g_messages,
		})
		session.commit()

class User(database.base):
	__tablename__ = 'users'

	id       = Column(BigInteger, primary_key=True)
	nickname = Column(String,     default=None    )
	mod      = Column(Boolean,    default=False   )
	cooldown = Column(Integer,    default=None    )
	readonly = Column(Boolean,    default=False   )
	banned   = Column(Boolean,    default=False   )

class UserRepository:
	def add(self, id: int):
		session.add(User(id=id))
		session.commit()
	def getAll(self):
		return session.query(User)
	def get(self, id: int):
		return session.query(User).filter(User.id==id).one_or_none()
	def set(self, id: int, nickname: str = None, mod: bool = None, cooldown: int = None,
				  readonly: bool = None, banned: bool = None):
		u = self.get(id)
		u_nickname = nickname if nickname else u.nickname
		u_mod      = mod      if mod      else u.mod
		u_cooldown = cooldown if cooldown else u.cooldown
		u_readonly = readonly if readonly else u.readonly
		u_banned   = banned   if banned   else u.banned
		session.query(User).filter(User.id==id).update({
			User.nickname : g_nickname,
			User.mod      : g_mod,
			User.cooldown : g_cooldown,
			User.readonly : g_readonly,
			User.banned   : g_banned,
		})
		session.commit()

class Log(database.base):
	__tablename__ = 'log'

	id        = Column(Integer,  primary_key=True, autoincrement=True)
	timestamp = Column(DateTime, default=datetime.now)
	author    = Column(BigInteger)
	table     = Column(String)
	key       = Column(String)
	old       = Column(String)
	new       = Column(String)

class LogRepository:
	def add(self, author: int, table: str, key: str, old: str, new: str):
		session.add(Log(author=author, table=table, key=key, old=old, new=new))
	def get(self, author: int = None, table: str = None, key: str = None, old: str = None, new: str = None):
		#TODO
		return

database.base.metadata.create_all(database.db)
session.commit()

repo_s = SettingsRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
repo_l = LogRepository()
