import json
import logging
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from core import wormcog, output
from core.database import repo_u

config = json.load(open("config.json"))
bot = commands.Bot(command_prefix=config["prefix"], help_command=None)

##
## EVENTS
##


started = False


@bot.event
async def on_ready():
    global started
    if started:
        return

    started = True

    m = "INFO: Ready at " + datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    print(m)

    # do not spam logging channel while testing
    level = getattr(logging, config["log level"])
    if level >= logging.INFO:
        ch = output.getLogChannel(bot)
        await ch.send(f"```{m}```")

    await wormcog.presence(bot)


@bot.event
async def on_error(event, *args, **kwargs):
    if config["suppress errors"]:
        return

    tb = traceback.format_exc()
    print(tb)


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
