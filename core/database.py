from sqlalchemy import create_engine, MetaData, Table, Column, Integer, BigInteger, String, Boolean, DateTime
from datetime import datetime

class Database:
	def __init__(self):
		self.engine = create_engine("sqlite:///data.db", echo=True)
		self.conn = self.engine.connect()

	def create(self):
		meta = MetaData()

		self.guild = Table(
			'guilds', meta,
			Column('guild_id', BigInteger, primary_key=True),
			Column('nickname', String,     default=None    ),
			Column('cooldown', Integer,    default=None    ),
			Column('readonly', Boolean,    default=False   ),
			Column('messages', Integer,    default=0       ),
		)

		self.users = Table(
			'users', meta,
			Column('user_id',  BigInteger, primary_key=True),
			Column('nickname', String,     default=None    ),
			Column('mod',      Boolean,    default=False   ),
			Column('cooldown', Integer,    default=None    ),
			Column('readonly', Boolean,    default=False   ),
			Column('banned',   Boolean,    default=False   ),
		)

		self.log = Table(
			'log', meta,
			Column('timestamp', DateTime, primary_key=True, default=datetime.now),
			Column('author',    BigInteger),
			Column('table',     String    ),
			Column('key',       String    ),
			Column('old',       String    ),
			Column('new',       String    ),
		)

		meta.create_all(self.engine)

	##
	## GUILD
	##

	def addGuild(self, guild_id: int):
		s = self.guilds.insert().values(guild_id=guild_id)
		self.conn.execute(s)

	def getGuild(self, guild_id: int):
		s = self.guilds.select().where(guilds.c.guild_id == guild_id)
		return self.conn.execute(s)

	def setGuild(self, guild_id: int, nickname: str = None, cooldown: int = None, readonly: bool = None):
		g = self.getGuild(guild_id)
		g_nickname = nickname if nickname else g.nickname
		g_cooldown = cooldown if cooldown else g.cooldown
		g_readonly = readonly if readonly else g.readonly
		s = self.guilds.update().where(guilds.c.guild_id == guild_id).values(
			nickname = g_nickname,
			cooldown = g_cooldown,
			readonly = g_readonly,
		)
		self.conn.execute(s)

	##
	## USER
	##

	def addUser(self, user_id: int):
		s = self.users.insert().values(user_id=user_id)
		self.conn.execute(s)

	def getUser(self, user_id: int):
		s = self.users.select().where(users.c.user_id == user_id)
		return self.conn.execute(s)

	def setUser(self, user_id: int, nickname: str = None, mod: bool = None, cooldown: int = None, readonly: bool = None, banned: bool = None):
		u = self.getUser(user_id)
		u_nickname = nickname if nickname else u.nickname
		u_mod      = mod      if mod      else u.mod
		u_cooldown = cooldown if cooldown else u.cooldown
		u_readonly = readonly if readonly else u.readonly
		u_banned   = banned   if banned   else u.banned
		s = self.users.update().where(users.c.user_id == user_id).values(
			nickname = nickname,
			mod      = mod,
			cooldown = cooldown,
			readonly = readonly,
			banned   = banned,
		)
		self.conn.execute(s)

	def getUser(self, user_id: int):
		s = self.users.select().where(users.c.user_id == user_id)
		return self.conn.execute(s)

	##
	## LOG
	##
	def log(self, author: int, table: str, key: str, old, new):
		s = self.users.insert().values(
			author = author,
			table  = table,
			key    = key,
			old    = old,
			new    = new,
		)
		self.conn.execute(s)

	def getLogs(self, author: int = None, table: str = None, key: str = None, old: str = None, new: str = None, before: datetime = None, after: datetime = None):
		#TODO
		return
