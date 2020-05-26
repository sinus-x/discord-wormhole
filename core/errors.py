import json

config = json.load(open("config.json"))


class WormholeException(Exception):
    def __init__(self, message):
        self.message = message


class DatabaseException(WormholeException):
    def __init__(self, message, table, key=None, value=None):
        super().__init__(message)
        self.table = table
        self.key = key
        self.value = value

    def __str__(self):
        if self.key and self.value:
            return f"{self.message} (table `{self.table}` > `{self.key} = {self.value}`)"
        if self.key:
            return f"{self.message} (table `{self.table}` > `{self.key}`)"
        return f"{self.message} (table `{self.table}`)"


class NotRegistered(WormholeException):
    def __init__(self):
        super().__init__("Not registered")

    def __str__(self):
        return f"You have to register first with `{config['prefix']}register`"
