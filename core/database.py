from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Database:
    def __init__(self):
        self.base = declarative_base()
        self.db = create_engine("sqlite:///data.db")


database = Database()
session = sessionmaker(database.db)()


class Beam(database.base):
    __tablename__ = "beams"

    # fmt: off
    name       = Column(String,  primary_key = True  )
    active     = Column(Boolean, default     = True  )
    replace    = Column(Boolean, default     = True  )
    anonymity  = Column(String,  default     = "none")
    timeout    = Column(Integer, default     = 60    )
    file_limit = Column(Integer, default     = -1    )
    # fmt: on


class BeamRepository:
    def add(self, name: str):
        session.add(Beam(name=name))
        session.commit()

    def get(self, name: str):
        return session.query(Beam).filter(Beam.name == name).one_or_none()

    def getAll(self):
        return session.query(Beam).all()

    def set(
        # fmt: off
        self,
        name:       str,
        active:     bool = None,
        replace:    bool = None,
        anonymity:  str  = None,
        timeout:    int  = None,
        file_limit: int  = None,
        # fmt: on
    ):
        # fmt: off
        b = self.get(name)
        b_active     = active     if active     else b.active
        b_replace    = replace    if replace    else b.replace
        b_anonymity  = anonymity  if anonymity  else b.anonymity
        b_timeout    = timeout    if timeout    else b.timeout
        b_file_limit = file_limit if file_limit else b.file_limit
        # fmt: on
        session.query(Beam).filter(Beam.name == name).update(
            {
                Beam.active: s_active,
                Beam.replace: s_replace,
                Beam.anonymity: s_anonymity,
                Beam.timeout: s_timeout,
                Beam.file_limit: s_file_limit,
            }
        )
        session.commit()

    def remove(self, name: str):
        session.query(Beam).filter(Beam.name == name).delete()


class Wormhole(database.base):
    __tablename__ = "wormholes"

    # fmt: off
    channel  = Column(BigInteger, primary_key = True)
    beam     = Column(String,     ForeignKey("beams.name", ondelete="CASCADE"))
    active   = Column(Boolean,    default = True )
    readonly = Column(Boolean,    default = False)
    logo     = Column(String,     default = None )
    messages = Column(Integer,    default = 0    )
    # fmt: on


class WormholeRepository:
    def add(self, beam: str, channel: int):
        session.add(Wormhole(channel=channel, beam=beam))
        session.commit()

    def get(self, channel: int):
        return session.query(Wormhole).filter(Wormhole.channel == channel).one_or_none()

    def getByBeam(self, beam: str):
        return session.query(Wormhole).filter(Wormhole.beam == beam).all()

    def getByActive(self):
        return session.query(Wormhole).filter(Wormhole.active == True).all()

    def getAll(self):
        return session.query(Wormhole).all()

    def set(
        # fmt: off
        self,
        channel:  int,
        active:   bool = None,
        logo:     str  = None,
        readonly: bool = None,
        messages: int  = None,
        # fmt: on
    ):
        # fmt: off
        g = self.get(channel)
        g_logo     = logo     if logo     else g.logo
        g_readonly = readonly if readonly else g.readonly
        g_messages = messages if messages else g.messages
        # fmt: on
        session.query(Wormhole).filter(Wormhole.channel == channel).update(
            {Wormhole.logo: g_logo, Wormhole.readonly: g_readonly, Wormhole.messages: g_messages,}
        )
        session.commit()

    def remove(self, channel: int):
        session.query(Wormhole).filter(Wormhole.channel == channel).delete()


class User(database.base):
    __tablename__ = "users"

    # fmt: off
    id         = Column(BigInteger, primary_key=True)
    nickname   = Column(String,     default=None )
    mod        = Column(Boolean,    default=False)
    restricted = Column(BigInteger, default=None )
    readonly   = Column(Boolean,    default=False)
    banned     = Column(Boolean,    default=False)
    # fmt: on


class UserRepository:
    def add(self, id: int):
        session.add(User(id=id))
        session.commit()

    def get(self, id: int):
        return session.query(User).filter(User.id == id).one_or_none()

    def getMods(self):
        return session.query(User).filter(User.mod == True).all()

    def getAll(self):
        return session.query(User).all()

    def set(
        # fmt: off
        self,
        id:         int,
        nickname:   str  = None,
        mod:        bool = None,
        restricted: int  = None,
        readonly:   bool = None,
        # fmt: on
    ):
        # fmt: off
        u = self.get(id)
        u_nickname   = nickname   if nickname   else u.nickname
        u_mod        = mod        if mod        else u.mod
        u_restricted = restricted if restricted else u.restricted
        u_readonly   = readonly   if readonly   else u.readonly
        # fmt: on
        session.query(User).filter(User.id == id).update(
            {User.nickname: g_nickname, User.mod: g_mod, User.readonly: g_readonly,}
        )
        session.commit()

    def delete(self, id: int):
        session.query(User).filter(User.id == id).delete()


class Log(database.base):
    __tablename__ = "log"

    # fmt: off
    id        = Column(Integer,  primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    author    = Column(BigInteger)
    table     = Column(String    )
    key       = Column(String    )
    old       = Column(String    )
    new       = Column(String    )
    # fmt: on


class LogRepository:
    def log(self, author: int, table: str, key: str, old: str, new: str):
        session.add(Log(author=author, table=table, key=key, old=old, new=new))

    def get(
        # fmt: off
        self,
        author: int = None,
        table:  str = None,
        key:    str = None,
        old:    str = None,
        new:    str = None,
        before: datetime = None,
        after:  datetime = None,
        # fmt: on
    ):
        # TODO
        return


database.base.metadata.create_all(database.db)
session.commit()

repo_b = BeamRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
repo_l = LogRepository()
