import json
import logging
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
        self.level = getattr(logging, config['log level'].upper())

    def bot(self, bot: discord.ext.commands.Bot):
        self.bot = bot

    async def debug(self, ctx, msg):
        await ctx.send(embed=self._getEmbed(ctx, "Debug", msg), delete_after=120)

    async def info(self, ctx, msg):
        await ctx.send(embed=self._getEmbed(ctx, "Info", msg), delete_after=120)

    async def warning(self, ctx, msg):
        await ctx.send(embed=self._getEmbed(ctx, "Warning", msg), delete_after=120)

    async def error(self, ctx, msg, error = None):
        embed = self._getEmbed(ctx, "Error", msg)

        if error:
            tr = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tr) > 2000:
                tr = tr[-2000:]
                embed.set_footer(text=f"```{tr}```")

        await ctx.send(embed=embed, delete_after=120)

    async def critical(self, ctx, msg, error = None):
        embed = self._getEmbed(ctx, "Critical", msg)

        if error:
            tr = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tr) > 2000:
                tr = tr[-2000:]
                embed.set_footer(text=f"```{tr}```")

        await ctx.send(embed=embed, delete_after=120)

    def _getEmbed(self, ctx, level, msg, ):
        colors = {
            "DEBUG": 0xefe19b,
            "INFO": 0x91c42b,
            "WARINNG": 0xce991e,
            "ERROR": 0xef4a13,
            "CRITICAL": 0xfc0509,
        }
        embed = discord.Embed(title="Wormhole output", color=colors[level.upper()])
        embed.add_field(name=level, value=msg)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        return embed

class Console:
    def __init__(self, bot: discord.ext.commands.Bot = None):
        self.bot = bot
        self.level = getattr(logging, config["log level"].upper())

        self.channel = None

    def bot(self, bot: discord.ext.commands.Bot):
        self.bot = bot
        self.channel = getLogChannel(self.bot)

    async def debug(self, msg, *args, **kwargs):
        if self.level <= logging.DEBUG:
            print(f"{getTimestamp()} DEBUG: {msg}")
            await self._send(msg, *args, **kwargs)

    async def info(self, msg, *args, **kwargs):
        if self.level <= logging.INFO:
            print(f"{getTimestamp()} INFO: {msg}")
            await self._send(msg, *args, **kwargs)

    async def warning(self, msg, *args, **kwargs):
        if self.level <= logging.WARNING:
            print(f"{getTimestamp()} WARNING: {msg}")
            await self._send(msg, *args, **kwargs)

    async def error(self, msg, *args, **kwargs):
        if self.level <= logging.ERROR:
            print(f"{getTimestamp()} ERROR: {msg}")
            await self._send(msg, *args, **kwargs)

    async def critical(self, msg, *args, **kwargs):
        if self.level <= logging.CRITICAL:
            print(f"{getTimestamp()} CRITICAL: {msg}")
            await self._send(msg, *args, **kwargs)

    async def _send(self, msg, *args, **kwargs):
        if self.channel is None:
                self.channel = getLogChannel(self.bot)

        await self.channel.send(f"```\n{getTimestamp()} {msg}\n```")

