import redis

from core import objects
from core.errors import DatabaseException


class Database:
    def __init__(self):
        self.db = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


class BeamRepository(Database):
    def __init__(self):
        super().__init__()
        self.attributes = ("active", "admin_id", "anonymity", "replace", "timeout")

    ##
    ## Interface
    ##

    def add(self, *, name: str, admin_id: int):
        self._name_check(name)

        self.set(
            name=name, admin_id=admin_id, active=0, replace=1, anonymity="none", timeout=60,
        )

    def get(self, name: str) -> objects.Beam:
        self._availability_check(name)

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
        return self.db.get(f"beam:{name}:{attribute}")

    def getNames(self):
        result = self.db.scan("beam:*:active").keys()
        return [self._getBeamName(x) for x in result]

    def set(self, name: str, **kwargs):
        self._existence_check(name)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid beam attribute: {key} = {value}.")

        for key, value in kwargs.items():
            self.db.set(f"beam:{name}:{key}", value)

    def delete(self, name: str):
        self._existence_check(name)
        for attribute in self.attributes:
            self.db.delete(f"beam:{name}:{attribute}")

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value):
        # fmt: off
        if key not in self.attributes \
        or key in ("active", "replace")    and value not in (0, 1) \
        or key in ("anonymity")            and value not in ("none", "guild", "full") \
        or key in ("admin_id", "timeout")  and type(value) != int \
        or key in ("name") and type(value) != str:
            return False
        return True
        # fmt:on

    ##
    ## Helpers
    ##

    def _getBeamName(self, string: str):
        return string.split(":")[1]

    def _availability_check(self, name: str):
        result = self.db.get(f"beam:{name}:active")
        if result is not None:
            raise DatabaseException("Beam name already exists.")

    def _existence_check(self, name: str):
        result = self.db.get(f"beam:{name}:active")
        if result is None:
            raise DatabaseException("Beam name not found.")

    def _name_check(self, name: str):
        if ":" in name:
            raise DatabaseException("Beam name cannot contain semicolon.")


class WormholeRepository(Database):
    def __init__(self):
        super().__init__()
        self.attributes = ("active", "admin_id", "beam", "logo", "messages", "readonly")

    ##
    ## Interface
    ##

    def add(self, *, beam: str, discord_id: int):
        self._availability_check(discord_id)
        self.set(
            beam=beam,
            discord_id=discord_id,
            active=1,
            admin_id=None,
            logo=None,
            messages=0,
            readonly=0,
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
        return self.db.get(f"wormhole:{discord_id}:{attribute}")

    def getAllIDs(self):
        result = self.db.scan("wormhole:*:active").keys()
        return [self._getWormholeDiscordId(x) for x in result]

    def set(self, discord_id: int, **kwargs):
        self._existence_check(discord_id)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid wormhole attribute: {key} = {value}.")

        for key, value in kwargs.items():
            self.db.set(f"wormhole:{discord_id}:{key}", value)

    def delete(self, discord_id: int):
        self._existence_check(discord_id)
        for attribute in self.attributes:
            self.db.delete(f"wormhole:{discord_id}:{attribute}")

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
        result = self.db.get(f"wormhole:{discord_id}:active")
        if result is not None:
            raise DatabaseException(f"Channel is already a wormhole: {discord_id}.")

    def _existence_check(self, discord_id: int):
        result = self.db.get(f"wormhole:{discord_id}:active")
        if result is None:
            raise DatabaseException(f"Channel is not a wormhole: {discord_id}.")


class UserRepository(Database):
    def __init__(self):
        super().__init__()
        self.attributes = ("discord_id", "home_id", "mod", "nickname", "readonly")

    ##
    ## Interface
    ##

    def add(self, *, discord_id: int, nickname: str, home_id: int = None):
        self._availability_check(discord_id)

        self.set(
            discord_id=discord_id, nickname=nickname, home_id=home_id, mod=0, readonly=0,
        )

    def get(self, discord_id: int) -> objects.User:
        self._existence_check(discord_id)

        result = objects.User(discord_id)
        result.home_id = self.getAttribute(discord_id, "home_id")
        result.mod = self.getAttribute(discord_id, "mod")
        result.nickname = self.getAttribute(discord_id, "nickname")
        result.readonly = self.getAttribute(discord_id, "readonly")

        return result

    def getAttribute(self, discord_id: int, attribute: str):
        if attribute not in self.attributes:
            raise DatabaseException(f"Invalid user attribute: {attribute}.")
        return self.db.get(f"user:{discord_id}:{attribute}")

    def getAllIDs(self):
        result = self.db.scan("user:*:readonly").keys()
        return [self._getUserDiscordId(x) for x in result]

    def set(self, discord_id: int, **kwargs):
        self._existence_check(discord_id)

        for key, value in kwargs.items():
            if not self.isValidAttribute(key, value):
                raise DatabaseException(f"Invalid user attribute: {key} = {value}.")

        for key, value in kwargs.items():
            self.db.set(f"user:{discord_id}:{key}", value)

    def delete(self, discord_id: int):
        self._existence_check(discord_id)
        for attribute in self.attributes:
            self.db.delete(f"user:{discord_id}:{attribute}")

    ##
    ## Logic
    ##

    def isValidAttribute(self, key: str, value):
        # fmt: off
        if key not in self.attributes \
        or key in ("mod", "readonly") and value not in (0, 1) \
        or key in ("home_id") and type(value) != int \
        or key in ("nickname") and type(value) != str:
            return False
        return True
        # fmt: on

    ##
    ## Helpers
    ##

    def _availability_check(self, discord_id: int):
        result = self.db.get(f"user:{discord_id}:readonly")
        if result is not None:
            raise DatabaseException(f"User ID already known: {discord_id}.")

    def _existence_check(self, discord_id: int):
        result = self.db.get(f"user:{discord_id}:readonly")
        if result is None:
            raise DatabaseException(f"User ID unknown: {discord_id}.")


repo_b = BeamRepository()
repo_w = WormholeRepository()
repo_u = UserRepository()
