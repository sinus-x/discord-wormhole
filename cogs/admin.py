import re
import json

import discord
from discord.ext import commands

from core import checks, errors, wormcog
from core.database import repo_b, repo_u, repo_w

config = json.load(open("config.json"))

# TODO Raise WormholeException instead of BadArgument


class Admin(wormcog.Wormcog):
    """Manage wormholes"""

    def __init__(self, bot):
        super().__init__(bot)

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
        # check names
        pattern = r"[a-zA-Z0-9_]+"
        if re.fullmatch(pattern, name) is None:
            raise commands.BadArgument(f"Beam name must match `{pattern}`")

        # add
        try:
            repo_b.add(name=name, admin_id=ctx.author.id)
            await self.console.info(f'Beam "{name}" created and opened')
            await self.embed.info(ctx, f"Beam **{name}** created and opened")
        except errors.DatabaseException as e:
            raise commands.BadArgument(f"Error creating the beam **{name}**", e)

    @beam.command(name="open", aliases=["enable"])
    async def beam_open(self, ctx: commands.Context, name: str):
        """Open closed beam"""
        try:
            repo_b.set(name=name, active=1)
            await self.console.info(f'Beam "{name}" opened')
            await self.send(
                ctx.message, name, "> The current wormhole beam has been opened.", system=True,
            )
        except Exception as e:
            raise commands.BadArgument(f"Error opening the beam **{name}**", e)

    @beam.command(name="close", aliases=["disable"])
    async def beam_close(self, ctx: commands.Context, name: str):
        """Close beam"""
        if repo_b.get(name) is None:
            raise commands.BadArgument("Invalid beam")

        try:
            await self.send(
                ctx.message, name, "> The current wormhole beam has been closed.", system=True,
            )
            repo_b.set(name=name, active=0)
            await self.console.info(f'Beam "{name}" closed')
        except Exception as e:
            raise commands.BadArgument(f"Error closing the beam **{name}**", e)

    @beam.command(name="edit", aliases=["alter"])
    async def beam_edit(self, ctx: commands.Context, name: str, key: str, value: str):
        """Edit beam

        key:value
        - admin_id: [int] (user ID)
        - anonymity: [none | guild | full]
        - replace: [0 | 1]
        - timeout: [int] (seconds)
        """
        if repo_b.get(name) is None:
            raise commands.BadArgument("Invalid beam")

        if value in ("active", "admin_id", "replace", "timeout"):
            value = int(value)

        repo_b.set(name=name, key=key, value=value)

        await self.send(ctx, f"Beam **{name}** updated: {key} = {value}", system=True)
        await self.console.info(f"Beam {name} updated: {key} = {value}")

    @beam.command(name="list")
    async def beam_list(self, ctx: commands.Context):
        """List all wormholes"""
        embed = discord.Embed(title="Beam list")

        beams = repo_b.listNames()
        for beam in beams:
            ws = len(repo_w.listIDs(beam=beam.name))
            name = f"**{beam.name}** ({'in' if not beam.active else ''}active) | {ws} wormholes"
            value = f"Anonymity _{beam.anonymity}_, " + f"timeout _{beam.timeout} s_ "
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @commands.group(name="wormhole")
    async def wormhole(self, ctx: commands.Context):
        """Manage wormholes"""
        if ctx.invoked_subcommand is None:
            pass

    @wormhole.command(name="add", aliases=["create"])
    async def wormhole_add(
        self, ctx: commands.Context, beam: str, channel: discord.TextChannel = None
    ):
        """Open new wormhole"""
        db_b = repo_b.get(beam)
        if not db_b:
            raise commands.BadArgument("No such beam")

        if channel is None:
            channel = ctx.channel

        try:
            repo_w.add(beam=db_b.name, channel=channel.id)
            await self.console.info(
                f'Channel {channel.id} in "{self.e(channel.guild.name)}" added to beam "{db_b.name}"'
            )
            await self.send(
                ctx.message,
                db_b.name,
                f"> New wormhole opened: **{self.e(channel.name)}** in **{self.e(channel.guild.name)}**.",
                system=True,
            )
        except errors.DatabaseException:
            raise commands.BadArgument("Already a wormhole")

    @wormhole.command(name="open", aliases=["enable"])
    async def wormhole_open(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Reopen existing wormhole"""
        if channel is None:
            channel = ctx.channel

        w = repo_w.get(channel=channel.id)
        if w is None:
            raise commands.BadArgument("No such wormhole")

        try:
            repo_w.set(channel=channel.id, active=True)
            await self.console.info(f"Wormhole {channel.id} opened")
            await self.send(
                ctx.message,
                None,
                f"> Wormhole opened: **{self.e(channel.name)}** in **{self.e(channel.guild.name)}**.",
                system=True,
            )
        except errors.DatabaseException as e:
            raise commands.BadArgument("Could not open the wormhole", e)

    @wormhole.command(name="close", aliases=["disable"])
    async def wormhole_close(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Close wormhole"""
        if channel is None:
            channel = ctx.channel

        try:
            await self.send(
                ctx.message,
                None,
                f"> Wormhole closed: **{self.e(channel.name)}** in **{self.e(channel.guild.name)}**.",
                system=True,
            )
            repo_w.set(channel=channel.id, active=False)
            await self.console.info(f"Wormhole {channel.id} closed")
        except errors.DatabaseException as e:
            raise commands.BadArgument("Could not open the wormhole", e)

    @wormhole.command(name="remove", aliases=["delete"])
    async def wormhole_remove(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Remove wormhole from database"""
        if channel is None:
            channel = ctx.channel

        try:
            beam = repo_w.get(channel.id).beam
            await self.send(
                ctx.message,
                beam,
                f"> Wormhole removed: **{self.e(channel.name)}** in **{self.e(channel.guild.name)}**.",
                system=True,
            )
            repo_w.remove(channel.id)
            await self.console.info(f"Wormhole {channel.id} removed")
            await ctx.send("> Wormhole removed.")
        except errors.DatabaseException as e:
            raise commands.BadArgument("Could not remove the wormhole", e)

    @wormhole.command(name="edit", aliases=["alter"])
    async def wormhole_edit(self, ctx: commands.Context, channel: discord.TextChannel, *args):
        """Edit wormhole

        channel: A text channel
        key:value
        - readonly: [true | false]
        - logo: <emote>
        """
        g = discord.utils.escape_markdown(channel.guild.name)

        if len(args) != 2:
            raise commands.BadArgument("Expecting key and value")

        key = args[0]
        value = args[1]

        msg = ""
        if key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                try:
                    repo_w.set(channel.id, readonly=value)
                    if value is True:
                        msg = "read only"
                    else:
                        msg = "read-write"
                except errors.DatabaseException as e:
                    raise commands.BadArgument("Updating error", e)
            else:
                raise commands.BadArgument("Expecting `true` or `false`")
        elif key == "logo":
            try:
                repo_w.set(channel.id, logo=value)
                msg = f"logo is now {value}"
            except errors.DatabaseException as e:
                raise commands.BadArgument("Updating error", e)
        else:
            raise commands.BadArgument("Expecting an emote or a string")

        await self.console.info(f"Wormhole {channel.id} updated: {key} = {value}")
        beam = repo_w.get(channel.id).beam
        await self.send(ctx.message, beam, f"> Wormhole in **{g}** updated: {msg}", system=True)

    @wormhole.command(name="list")
    async def wormhole_list(self, ctx: commands.Context):
        """List all wormholes"""
        ws = repo_w.getAll()

        embed = discord.Embed(title="Wormhole list")
        for w in ws:
            ch = self.bot.get_channel(w.channel)
            name = "\u200B"
            value = f"**{ch.mention}** ({self.e(ch.guild.name)}): "
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
            # TODO Help embed
            pass

    @user.command(name="add")
    async def user_add(self, ctx: commands.Context, member: discord.Member):
        """Add user"""
        try:
            repo_u.add(member.id)
            await self.console.info(f"User {self.e(member.name)} ({member.id}) added")
            await self.embed.info(ctx, f"User **{self.e(member.name)}** added")
        except Exception as e:
            raise commands.BadArgument(f"Could not add the user {member.id}", e)

    @user.command(name="remove", aliases=["delete"])
    async def user_remove(self, ctx: commands.Context, member: discord.Member):
        """Remove user"""
        try:
            repo_u.remove(member.id)
            await self.console.info(f"User {self.e(member.name)} ({member.id}) removed")
            await self.embed.info(ctx, f"User **{self.e(member.name)}** removed")
        except Exception as e:
            raise commands.BadArgument(f"Could not remove the user {member.id}", e)

    @user.command(name="edit", aliases=["alter"])
    async def user_edit(self, ctx: commands.Context, member: discord.Member, *args):
        """Edit user

        member: A discord member
        key:value:
            nickname: string or None
            mod:      true or false
            readonly: true or false
        """
        if ctx.author.id != config["admin id"] and repo_u.getAttribute(member.id, "mod") == 1:
            return await ctx.send("> You do not have permission to alter mod accounts")
        if ctx.author.id != config["admin id"] and member.id == config["admin id"]:
            return await ctx.send("> You do not have permission to alter admin account")

        if len(args) != 2:
            raise commands.BadArgument("Expecting key and value")

        key = args[0]
        value = args[1]

        if key == "nickname":
            if "(" in value or ")" in value:
                return await ctx.send("The name cannot contain `(` or `)`")
            repo_u.set(member.id, nickname=value)
        if key == "mod":
            if value.lower() in ["true", "false"]:
                value = True if value.lower() == "true" else False
                repo_u.set(member.id, mod=value)
                if value is True:
                    await self.send(
                        ctx.message, None, f"> New mod: **{self.e(member.name)}**", system=True
                    )
                    await member.send("You are now a Wormhole mod!")
                else:
                    await member.send("You are no longer a Wormhole mod.")
            else:
                raise commands.BadArgument("Expecting true or false")
        elif key == "readonly":
            if value in ["true", "false"]:
                value = True if value == "true" else False
                repo_u.set(member.id, readonly=value)
                if value is True:
                    await member.send(
                        "You have been silenced. Wormhole won't accept your messages."
                    )
                else:
                    await member.send("You are no longer silenced.")
            else:
                raise commands.BadArgument("Expecting true or false")
        elif key == "home":
            if value.lower() == "none":
                repo_u.set(member.id, home=None)
            try:
                converter = commands.TextChannelConverter()
                home = await converter.convert(ctx=ctx, argument=value)
                repo_u.set(member.id, home=home.id)
                await member.send(
                    f"Your home wormhole has been set to {home.mention} in **{self.e(home.guild.name)}**"
                )
            except commands.errors.BadArgument:
                raise commands.BadArgument(f"{value} is not valid channel")
        else:
            raise commands.BadArgument("Unknown key")

        await self.console.info(
            f"User {self.e(member.name)} ({member.id}) updated: {key} = {value}"
        )

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
            if u.home:
                ch = self.bot.get_channel(u.home)
                g = discord.utils.escape_markdown(ch.guild.name)
                value += f"home in {ch.mention} ({g})"
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    def str2int(self, s):
        if isinstance(s, discord.TextChannel):
            return s.id
        try:
            return int(s)
        except:
            raise commands.UserInputError("Could not convert to int: " + str(s))


def setup(bot):
    bot.add_cog(Admin(bot))
