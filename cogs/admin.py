import re
import json

import discord
from discord.ext import commands

from core import checks, errors, wormcog
from core.database import repo_b, repo_u, repo_w

config = json.load(open("config.json"))


class Admin(wormcog.Wormcog):
    """Manage wormholes"""

    def __init__(self, bot):
        super().__init__(bot)

    @commands.check(checks.is_admin)
    @commands.group(name="beam")
    async def beam(self, ctx: commands.Context):
        """Manage beams"""
        if ctx.invoked_subcommand is not None:
            return

        prefix = config["prefix"] + "beam…"
        values = [
            "add <name>",
            "open <name>",
            "close <name>",
            "edit <name> active [0, 1]",
            "edit <name> admin_id <member ID>",
            "edit <name> anonymity [none, guild, full]",
            "edit <name> replace [0, 1]",
            "edit <name> timeout <int>",
            "list",
        ]

        embed = self.getEmbed(ctx=ctx, title="Beams", description=prefix)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        await ctx.send(embed=embed, delete_after=self.delay("admin"))

    @beam.command(name="add", aliases=["create"])
    async def beam_add(self, ctx: commands.Context, name: str):
        """Add new beam"""
        # check names
        pattern = r"[a-zA-Z0-9_]+"
        if re.fullmatch(pattern, name) is None:
            raise errors.BadArgument(f"Beam name must match `{pattern}`")

        # add
        try:
            repo_b.add(name=name, admin_id=ctx.author.id)
            await self.console.info(f'Beam "{name}" created and opened')
            await self.embed.info(ctx, f"Beam **{name}** created and opened")
        except errors.DatabaseException as e:
            raise errors.BadArgument(f"Error creating the beam **{name}**", e)

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
            raise errors.BadArgument(f"Error opening the beam **{name}**", e)

    @beam.command(name="close", aliases=["disable"])
    async def beam_close(self, ctx: commands.Context, name: str):
        """Close beam"""
        if repo_b.get(name) is None:
            raise errors.BadArgument("Invalid beam")

        try:
            await self.send(
                ctx.message, name, "> The current wormhole beam has been closed.", system=True,
            )
            repo_b.set(name=name, active=0)
            await self.console.info(f'Beam "{name}" closed')
        except Exception as e:
            raise errors.BadArgument(f"Error closing the beam **{name}**", e)

    @beam.command(name="edit", aliases=["alter"])
    async def beam_edit(self, ctx: commands.Context, name: str, key: str, value: str):
        """Edit beam"""
        if not repo_b.exists(name):
            raise errors.BadArgument("Invalid beam")

        if value in ("active", "admin_id", "replace", "timeout"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        repo_b.set(name=name, key=key, value=value)

        await self.send(ctx, f"Beam **{name}** updated: {key} = {value}", system=True)
        await self.console.info(f"Beam {name} updated: {key} = {value}")

    @beam.command(name="list")
    async def beam_list(self, ctx: commands.Context):
        """List all wormholes"""
        embed = discord.Embed(title="Beam list")

        beam_names = repo_b.listNames()
        for beam_name in beam_names:
            beam = repo_b.get(beam_name)
            ws = len(repo_w.listIDs(beam=beam.name))
            name = f"**{beam.name}** ({'in' if not beam.active else ''}active) | {ws} wormholes"
            value = f"Anonymity _{beam.anonymity}_, " + f"timeout _{beam.timeout} s_ "
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @commands.group(name="wormhole")
    async def wormhole(self, ctx: commands.Context):
        """Manage wormholes"""
        if ctx.invoked_subcommand is not None:
            return

        description = config["prefix"] + "wormhole…"
        values = [
            "add <beam> [<channel ID>, None]",
            "close [<channel ID>, None]",
            "remove [<channel ID>, None]",
            "edit <channel ID> beam <beam>",
            "edit <channel ID> admin_id <member ID>",
            "edit <channel ID> active [0, 1]",
            "edit <channel ID> logo <string>",
            "edit <channel ID> readonly [0, 1]",
            "edit <channel ID> messages <int>",
            "list",
        ]

        embed = self.getEmbed(ctx=ctx, title="Wormholes", description=description)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        await ctx.send(embed=embed, delete_after=self.delay("admin"))

    @wormhole.command(name="add", aliases=["create"])
    async def wormhole_add(
        self, ctx: commands.Context, beam: str, channel: discord.TextChannel = None
    ):
        """Open new wormhole"""
        db_b = repo_b.get(beam)
        if not db_b:
            raise errors.BadArgument("No such beam")

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
            raise errors.BadArgument("Already a wormhole")

    @wormhole.command(name="open", aliases=["enable"])
    async def wormhole_open(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Reopen existing wormhole"""
        if channel is None:
            channel = ctx.channel

        w = repo_w.get(channel=channel.id)
        if w is None:
            raise errors.BadArgument("No such wormhole")

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
            raise errors.BadArgument("Could not open the wormhole", e)

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
            raise errors.BadArgument("Could not open the wormhole", e)

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
            raise errors.BadArgument("Could not remove the wormhole", e)

    @wormhole.command(name="edit", aliases=["alter"])
    async def wormhole_edit(self, ctx, channel: discord.TextChannel, key: str, value: str):
        """Edit wormhole"""
        if not repo_w.exists(channel.id):
            raise errors.BadArgument("Invalid wormhole")

        if value in ("admin_id", "active", "readonly", "messages"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        repo_w.set(discord_id=channel.id, key=key, value=value)

        g = self.sanitise(channel.guild.name)
        await self.console.info(f"Wormhole {channel.id} updated: {key} = {value}")
        beam = repo_w.get(channel.id).beam
        await self.send(
            ctx.message, beam, f"> Wormhole in **{g}** updated: {key} is {value}", system=True
        )

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
        if ctx.invoked_subcommand is not None:
            return

        description = config["prefix"] + "user…"
        values = [
            "add <member ID>",
            "remove <member ID>",
            "edit <member ID> home_id <channel ID>",
            "edit <member ID> mod [0, 1]",
            "edit <member ID> nickname <string>",
            "edit <member ID> readonly [0, 1]",
            "edit <member ID> restricted [0, 1]",
            "list",
        ]

        embed = self.getEmbed(ctx=ctx, title="Users", description=description)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        await ctx.send(embed=embed, delete_after=self.delay("admin"))

    @user.command(name="add")
    async def user_add(self, ctx: commands.Context, member: discord.Member):
        """Add user"""
        try:
            repo_u.add(member.id)
            await self.console.info(f"User {self.e(member.name)} ({member.id}) added")
            await self.embed.info(ctx, f"User **{self.e(member.name)}** added")
        except Exception as e:
            raise errors.BadArgument(f"Could not add the user {member.id}", e)

    @user.command(name="remove", aliases=["delete"])
    async def user_remove(self, ctx: commands.Context, member: discord.Member):
        """Remove user"""
        try:
            repo_u.remove(member.id)
            await self.console.info(f"User {self.e(member.name)} ({member.id}) removed")
            await self.embed.info(ctx, f"User **{self.e(member.name)}** removed")
        except Exception as e:
            raise errors.BadArgument(f"Could not remove the user {member.id}", e)

    @user.command(name="edit", aliases=["alter"])
    async def user_edit(self, ctx, member: discord.Member, key: str, value: str):
        """Edit user"""
        if not repo_u.exists(member.id):
            raise errors.BadArgument("Invalid user")

        if ctx.author.id != config["admin id"] and repo_u.getAttribute(member.id, "mod") == 1:
            return await ctx.send("> You do not have permission to alter mod accounts")
        if ctx.author.id != config["admin id"] and member.id == config["admin id"]:
            return await ctx.send("> You do not have permission to alter admin account")

        if value in ("home_id", "mod", "readonly", "restricted"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        repo_u.set(discord_id=member.id, key=key, value=value)

        await self.console.info(
            f"User {self.e(member.name)} ({member.id}) updated: {key} = {value}"
        )

    @user.command(name="list")
    async def user_list(self, ctx):
        """List all registered users"""
        db_users = repo_u.listObjects()

        # TODO This is not good enough

        template = "{name:>12}/{nickname:<12} | {mod:>3} {ro:>3} {restr:>3} | {home} ({guild})"
        title = template.format(
            name="NAME",
            nickname="NICKNAME",
            mod="MOD",
            ro="RO",
            restr="RES",
            home="HOME",
            guild="GUILD",
        )

        wormholes = {}

        result = []
        for db_user in db_users:
            # get user
            user = self.bot.get_user(db_user.discord_id)
            user_name = user.name if hasattr(user, "name") else "---"
            # get wormhole's guild
            if str(db_user.home_id) not in wormholes.keys():
                channel = self.bot.get_channel(db_user.home_id)
                if isinstance(channel, discord.TextChannel):
                    wormholes[str(db_user.home_id)] = self.sanitise(channel.guild.name)
                else:
                    wormholes[str(db_user.home_id)] = "---"

            # add string
            result.append(
                template.format(
                    name=user_name,
                    nickname=db_user.nickname,
                    mod=db_user.mod,
                    ro=db_user.readonly,
                    restr=db_user.restricted,
                    home=db_user.home_id,
                    guild=wormholes[str(db_user.home_id)],
                )
            )

        async def sendOutput(output: str):
            await ctx.send("```" + title + "\n" + output + "```")

        # iterate over the result
        output = ""
        for line in result:
            if len(output) > 1900:
                await sendOutput(output)
                output = ""
            output += "\n" + line
        await sendOutput(output)


def setup(bot):
    bot.add_cog(Admin(bot))
