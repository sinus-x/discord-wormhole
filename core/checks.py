import json

from discord.ext import commands
from core.database import repo_u, repo_w

config = json.load(open("config.json"))


def is_admin(ctx: commands.Context):
    return ctx.author.id == config["admin id"] or commands.is_owner(ctx)


def is_mod(ctx: commands.Context):
    return repo_u.getAttribute(ctx.author.id, "mod") == 1


def in_wormhole(ctx: commands.Context):
    return hasattr(ctx.channel, "id") and repo_w.exists(ctx.channel.id)
