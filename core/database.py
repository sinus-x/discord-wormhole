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

class Guild(database.base):
	__tablename__ = 'guilds'

	id       = Column(BigInteger, primary_key=True)
	readonly = Column(Boolean,    default=False)
	nickname = Column(String,     default=None)
	cooldown = Column(Integer,    default=None)
	messages = Column(Integer,    default=0)

class GuildRepository:
	def add(self, id: int):
		session.add(Guild(id=id))
		session.commit()
	def get(self, id: int):
		return session.query(Guild).filter(Guild.id==id).one_or_none()
	def set(self, id: int, nickname: str = None, cooldown: int = None, readonly: bool = None, message: int = None):
		g = self.get(id)
		g_nickname = nickname if nickname else g.nickname
		g_cooldown = cooldown if cooldown else g.cooldown
		g_readonly = readonly if readonly else g.readonly
		g_messages = messages if messages else g.messages
		session.query(Guild).filter(Guild.id==id).update({
			Guild.nickname : g_nickname,
			Guild.cooldown : g_cooldown,
			Guild.readonly : g_readonly,
			Guild.messages : g_messages,
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

guildRepository = GuildRepository()
userRepository  = UserRepository()
logRepository   = LogRepository()
