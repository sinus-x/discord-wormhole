class Beam:
    active = False
    anonymity = "none"
    name = None
    replace = True
    timeout = 60

    def __init__(self, name: str = None):
        self.name = name


class Wormhole:
    active = True
    beam = None
    discord_id = None
    logo = None
    messages = 0
    readonly = False

    def __init__(self, discord_id: int = None):
        self.discord_id = discord_id


class User:
    discord_id = None
    home = None
    mod = False
    nickname = None
    readonly = False

    def __init__(self, discord_id: int = None):
        self.discord_id = discord_id
