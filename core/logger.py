import logging


class WormholeLogger(logging.StreamHandler):
    def __init__(self):
        super().__init__(self)
        fmt = "%(asctime)s %(levelname)-7s %(filename)s, %(funcName)s(): %(message)s"
        fmt_date = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)
