import json
import traceback
from datetime import datetime

from discord.ext import commands

from core import wormcog, output

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

    ch = bot.get_channel(config["error channel"])
    await ch.send(f"```{m}```")
    await wormcog.presence(bot)


@bot.event
async def on_error(event, *args, **kwargs):
    if config["log level"] == "CRITICAL":
        return

    tb = traceback.format_exc()
    print(tb)

    channel = bot.get_channel(config["error channel"])
    if channel is None:
        print("ERROR: Error channel not found")
        return
    output = list(tb[0 + i : 1980 + i] for i in range(0, len(tb), 1980))
    for o in output:
        await channel.send(f"```{o}```")


##
## COMMANDS
##


@bot.command(hidden=True)
async def reload(ctx: commands.Context, cog: str):
    """Reload the wormhole"""
    if ctx.author.id != config["admin id"]:
        await ctx.send("You do not have permission to do this!", delete_after=5)
        return
    try:
        bot.reload_extension(f"cogs.{cog}")
        print(f"{cog.upper()} reloaded.")
        await ctx.send(f"**{cog.upper()}** reloaded.", delete_after=5)
    except Exception as e:
        await ctx.send(f"An error occured: ```\n{e}```", delete_after=20)


##
## INIT
##
bot.load_extension("cogs.errors")
for c in ["wormhole", "admin", "user"]:
    bot.load_extension(f"cogs.{c}")
    print(f"{c.upper()} loaded")

bot.run(config.get("bot key"))
