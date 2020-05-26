from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.errors import DatabaseException


class Database:
    def __init__(self):
        self.base = declarative_base()
        self.db = create_engine("sqlite:///wormhole.db")


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
        try:
            session.add(Beam(name=name))
            session.commit()
        except:
            session.rollback()
            raise DatabaseException(f'Beam "{name}" already exists', table="beams")

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
        b_active     = active     if active     is not None else b.active
        b_replace    = replace    if replace    is not None else b.replace
        b_anonymity  = anonymity  if anonymity  is not None else b.anonymity
        b_timeout    = timeout    if timeout    is not None else b.timeout
        b_file_limit = file_limit if file_limit is not None else b.file_limit
        # fmt: on
        try:
            session.query(Beam).filter(Beam.name == name).update(
                {
                    Beam.active: b_active,
                    Beam.replace: b_replace,
                    Beam.anonymity: b_anonymity,
                    Beam.timeout: b_timeout,
                    Beam.file_limit: b_file_limit,
                }
            )
            session.commit()
        except:
            session.rollback()
            raise DatabaseException(f'Update of beam "{name}" failed', table="beams")

    def remove(self, name: str):
        try:
            session.query(Beam).filter(Beam.name == name).delete()
        except:
            session.rollback()
            raise DatabaseException(f"Beam {name} not found", table="beams")


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
        try:
            session.add(Wormhole(channel=channel, beam=beam))
            session.commit()
        except Exception as e:
            session.rollback()
            print(e)
            raise DatabaseException(f"Channel {channel} is already a wormhole", table="wormholes")

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
        ch = self.get(channel)
        if ch == None:
            raise DatabaseException("Wormhole {channel} not found", table="wormholes")

        ch_logo     = logo     if logo     is not None else ch.logo
        ch_readonly = readonly if readonly is not None else ch.readonly
        ch_messages = messages if messages is not None else ch.messages
        # fmt: on
        try:
            session.query(Wormhole).filter(Wormhole.channel == channel).update(
                {
                    Wormhole.logo: ch_logo,
                    Wormhole.readonly: ch_readonly,
                    Wormhole.messages: ch_messages,
                }
            )
            session.commit()
        except:
            session.rollback()
            raise DatabaseException(f"Update for wormhole {channel} failed", table="wormholes")

    def remove(self, channel: int):
        try:
            session.query(Wormhole).filter(Wormhole.channel == channel).delete()
        except:
            session.rollback()
            raise DatabaseException(f"Wormhole {channel} found", table="wormholes")


class User(database.base):
    __tablename__ = "users"

    # fmt: off
    id         = Column(BigInteger, primary_key=True)
    nickname   = Column(String,     default=None )
    mod        = Column(Boolean,    default=False)
    home       = Column(BigInteger, default=None )
    readonly   = Column(Boolean,    default=False)
    banned     = Column(Boolean,    default=False)
    # fmt: on


class UserRepository:
    def add(self, id: int):
        try:
            session.add(User(id=id))
            session.commit()
        except:
            session.rollback()
            raise DatabaseException(f"User {id} already exists", table="users")

    def get(self, id: int):
        return session.query(User).filter(User.id == id).one_or_none()

    def getMods(self):
        return session.query(User).filter(User.mod == True).all()

    def getAll(self):
        return session.query(User).all()

    def set(
        # fmt: off
        self,
        id:       int,
        nickname: str  = None,
        mod:      bool = None,
        home:     int  = None,
        readonly: bool = None,
        # fmt: on
    ):
        # fmt: off
        u = self.get(id)
        u_nickname = nickname if nickname is not None else u.nickname
        u_mod      = mod      if mod      is not None else u.mod
        u_home     = home     if home     is not None else u.home
        u_readonly = readonly if readonly is not None else u.readonly
        # fmt: on
        try:
            session.query(User).filter(User.id == id).update(
                {
                    User.nickname: u_nickname,
                    User.mod: u_mod,
                    User.home: u_home,
                    User.readonly: u_readonly,
                }
            )
            session.commit()
        except:
            session.rollback()
            raise DatabaseException(f"User {id} could not be updated", table="users")

    def delete(self, id: int):
        try:
            session.query(User).filter(User.id == id).delete()
        except:
            session.rollback()
            raise DatabaseException(f"Use {id} found", table="users")


database.base.metadata.create_all(database.db)
session.commit()

repo_b = BeamRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
