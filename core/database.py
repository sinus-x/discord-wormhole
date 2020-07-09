import redis
from typing import Union, Optional, List, Dict

from core import objects
from core.errors import DatabaseException

db = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


class BeamRepository:
    def __init__(self):
        self.attributes = ("active", "admin_id", "anonymity", "replace", "timeout")

    ##
    ## Interface
    ##

    def exists(self, name: str) -> bool:
        return db.exists(f"beam:{name}:active")

    def add(self, *, name: str, admin_id: int):
        self._name_check(name)
        self._availability_check(name)

        db.mset(
            {
                f"beam:{name}:active": 1,
                f"beam:{name}:admin_id": admin_id,
                f"beam:{name}:anonymity": "none",
                f"beam:{name}:replace": 1,
                f"beam:{name}:timeout": 60,
            }
        )

    def get(self, name: str) -> Optional[objects.Beam]:
        if not self.exists(name):
            return None

        result = objects.Beam(name)
        result.active = self.getAttribute(name, "active")
        result.admin_id = self.getAttribute(name, "admin_id")
        result.anonymity = self.getAttribute(name, "anonymity")
        result.replace = self.getAttribute(name, "replace")
        result.timeout = self.getAttribute(name, "timeout")

        return result

    def getAttribute(self, name: str, attribute: str) -> Union[str, int]:
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid beam attribute: {attribute}.")
        result = db.get(f"beam:{name}:{attribute}")
        if attribute in ("active", "admin_id", "replace", "timeout") and result:
            result = int(result)
        return result

    def listNames(self) -> List[str]:
        result = []
        for r in db.scan_iter(match="beam:*:active"):
            result.append(r)
        return [x.split(":")[1] for x in result]

    def listObjects(self) -> List[objects.Beam]:
        names = self.listNames()
        return [self.get(x) for x in names]

    def set(self, name: str, key: str, value):
        self._existence_check(name)

        if not self.isValidAttribute(key, value):
            raise DatabaseException(f"Invalid beam attribute: {key} = {value}.")

        db.set(f"beam:{name}:{key}", value)

    def delete(self, name: str):
        self._existence_check(name)

        wormholes = [db.get(x) for x in db.scan(match="wormhole:*:beam")[1]]
        if name in wormholes:
            raise DatabaseException(f"Found {len(wormholes)} linked wormholes, halting.")

        for attribute in self.attributes:
            db.delete(f"beam:{name}:{attribute}")

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value) -> bool:
        # fmt: off
        if key not in self.attributes \
        or key in ("active", "replace")   and value not in (0, 1) \
        or key in ("anonymity")           and value not in ("none", "guild", "full") \
        or key in ("admin_id", "timeout") and type(value) != int \
        or key in ("name")                and type(value) != str:
            return False
        return True
        # fmt:on

    ##
    ## Helpers
    ##

    def _getBeamName(self, string: str) -> str:
        return string.split(":")[1]

    def _name_check(self, name: str):
        if ":" in name:
            raise DatabaseException(f"Beam name `{name}` contains semicolon.")

    def _availability_check(self, name: str):
        result = db.get(f"beam:{name}:active")
        if result is not None:
            raise DatabaseException(f"Beam name `{name}` already exists.")

    def _existence_check(self, name: str):
        result = db.get(f"beam:{name}:active")
        if result is None:
            raise DatabaseException(f"Beam name `{name}` not found.")


class WormholeRepository:
    def __init__(self):
        self.attributes = ("beam", "admin_id", "active", "logo", "readonly", "messages")

    ##
    ## Interface
    ##

    def exists(self, discord_id: int) -> bool:
        return db.exists(f"wormhole:{discord_id}:active")

    def add(self, *, beam: str, discord_id: int):
        self._availability_check(beam, discord_id)

        db.mset(
            {
                f"wormhole:{discord_id}:beam": beam,
                f"wormhole:{discord_id}:admin_id": 0,
                f"wormhole:{discord_id}:active": 1,
                f"wormhole:{discord_id}:logo": "",
                f"wormhole:{discord_id}:readonly": 0,
                f"wormhole:{discord_id}:messages": 0,
            }
        )

    def get(self, discord_id: int) -> Optional[objects.Wormhole]:
        if not self.exists(discord_id):
            return None

        result = objects.Wormhole(discord_id)
        result.active = self.getAttribute(discord_id, "active")
        result.admin_id = self.getAttribute(discord_id, "admin_id")
        result.beam = self.getAttribute(discord_id, "beam")
        result.logo = self.getAttribute(discord_id, "logo")
        result.messages = self.getAttribute(discord_id, "messages")
        result.readonly = self.getAttribute(discord_id, "readonly")

        return result

    def getAttribute(self, discord_id: int, attribute: str) -> Union[str, int]:
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid wormhole attribute: {attribute}.")
        result = db.get(f"wormhole:{discord_id}:{attribute}")

        # get data types
        if attribute in ("active", "admin_id", "messages", "readonly") and result:
            result = int(result)

        return result

    def listIDs(self, beam: str = None) -> List[int]:
        result = []
        for r in db.scan_iter(match="wormhole:*:active"):
            result.append(r)

        result = [int(x.split(":")[1]) for x in result]
        if beam is None:
            return result
        return [w for w in result if self.getAttribute(w, "beam") == beam]

    def listObjects(self, beam: str = None) -> List[objects.Wormhole]:
        return [self.get(x) for x in self.listIDs(beam)]

    def set(self, discord_id: int, key: str, value):
        self._existence_check(discord_id)

        if not self.isValidAttribute(key, value):
            raise DatabaseException(f"Invalid wormhole attribute: {key} = {value}.")

        db.set(f"wormhole:{discord_id}:{key}", value)

    def delete(self, discord_id: int):
        self._existence_check(discord_id)
        for attribute in self.attributes:
            db.delete(f"wormhole:{discord_id}:{attribute}")

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value) -> bool:
        # fmt: off
        if key not in self.attributes \
        or key in ("active", "readonly")   and value not in (0, 1) \
        or key in ("admin_id", "messages") and type(value) != int \
        or key in ("beam", "logo")         and type(value) != str:
            return False
        return True
        # fmt: on

    ##
    ## Helpers
    ##

    def _getWormholeDiscordId(self, string: str) -> int:
        return int(string.split(":")[1])

    def _availability_check(self, beam: str, discord_id: int):
        if not db.exists(f"beam:{beam}:active"):
            raise DatabaseException(f"Beam {beam} does not exist.")
        if db.exists(f"wormhole:{discord_id}:active"):
            raise DatabaseException(f"Channel `{discord_id}` is already a wormhole.")

    def _existence_check(self, discord_id: int):
        result = db.get(f"wormhole:{discord_id}:active")
        if result is None:
            raise DatabaseException(f"Channel `{discord_id}` is not a wormhole.")


class UserRepository:
    def __init__(self):
        self.attributes = ("discord_id", "home_id", "mod", "nickname", "readonly", "restricted")

    ##
    ## Interface
    ##

    def exists(self, discord_id: int) -> bool:
        return db.exists(f"user:{discord_id}:readonly")

    def add(self, *, discord_id: int, nickname: str):
        self._availability_check(discord_id)

        db.mset(
            {
                f"user:{discord_id}:mod": 0,
                f"user:{discord_id}:nickname": nickname,
                f"user:{discord_id}:readonly": 0,
                f"user:{discord_id}:restricted": 0,
            }
        )

    def get(self, discord_id: int) -> Optional[objects.User]:
        if not self.exists(discord_id):
            return None

        result = objects.User(discord_id)
        result.home_ids = self.getHome(discord_id)
        result.mod = self.getAttribute(discord_id, "mod")
        result.nickname = self.getAttribute(discord_id, "nickname")
        result.readonly = self.getAttribute(discord_id, "readonly")
        result.restricted = self.getAttribute(discord_id, "restricted")

        return result

    def getByNickname(self, nickname: str) -> Optional[objects.User]:
        for r in db.scan_iter(match="user:*:nickname"):
            if db.get(r) == nickname:
                return self.get(int(r.split(":")[1]))
        return None

    def getAttribute(self, discord_id: int, attribute: str):
        attr = attribute if ":" not in attribute else attribute.split(":")[0]
        if attr not in self.attributes:
            raise DatabaseException(f"Invalid user attribute: {attribute}.")

        result = db.get(f"user:{discord_id}:{attribute}")
        if attr in ("home_id", "mod", "readonly", "restricted") and result:
            result = int(result)
        return result

    def getHome(self, discord_id: int, beam: str = None) -> Dict[str, int]:
        match = f"user:{discord_id}:home_id:" + ("*" if beam is None else beam)

        result = {}
        for r in db.scan_iter(match=match):
            result[r.split(":")[-1]] = int(db.get(r))
        return result

    def listIDs(self) -> List[int]:
        result = []
        for r in db.scan_iter(match="user:*:readonly"):
            result.append(r)
        return [int(x.split(":")[1]) for x in result]

    def listIDsByBeam(self, beam: str) -> List[int]:
        result = []
        for r in db.scan_iter(match=f"user:*:home_id:{beam}"):
            result.append(r)
        return [int(x.split(":")[1]) for x in result]

    def listIDsByWormhole(self, discord_id: int) -> List[int]:
        result = []
        users = []
        for r in db.scan_iter(match=f"user:*:home_id:*"):
            user = r.split(":")[1]
            if user not in users:
                users.append(user)
                result.append(r)
        return [int(x.split(":")[1]) for x in result if db.get(x) == str(discord_id)]

    def listObjects(self) -> List[objects.User]:
        return [self.get(x) for x in self.listIDs()]

    def listObjectsByBeam(self, beam: str) -> List[objects.User]:
        return [self.get(x) for x in self.listIDsByBeam(beam)]

    def listObjectsByWormhole(self, discord_id: int) -> List[objects.User]:
        return [self.get(x) for x in self.listIDsByWormhole(discord_id)]

    def set(self, discord_id: int, key: str, value):
        self._existence_check(discord_id)

        k = key if ":" not in key else key.split(":")[0]
        if not self.isValidAttribute(k, value):
            raise DatabaseException(f"Invalid user attribute: {key} = {value}.")
        if k == "home_id":
            beam = key.split(":")[1]
            if not db.exists(f"beam:{beam}:active"):
                raise DatabaseException(f"Beam not found: {beam}.")

        db.set(f"user:{discord_id}:{key}", value)

    def delete(self, discord_id: int):
        self._existence_check(discord_id)
        for attribute in self.attributes:
            db.delete(f"user:{discord_id}:{attribute}")

    def nicknameIsUsed(self, nickname: str) -> bool:
        return nickname in [db.get(x) for x in db.scan(match="user:*:nickname")[1]]

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value) -> bool:
        # fmt: off
        if key not in self.attributes \
        or key in ("mod", "readonly", "restricted") and value not in (0, 1) \
        or key in ("home_id") and type(value) != int \
        or key in ("nickname") and type(value) != str:
            return False
        return True
        # fmt: on

    ##
    ## Helpers
    ##

    def _availability_check(self, discord_id: int):
        result = db.get(f"user:{discord_id}:readonly")
        if result is not None:
            raise DatabaseException(f"User ID `{discord_id}` is already known.")

    def _existence_check(self, discord_id: int):
        result = db.get(f"user:{discord_id}:readonly")
        if result is None:
            raise DatabaseException(f"User ID `{discord_id}` unknown.")


repo_b = BeamRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
