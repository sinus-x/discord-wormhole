import json

import discord
from discord.ext import commands

from core.database import repo_u, repo_w

config = json.load(open("config.json"))


def is_admin(ctx: commands.Context):
    return ctx.author.id == config["admin id"]


def is_mod(ctx: commands.Context):
    return is_admin(ctx) or repo_u.get_attribute(ctx.author.id, "mod") == 1


def in_wormhole(ctx: commands.Context):
    return is_admin(ctx) or (hasattr(ctx.channel, "id") and repo_w.exists(ctx.channel.id))


def in_wormhole_or_dm(ctx: commands.Context):
    return is_admin(ctx) or in_wormhole(ctx) or isinstance(ctx.channel, discord.DMChannel)


def not_in_wormhole(ctx: commands.Context):
    return is_admin(ctx) or not in_wormhole(ctx)
