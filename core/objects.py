class Beam:
    name = None
    active = 0
    anonymity = "none"
    replace = 1
    timeout = 60

    def __init__(self, name: str = None):
        self.name = name

    def __repr__(self):
        return (
            f"Beam {self.name}: "
            f"active {self.active}, anonymity {self.anonymity}, "
            f"replace {self.replace}, timeout {self.timeout}"
        )


class Wormhole:
    discord_id = None
    beam = None
    admin_id = 0
    active = 1
    logo = ""
    messages = 0
    readonly = 0
    invite = ""

    def __init__(self, discord_id: int = None):
        self.discord_id = discord_id

    def __repr__(self):
        return (
            f"Wormhole {self.discord_id}: "
            f"beam {self.beam}, admin {self.admin_id}, "
            f"active {self.active}, readonly {self.readonly}, "
            f"logo '{self.logo}', invite: {self.invite}"
        )


class User:
    discord_id = None
    mod = 0
    nickname = ""
    readonly = 0
    restricted = 0

    def __init__(self, discord_id: int = None):
        self.discord_id = discord_id

    def __repr__(self):
        return (
            f"User {self.discord_id}: nickname {self.nickname}, "
            f"mod {self.mod}, readonly {self.readonly}, restricted {self.restricted}"
        )
