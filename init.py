import json
import logging
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from core import wormcog, logger
from core.database import repo_u

config = json.load(open("config.json"))
bot = commands.Bot(command_prefix=config["prefix"], help_command=None)

log = logging.getLogger("root")
log.setLevel(config["log level"])
log.addHandler(logger.WormholeLogger())

##
## EVENTS
##


@bot.event
async def on_ready():
    print("Ready at " + datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
    await wormcog.presence(bot)


@bot.event
async def on_error(event, *args, **kwargs):
    if config["suppress errors"]:
        return

    output = traceback.format_exc()
    print(output)


##
## COMMANDS
##


@bot.command()
async def reload(ctx: commands.Context, cog: str):
    """Reload the wormhole"""
    if ctx.author.id != config["admin id"]:
        await ctx.send("You do not have permission to do this!")
        return
    try:
        bot.reload_extension(f"cogs.{cog}")
        m = f"**{cog.upper()}** reloaded."
        print(m)
        await ctx.send(m)
    except Exception as e:
        await ctx.send(f"An error occured: ```\n{e}```")


##
## INIT
##

for c in ["errors", "wormhole", "admin"]:
    bot.load_extension(f"cogs.{c}")
    print(f"{c.upper()} loaded")

bot.run(config.get("bot key"))
