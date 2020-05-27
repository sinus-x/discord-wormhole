import asyncio
import json
import logging
import git

import discord
from discord.ext import commands

from core import database, errors, output
from core.database import repo_b, repo_u, repo_w

# TODO When the message is removed, remove it from sent[], too


config = json.load(open("config.json"))


async def presence(bot: commands.Bot):
    git_repo = git.Repo(search_parent_directories=True)
    git_hash = git_repo.head.object.hexsha[:7]
    s = f"{config['prefix']}help | " + git_hash
    await bot.change_presence(activity=discord.Game(s))


class Wormcog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        # active text channels acting as wormholes
        self.wormholes = {}

        # sent messages still held in memory
        self.sent = []

        # bot management logging
        self.console = output.Console(bot)
        self.embed = output.Embed(bot)

    ##
    ## FUNCTIONS
    ##

    def reconnect(self, beam: str = None):
        if beam == None:
            self.wormholes = {}
            ws = repo_w.getAll()
        else:
            self.wormholes[beam] = []
            ws = repo_w.getByBeam(beam)
        for w in repo_w.getByBeam(beam):
            self.wormholes[beam].append(self.bot.get_channel(w.channel))

    def removalDelay(self, key: str = "user"):
        if key == "user":
            return 20
        if key == "admin":
            return 10

    async def send(
        self,
        message: discord.Message,
        beam: str,
        text: str,
        files: list = None,
        announcement: bool = False,
        system: bool = False,
    ):
        """Distribute the message"""

        # get variables
        msgs = [message]
        user = repo_u.get(message.author.id)
        wormhole = repo_w.get(message.channel.id)
        if beam == None and wormhole != None:
            # try to get information from message
            beam = repo_b.get(wormhole.beam)
        else:
            # use supplied information
            beam = repo_b.get(beam)

        # access control
        if beam == None:
            return
        if not system and (not beam.active or (wormhole != None and not wormhole.active)):
            return
        if not system and (
            (wormhole != None and wormhole.readonly) or (user != None and user.readonly)
        ):
            return

        # if the bot has 'Manage messages' permission, remove the original
        if beam.replace and not files:
            try:
                msgs[0] = message.author
                await self.delete(message)
                announcement = True
            except discord.Forbidden:
                pass

        # limit message length
        if len(text) > 1000:
            text = text[:1000]

        # distribute the message
        if beam is None:
            ws = self.wormholes.values()
        else:
            if not beam.name in self.wormholes:
                self.reconnect(beam.name)
            ws = self.wormholes[beam.name]
        for w in ws:
            if w.id == message.channel.id and not announcement:
                continue
            if not repo_w.get(w.id).active:
                continue
            m = await w.send(content=text)
            msgs.append(m)

        # save message objects in case of editing/deletion
        if beam.timeout > 0:
            self.sent.append(msgs)
            await asyncio.sleep(beam.timeout)
            self.sent.remove(msgs)

    async def delete(self, message: discord.Message):
        """Try to delete original message"""
        try:
            await message.delete()
        except:
            return

    def message2Beam(self, message: discord.Message):
        wormhole = repo_w.get(message.channel.id)
        beam = repo_b.get(wormhole.beam)
        return beam
