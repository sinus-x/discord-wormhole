import asyncio
import json
from datetime import datetime

import discord
from discord.ext import commands

import init
from core import wormcog
from core.database import repo_b, repo_l, repo_u, repo_w

config = json.load(open("config.json"))


class Admin(wormcog.Wormcog):
    """Manage wormholes"""

    def __init__(self, bot):
        super().__init__(bot)
        self.mod_ids = [m.id for m in repo_u.getMods()]

    @commands.check(init.is_admin)
    @commands.group(name="beam")
    async def beam(self, ctx: commands.Context):
        """Manage beams"""
        if ctx.invoked_subcommand is None:
            # TODO Make Rubbergoddess-like help embed
            pass

    @beam.command(name="open", aliases=["create", "add"])
    async def beam_open(self, ctx: commands.Context, name: str):
        """Open new beam"""
        try:
            repo_b.add(name)
        except:
            # TODO Already exists
            return

    @beam.command(name="close", aliases=["remove"])
    async def beam_close(self, ctx: commands.Context, name: str):
        """Close beam"""
        try:
            repo_b.set(name=name, active=False)
            # TODO Disable all beam wormholes, if some
        except:
            # TODO Error
            return

    @beam.command(name="edit", aliases=["alter"])
    async def beam_edit(self, ctx: commands.Context, name: str, *args):
        """Edit beam"""
        if len(args) != 2:
            # TODO Wrong argument count
            return
        key = args[0]
        value = args[1]

        if key == "replace":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_b.set(name, replace=value)
            else:
                # TODO Wrong value
                return
        elif key == "anonymity":
            if value in ["none", "guild", "full"]:
                repo_b.set(name, anonymity=value)
            else:
                # TODO Wrong value
                return
        elif key == "timeout":
            try:
                value = int(value)
                value = 0 if value < 0 else value
                repo_b.set(name, timeout=value)
            except:
                # TODO Wrong value
                return
        elif key == "file_limit":
            try:
                value = int(value)
                repo_b.set(name, file_limit=value)
            except:
                # TODO Wrong value
                return
        else:
            # TODO Wrong key
            return

    @beam.command(name="list")
    async def beam_list(self, ctx: commands.Context):
        """List all wormholes"""
        bs = repo_b.getAll()

        result = "NAME" + " " * 10 + "ACTIVE REPLACE ANONYMITY TIMEOUT FILELIMIT\n"
        s = "{} {} {} {} {}"
        for b in bs:
            result += s.format(
                b.name.ljust(13),
                "yes   " if b.active else "no    ",
                "yes    " if b.replace else "no     ",
                b.anonymity.ljust(9),
                str(b.timeout).ljust(7),
                b.file_limit,
            )
        await ctx.send(f"```{result}```")

    @commands.check(init.is_admin)
    @commands.group(name="wormhole")
    async def wormhole(self, ctx: commands.Context):
        """Manage wormholes"""
        if ctx.invoked_subcommand is None:
            # TODO Make Rubbergoddess-like help embed
            pass

    @wormhole.command(name="open", aliases=["create", "add"])
    async def wormhole_open(self, ctx: commands.Context, beam: str, channel=None):
        """Open new wormhole"""
        beam = repo_b.get(beam)
        if not beam:
            # TODO No beam found
            return

        if channel:
            channel = str2int(channel)
        else:
            channel = ctx.channel.id
        try:
            repo_w.add(channel)
        except:
            # TODO Already exists
            return

    @wormhole.command(name="close")
    async def wormhole_close(self, ctx: commands.Context, channel=None):
        """Close wormhole"""
        if channel:
            channel = str2int(channel)
        else:
            channel = ctx.channel.id

        try:
            repo_b.set(name=name, active=False)
            # TODO Disable all beam wormholes, if there are registered
        except:
            # TODO Error
            return

    @wormhole.command(name="remove", aliases=["delete"])
    async def wormhole_remove(self, ctx: commands.Context, channel=None):
        """Remove wormhole from database"""
        if channel:
            channel = str2int(channel)
        else:
            channel = ctx.channel.id

        try:
            repo_b.delete(id=channel)
        except:
            # TODO Error
            return

    @wormhole.command(name="edit")
    async def wormhole_edit(self, ctx: commands.Context, channel=None):
        if channel:
            channel = str2int(channel)
        else:
            channel = ctx.channel.id

        if len(args) != 2:
            # TODO Wrong argument count
            return
        key = args[0]
        value = args[1]

        if key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_b.set(name, readonly=value)
            else:
                # TODO Wrong value
                return
        elif key == "logo":
            repo_b.set(name, logo=value)
        else:
            # TODO Wrong key
            return

    @wormhole.command(name="list")
    async def wormhole_list(self, ctx: commands.Context):
        """List all wormholes"""
        ws = repo_w.getAll()

        result = "CHANNEL     GUILD    ACTIVE READONLY LOGO"
        s = "{} {} {} {} {}"
        for w in ws:
            ch = self.bot.get_channel(w.channel)
            result += s.format(
                ch.name.rjust(12),
                ch.guild.name.rjust(8),
                "yes   " if w.active else "no    ",
                "yes   " if w.readonly else "no    ",
                w.logo.ljust(30),
            )
        await ctx.send(f"```{result}```")

    @commands.check(init.is_mod)
    @commands.group(name="user")
    async def user(self, ctx: commands.Context):
        """Manage users"""
        if ctx.invoked_subcommand is None:
            # TODO Make Rubbergoddess-like help embed
            pass

    @user.command(name="add")
    async def user_add(self, ctx: commands.Context, member: discord.Member):
        """Add user"""
        try:
            repo_u.add(member.id)
        except:
            # TODO Error
            return

    @user.command(name="remove", aliases=["delete"])
    async def user_remove(self, ctx: commands.Context, member: discord.Member):
        """Remove user"""
        try:
            repo_u.delete(member.id)
        except:
            # TODO Error
            return

    @user.command(name="edit")
    async def user_edit(self, ctx: commands.Context, member: discord.Member, *args):
        """Edit user"""
        if ctx.author.id != config["admin id"] and (
            member.id == config["admin id"] or member.id in self.mod_ids
        ):
            await ctx.send("You do not have permission to alter the this account.")
            return

        if len(args) != 2:
            # TODO Wrong argument count
            return
        key = args[0]
        value = args[1]

        if key == "nickname":
            value = None if value == "None" else value
            repo_b.set(name, nickname=value)
        if key == "mod":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_b.set(name, replace=value)
            else:
                # TODO Wrong value
                return
        if key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_b.set(name, readonly=value)
            else:
                # TODO Wrong value
                return
        else:
            # TODO Wrong key
            return

    def str2int(s: str):
        try:
            return int(s)
        except:
            # TODO Wrong value
            return


def setup(bot):
    bot.add_cog(Admin(bot))
