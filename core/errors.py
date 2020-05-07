class WormholeException(Exception):
    def __init__(self, message):
        self.message = message


class DatabaseException(WormholeException):
    def __init__(self, message, table):
        super().__init__(message)
        self.table = table

    def __str__(self):
        return f"{self.message} (`{self.table}`)"


class DatabaseAddException(DatabaseException):
    def __init__(self, message, table: str, item=None):
        super().__init__(message, table)
        self.item = item

    def __str__(self):
        if self.item:
            return f"{self.message} (`{self.table}` > `{self.item}`)"
        return super().__str__()


class DatabaseUpdateException(DatabaseException):
    def __init__(self, message, table: str, key=None, value=None):
        super().__init__(message, table)
        self.key = key
        self.value = value

    def __str__(self):
        if self.key and self.value:
            return f"{self.message} (`{self.table}` > `{self.key} = {self.value}`)"
        return super().__str__()
