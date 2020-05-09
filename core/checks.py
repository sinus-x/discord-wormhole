import json

from discord.ext import commands
from core.database import repo_u

config = json.load(open("config.json"))


def is_admin(ctx: commands.Context):
    return ctx.author.id == config["admin id"]


def is_mod(ctx: commands.Context):
    return is_admin(ctx) or ctx.author.id in [u.id for u in repo_u.getMods()]


def in_wormhole(ctx: commands.Context):
    return ctx.author.id == config["admin id"] or ctx.channel.id in config["wormholes"]
