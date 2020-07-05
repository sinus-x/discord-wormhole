import redis

from core import objects
from core.errors import DatabaseException


db = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


class BeamRepository:
    def __init__(self):
        self.attributes = ("active", "admin_id", "anonymity", "replace", "timeout")

    ##
    ## Interface
    ##

    def add(self, *, name: str, admin_id: int):
        self._name_check(name)
        self._availability_check(name)

        db.mset(
            {
                f"beam:{name}:active": 0,
                f"beam:{name}:admin_id": admin_id,
                f"beam:{name}:anonymity": "none",
                f"beam:{name}:replace": 1,
                f"beam:{name}:timeout": 60,
            }
        )

    def get(self, name: str) -> objects.Beam:
        self._existence_check(name)

        result = objects.Beam(name)
        result.active = self.getAttribute(name, "active")
        result.admin_id = self.getAttribute(name, "admin_id")
        result.anonymity = self.getAttribute(name, "anonymity")
        result.replace = self.getAttribute(name, "replace")
        result.timeout = self.getAttribute(name, "timeout")

        return result

    def getAttribute(self, name: str, attribute: str):
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid beam attribute: {attribute}.")
        return db.get(f"beam:{name}:{attribute}")

    def listNames(self):
        try:
            result = db.scan(match="beam:*:active")[1]
            return [x.split(":")[1] for x in result]
        except redis.exceptions.ResponseError as e:
            return []

    def listObjects(self):
        names = self.listNames()
        return [self.get(x) for x in names]

    def set(self, name: str, **kwargs):
        self._existence_check(name)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid beam attribute: {key} = {value}.")

        for key, value in kwargs.items():
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

    def isValidAttribute(self, key: str, value):
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

    def _getBeamName(self, string: str):
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

    def add(self, *, beam: str, discord_id: int):
        self._availability_check(discord_id)

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

    def get(self, discord_id: int) -> objects.Wormhole:
        self._existence_check(discord_id)

        result = objects.Wormhole(discord_id)
        result.active = self.getAttribute(discord_id, "active")
        result.admin_id = self.getAttribute(discord_id, "admin_id")
        result.beam = self.getAttribute(discord_id, "beam")
        result.logo = self.getAttribute(discord_id, "logo")
        result.messages = self.getAttribute(discord_id, "messages")
        result.readonly = self.getAttribute(discord_id, "readonly")

        return result

    def getAttribute(self, discord_id: int, attribute: str):
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid wormhole attribute: {attribute}.")
        return db.get(f"wormhole:{discord_id}:{attribute}")

    def listIDs(self):
        return [int(x.split(":")[1]) for x in db.scan(match="wormhole:*:active")[1]]

    def listObjects(self):
        return [self.get(x) for x in self.listIDs()]

    def set(self, discord_id: int, **kwargs):
        self._existence_check(discord_id)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid wormhole attribute: {key} = {value}.")

        for key, value in kwargs.items():
            db.set(f"wormhole:{discord_id}:{key}", value)

    def delete(self, discord_id: int):
        self._existence_check(discord_id)
        for attribute in self.attributes:
            db.delete(f"wormhole:{discord_id}:{attribute}")

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value):
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

    def _getWormholeDiscordId(self, string: str):
        return int(string.split(":")[1])

    def _availability_check(self, discord_id: int):
        result = db.get(f"wormhole:{discord_id}:active")
        if result is not None:
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

    def add(self, *, discord_id: int, nickname: str, home_id: int = None):
        self._availability_check(discord_id)

        db.mset(
            {
                f"user:{discord_id}:home_id": home_id,
                f"user:{discord_id}:mod": 0,
                f"user:{discord_id}:nickname": nickname,
                f"user:{discord_id}:readonly": 0,
                f"user:{discord_id}:restricted": 0,
            }
        )

    def get(self, discord_id: int) -> objects.User:
        self._existence_check(discord_id)

        result = objects.User(discord_id)
        result.home_id = self.getAttribute(discord_id, "home_id")
        result.mod = self.getAttribute(discord_id, "mod")
        result.nickname = self.getAttribute(discord_id, "nickname")
        result.readonly = self.getAttribute(discord_id, "readonly")
        result.restricted = self.getAttribute(discord_id, "restricted")

        return result

    def getByNickname(self, nickname: str) -> objects.User:
        result = db.scan(match="user:*:nickname")
        for key, value in result:
            if value == nickname:
                return self.get(self._getUserDiscordId(key))
        return None

    def getAttribute(self, discord_id: int, attribute: str):
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid user attribute: {attribute}.")
        return db.get(f"user:{discord_id}:{attribute}")

    def listIDs(self):
        return [int(x.split(":")[1]) for x in db.scan(match="user:*:readonly")[1]]

    def listObjects(self):
        return [self.get(x) for x in self.listIDs()]

    def set(self, discord_id: int, **kwargs):
        self._existence_check(discord_id)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid user attribute: {key} = {value}.")

        for key, value in kwargs.items():
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

    def isValidAttribute(self, key: str, value):
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

    def _getUserDiscordId(self, string: str):
        return int(string.split(":")[1])


repo_b = BeamRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
