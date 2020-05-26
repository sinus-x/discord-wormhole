import json
import logging
import traceback
from datetime import datetime

import discord

config = json.load(open("config.json"))


def getLogChannel(bot: discord.ext.commands.Bot):
    return bot.get_channel(config["log channel"])


def getTimestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Embed:
    def __init__(self, bot: discord.ext.commands.Bot = None):
        self.bot = bot
        self.level = getattr(logging, config["log level"].upper())

    def bot(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def debug(self, ctx, msg, error=None):
        await ctx.send(embed=self.getEmbed(ctx, "Debug", msg, error), delete_after=120)

    async def info(self, ctx, msg, error=None):
        await ctx.send(embed=self.getEmbed(ctx, "Info", msg, error), delete_after=120)

    async def warning(self, ctx, msg, error=None):
        await ctx.send(embed=self.getEmbed(ctx, "Warning", msg, error), delete_after=120)

    async def error(self, ctx, msg, error=None):
        await ctx.send(embed=self.getEmbed(ctx, "Error", msg, error), delete_after=120)

    async def critical(self, ctx, msg, error=None):
        await ctx.send(embed=self.getEmbed(ctx, "Critical", msg, error), delete_after=120)

    def getEmbed(self, ctx, level, msg, error=None):
        colors = {
            "DEBUG": 0xEFE19B,
            "INFO": 0x91C42B,
            "WARINNG": 0xCE991E,
            "ERROR": 0xEF4A13,
            "CRITICAL": 0xFC0509,
        }
        embed = discord.Embed(title="Wormhole", color=colors[level.upper()])
        embed.add_field(name=level, value=msg, inline=False)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

        if error is not None:
            embed.add_field(name="Reason", value=str(error), inline=False)
            tr = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tr) > 1900:
                tr = tr[-1900:]
                embed.set_footer(text=f"{str(error)}\n{tr}")
        return embed


class Console:
    def __init__(self, bot: discord.ext.commands.Bot = None):
        self.bot = bot
        self.level = getattr(logging, config["log level"].upper())

        self.channel = None

    def bot(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.channel = getLogChannel(self.bot)

    async def debug(self, msg, error=None, *args, **kwargs):
        if self.level <= logging.DEBUG:
            print(f"{getTimestamp()} DEBUG: {msg}")
            await self._send(msg, error, *args, **kwargs)

    async def info(self, msg, error=None, *args, **kwargs):
        if self.level <= logging.INFO:
            print(f"{getTimestamp()} INFO: {msg}")
            await self._send(msg, error, *args, **kwargs)

    async def warning(self, msg, error=None, *args, **kwargs):
        if self.level <= logging.WARNING:
            print(f"{getTimestamp()} WARNING: {msg}")
            await self._send(msg, error, *args, **kwargs)

    async def error(self, msg, error=None, *args, **kwargs):
        if self.level <= logging.ERROR:
            print(f"{getTimestamp()} ERROR: {msg}")
            await self._send(msg, error, *args, **kwargs)

    async def critical(self, msg, error=None, *args, **kwargs):
        if self.level <= logging.CRITICAL:
            print(f"{getTimestamp()} CRITICAL: {msg}")
            await self._send(msg, error, *args, **kwargs)

    async def _send(self, msg, error, *args, **kwargs):
        if self.channel is None:
            self.channel = getLogChannel(self.bot)

        m = f"{getTimestamp()} {msg}"
        if error is not None:
            m += f"\n{str(error)}"

        await self.channel.send(f"```\n{m}\n```")
