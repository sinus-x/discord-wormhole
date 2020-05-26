import asyncio
import json
from datetime import datetime

import discord
from discord.ext import commands

from core import checks, errors, wormcog
from core.database import repo_b, repo_u, repo_w

config = json.load(open("config.json"))

# TODO Fix those awful error outputs (e.g. wormhole_edit)


class Admin(wormcog.Wormcog):
    """Manage wormholes"""

    def __init__(self, bot):
        super().__init__(bot)
        self.mod_ids = [m.id for m in repo_u.getMods()]

    @commands.check(checks.is_admin)
    @commands.group(name="beam")
    async def beam(self, ctx: commands.Context):
        """Manage beams"""
        if ctx.invoked_subcommand is None:
            # TODO Help embed
            pass

    @beam.command(name="add", aliases=["create"])
    async def beam_add(self, ctx: commands.Context, name: str):
        """Add new beam"""
        try:
            repo_b.add(name)
            await self.console.info(f'Beam "{name}" created and opened')
            await self.embed.info(ctx, f"Beam **{name}** created and opened")
        except errors.DatabaseException as e:
            await self.console.error(f'Beam "{name}" could not be created', e)
            await self.embed.error(ctx, f"Beam **{name}** could not be created", e)
            return

    @beam.command(name="open", aliases=["enable"])
    async def beam_open(self, ctx: commands.Context, name: str):
        """Open closed beam"""
        try:
            repo_b.set(name=name, active=True)
            await self.console.info(f"Beam {name} opened")
            await self.send(
                ctx.message,
                name,
                "> The current wormhole beam has been opened.",
                announcement=True,
            )
        except Exception as e:
            await self.console.error(f'Beam "{name}" could not be opened', e)
            await self.embed.error(ctx, f"Beam **{name}** could not be opened", e)
            return

    @beam.command(name="close", aliases=["disable"])
    async def beam_close(self, ctx: commands.Context, name: str):
        """Close beam"""
        try:
            repo_b.set(name=name, active=False)
            await self.console.info(f'Beam "{name}" closed')
            await self.send(
                ctx.message,
                name,
                "> The current wormhole beam has been closed.",
                announcement=True,
            )
        except Exception as e:
            await self.console.error(f'Beam "{name}" could not be closed', e)
            await self.embed.error(ctx, f"Beam **{name}** could not be closed", e)
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
                await self.console.error(f"Beam {name} update error: {key} = {value}")
                await self.embed.error(ctx, f"Beam **{name}** update error: {key} = {value}")
                return
        elif key == "anonymity":
            if value in ["none", "guild", "full"]:
                repo_b.set(name, anonymity=value)
            else:
                await self.console.error(f"Beam {name} update error: {key} = {value}")
                await self.embed.error(ctx, f"Beam **{name}** update error: {key} = {value}")
                return
        elif key == "timeout":
            try:
                value = int(value)
                value = 0 if value < 0 else value
            except Exception as e:
                await self.console.error(f"Beam {name} update error: {key} = {value}", e)
                await self.embed.error(ctx, f"Beam **{name}** update error: {key} = {value}", e)
                return
        else:
            await self.console.error(f"Beam {name} update error: invalid key {key}")
            await self.embed.error(ctx, f"Beam **{name}** update error: invalid key {key}")
            return

        await self.console.info(f"Beam {name} updated: {key} = {value}")
        await self.embed.info(ctx, f"Beam **{name}** updated: {key} = {value}")

    @beam.command(name="list")
    async def beam_list(self, ctx: commands.Context):
        """List all wormholes"""
        bs = repo_b.getAll()

        embed = discord.Embed(title="Beam list")

        for b in bs:
            ws = len(repo_w.getByBeam(b.name))
            name = f"**{b.name}** ({'in' if not b.active else ''}active) | {ws} wormholes"

            value = f"Anonymity _{b.anonymity}_, " + f"timeout _{b.timeout} s_ "
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @commands.group(name="wormhole")
    async def wormhole(self, ctx: commands.Context):
        """Manage wormholes"""
        if ctx.invoked_subcommand is None:
            # TODO Make Rubbergoddess-like help embed
            pass

    @wormhole.command(name="add", aliases=["create"])
    async def wormhole_add(
        self, ctx: commands.Context, beam: str, channel: discord.TextChannel = None
    ):
        """Open new wormhole"""
        beam = repo_b.get(beam)
        if not beam:
            await self.console.error(f'Beam "{name}" not found')
            await self.embed.error(ctx, f"Beam **{name}** not found")
            return

        if channel is None:
            channel = ctx.channel

        try:
            repo_w.add(beam=beam.name, channel=channel.id)
            ch_name = discord.utils.escape_markdown(channel.name)
            g_name = discord.utils.escape_markdown(channel.guild.name)
            await self.console.info(
                f'Channel {channel.id} in "{g_name}" added to beam "{beam.name}"'
            )
            await self.send(
                ctx.message,
                beam.name,
                f"> New wormhole opened: **{ch_name}** in **{g_name}**.",
                announcement=True,
            )
        except errors.DatabaseException as e:
            await self.console.error(f"Channel {channel.id} is already registered as a wormhole", e)
            await self.embed.error(
                ctx, f"Channel **{channel.id}** is already registered as a wormhole", e
            )
            return

    @wormhole.command(name="open")
    async def wormhole_open(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Reopen existing wormhole"""
        if channel is None:
            channel = ctx.channel

        w = repo_w.get(channel=channel.id)
        if w is None:
            await self.console.error(f"No wormhole {channel.id} found. Has it been added?")
            await self.embed.error(ctx, f"No wormhole **{channel.id}** found. Has it been added?")
            return

        try:
            repo_w.set(channel=channel.id, active=True)
            await self.console.info(f"Wormhole {channel.id} opened")
            ch_name = discord.utils.escape_markdown(channel.name)
            g_name = discord.utils.escape_markdown(channel.guild.name)
            await self.send(
                ctx.message,
                None,
                f"> Wormhole opened: **{ch_name}** in **{g_name}**.",
                announcement=True,
            )
        except errors.DatabaseException as e:
            await self.console.error(f"Wormhole {channel.id} could not be opened", e)
            await self.embed.error(ctx, f"Wormhole **{channel.id}** could not be opened", e)
            return

    @wormhole.command(name="close")
    async def wormhole_close(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Close wormhole"""
        if channel is None:
            channel = ctx.channel

        try:
            repo_w.set(channel=channel.id, active=False)
            await self.console.info(f"Wormhole {channel.id} closed")
            ch_name = discord.utils.escape_markdown(channel.name)
            g_name = discord.utils.escape_markdown(channel.guild.name)
            await self.send(
                ctx.message,
                None,
                f"> Wormhole closed: **{ch_name}** in **{g_name}**.",
                announcement=True,
            )
        except errors.DatabaseException as e:
            await self.console.error(f"Wormhole {channel.id} could not be closed", e)
            await self.embed.error(ctx, f"Wormhole **{channel.id}** could not be closed", e)
            return

    @wormhole.command(name="remove", aliases=["delete"])
    async def wormhole_remove(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Remove wormhole from database"""
        if channel is None:
            channel = ctx.channel

        try:
            beam = repo_w.get(channel.id).beam
            repo_w.remove(channel.id)
            await self.console.info(f"Wormhole {channel.id} removed")
            ch_name = discord.utils.escape_markdown(channel.name)
            g_name = discord.utils.escape_markdown(channel.guild.name)
            await self.send(
                ctx.message,
                beam,
                f"> Wormhole removed: **{ch_name}** in **{g_name}**.",
                announcement=True,
            )
            await ctx.send("> Wormhole removed.")
        except errors.DatabaseException as e:
            await self.console.error(f"Wormhole {channel.id} could not be removed", e)
            await self.embed.error(ctx, f"Wormhole **{channel.id}** could not be removed", e)
            return

    @wormhole.command(name="edit")
    async def wormhole_edit(self, ctx: commands.Context, channel: discord.TextChannel, *args):
        g_name = discord.utils.escape_markdown(channel.guild.name)
        channel = channel.id

        if len(args) != 2:
            await self.embed.error(ctx, f"Wormhole update error: Wrong argument count")
            return
        key = args[0]
        value = args[1]

        if key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                try:
                    repo_w.set(channel, readonly=value)
                except errors.DatabaseException as e:
                    await self.console.error(f"Wormhole update error: {key} = {value}")
                    await self.embed.error(ctx, f"Wormhole update error: {key} = {value}")
                    return
            else:
                await self.console.error(f"Wormhole update error: {key} = {value}")
                await self.embed.error(ctx, f"Wormhole update error: {key} = {value}")
                return
        elif key == "logo":
            try:
                repo_w.set(channel, logo=value)
            except errors.DatabaseException as e:
                await self.console.error(f"Wormhole update error: {key} = {value}")
                await self.embed.error(ctx, f"Wormhole update error: {key} = {value}")
                return
        else:
            await self.console.error(f"Wormhole update error: invalid key {key}")
            await self.embed.error(ctx, f"Wormhole update error: invalid key {key}")
            return

        await self.console.info(f"Wormhole {name} updated: {key} = {value}")
        await self.embed.info(ctx, f"Wormhole **{name}** updated: {key} = {value}")

        await self.send(ctx.message, None, f"> Wormhole in **{g_name}** updated: {key} is {value}")

    @wormhole.command(name="list")
    async def wormhole_list(self, ctx: commands.Context):
        """List all wormholes"""
        ws = repo_w.getAll()

        embed = discord.Embed(title="Wormhole list")
        for w in ws:
            ch = self.bot.get_channel(w.channel)
            g = discord.utils.escape_markdown(ch.guild.name)
            name = "\u200B"
            value = f"**{ch.mention}** ({g}): "
            value += f"{'in' if not w.active else ''}active"
            value += ", read only" if w.readonly else ""
            value += f", {w.logo}" if w.logo else ""
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.check(checks.is_mod)
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
            print(f"User {member} ({member.id}) added to database")
        except:
            # TODO Error
            print(f"Could not add {member} ({member.id}) to the database")
            return

    @user.command(name="remove", aliases=["delete"])
    async def user_remove(self, ctx: commands.Context, member: discord.Member):
        """Remove user"""
        try:
            repo_u.remove(member.id)
            print(f"User {member} ({member.id}) remove from the database")
        except:
            # TODO Error
            print(f"Could not remove {member} ({member.id}) from the database")
            return

    @user.command(name="edit")
    async def user_edit(self, ctx: commands.Context, member: discord.Member, *args):
        """Edit user

        member: A discord member
        key:value:
            nickname: string or None
            mod:      true or false
            readonly: true or false
        """
        if ctx.author.id != config["admin id"] and member.id in self.mod_ids:
            return await ctx.send("> You do not have permission to alter mod account.")
        if ctx.author.id != config["admin id"] and member.id == config["admin id"]:
            return await ctx.send("> You do not have permission to alter admin account")

        if len(args) != 2:
            # TODO Wrong argument count
            return
        key = args[0]
        value = args[1]

        if key == "nickname":
            value = None if value == "None" else value
            repo_u.set(member.id, nickname=value)
        if key == "mod":
            if value.lower() in ["true", "false"]:
                value = True if value.lower() == "true" else False
                repo_u.set(member.id, mod=value)
            else:
                # TODO Wrong value
                return
        if key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_u.set(member.id, readonly=value)
            else:
                # TODO Wrong value
                return
        else:
            # TODO Wrong key
            return

    @user.command(name="list")
    async def user_list(self, ctx):
        """List all registered users"""
        us = repo_u.getAll()
        embed = discord.Embed(title="User list")
        for u in us:
            user = self.bot.get_user(u.id)
            name = "MOD" if u.mod else "\u200B"
            value = f"{user.mention}"
            value += f" {discord.utils.escape_markdown(u.nickname)}. " if u.nickname else ". "
            value += "Read only. " if u.readonly else ""
            if u.restricted:
                ch = self.bot.get_channel(u.restricted)
                g = discord.utils.escape_markdown(ch.guild.name)
                value += f"restricted to {ch.mention} ({g})"
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    def str2int(self, s):
        if isinstance(s, discord.TextChannel):
            return s.id
        try:
            return int(s)
        except:
            # TODO Wrong value
            return


def setup(bot):
    bot.add_cog(Admin(bot))
