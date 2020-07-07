import json
import traceback
from datetime import datetime

from discord.ext import commands

from core import wormcog, output, checks

config = json.load(open("config.json"))
bot = commands.Bot(command_prefix=config["prefix"], help_command=None)
event = output.Event(bot)

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

    ch = bot.get_channel(config["log channel"])
    await ch.send(f"```{m}```")
    await wormcog.presence(bot)


@bot.event
async def on_error(event, *args, **kwargs):
    if config["log level"] == "CRITICAL":
        return

    tb = traceback.format_exc()
    print(tb)

    channel = bot.get_channel(config["log channel"])
    if channel is None:
        print("ERROR: Error channel not found")
        return
    output = list(tb[0 + i : 1980 + i] for i in range(0, len(tb), 1980))
    for o in output:
        await channel.send(f"```{o}```")


##
## COMMANDS
##


@bot.command()
@commands.check(checks.is_admin)
async def load(ctx: commands.Context, cog: str):
    """Load module"""
    bot.load_extension(f"cogs.{cog}")
    await ctx.send(f"**{cog.upper()}** loaded.")
    await event.sudo(ctx, f"Loaded: {cog.upper()}")
    print(f"{cog.upper()} loaded")


@bot.command()
@commands.check(checks.is_admin)
async def reload(ctx: commands.Context, cog: str):
    """Reload module"""
    bot.reload_extension(f"cogs.{cog}")
    await ctx.send(f"**{cog.upper()}** reloaded.")
    await event.sudo(ctx, f"Reloaded: {cog.upper()}")
    print(f"{cog.upper()} reloaded")


@bot.command()
@commands.check(checks.is_admin)
async def unload(ctx: commands.Context, cog: str):
    """Unload module"""
    bot.unload_extension(f"cogs.{cog}")
    await ctx.send(f"**{cog.upper()}** unloaded.")
    await event.sudo(ctx, f"Unloaded: {cog.upper()}")
    print(f"{cog.upper()} unloaded")


##
## INIT
##
bot.load_extension("cogs.errors")
for c in ["wormhole", "admin", "user", "notifications"]:
    bot.load_extension(f"cogs.{c}")
    print(f"{c.upper()} loaded")

bot.run(config.get("bot key"))
