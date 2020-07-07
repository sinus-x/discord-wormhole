import json
import logging
import traceback
from datetime import datetime

import discord
from discord.ext import commands

config = json.load(open("config.json"))


class Event:
    def __init__(self, bot):
        self.bot = bot
        self.channel = None

        self.user_template = "{user} in {location}: {message}"
        self.sudo_template = "**SUDO** {user} in {location}: {message}"

    def getChannel(self):
        if self.channel is None:
            self.channel = self.bot.get_channel(config["log channel"])
        return self.channel

    async def user(self, ctx: commands.Context, message: str):
        """Unprivileged events"""
        # fmt: off
        await self.getChannel().send(self.user_template.format(
            user=str(ctx.author),
            location=f"{ctx.channel.mention} ({ctx.guild.name})"
            if hasattr(ctx.channel, "mention")
            else type(ctx.channel).__name__,
            message=message.replace("@", "@\u200b"),
        ))
        # fmt: on

    async def sudo(self, ctx: commands.Context, message: str):
        """Privileged events"""
        # fmt: off
        await self.getChannel().send(self.sudo_template.format(
            user=str(ctx.author),
            location=f"{ctx.channel.mention} ({ctx.guild.name})"
            if hasattr(ctx.channel, "mention")
            else type(ctx.channel).__name__,
            message=message.replace("@", "@\u200b"),
        ))
        # fmt: on
