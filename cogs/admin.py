import re
import json

import discord
from discord.ext import commands

from core import checks, errors, wormcog
from core.database import repo_b, repo_u, repo_w

config = json.load(open("config.json"))


def is_id(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class Admin(wormcog.Wormcog):
    """Manage wormholes"""

    def __init__(self, bot):
        super().__init__(bot)

    @commands.check(checks.in_wormhole)
    @commands.check(checks.is_admin)
    @commands.command(name="announce")
    async def announce_(self, ctx, *, message):
        """Send announcement"""
        await self.announce(beam=repo_w.get_attribute(ctx.channel.id, "beam"), message=message)

    @commands.check(checks.in_wormhole)
    @commands.check(checks.is_mod)
    @commands.command(name="block", aliases=["ban"])
    async def block(self, ctx, member: discord.Member):
        """Block discord user from sending messages"""
        nickname = self.sanitise(member.name, limit=16).replace(")", "").replace("(", "")
        nickname = self.get_free_nickname(nickname)

        if not repo_u.exists(discord_id=member.id):
            self.user_add(ctx, member_id=member.id, nickname=nickname)

        repo_u.set(discord_id=member.id, key="readonly", value=1)
        await self.event.sudo(ctx, f"User **{nickname}** blocked.")

    @commands.check(checks.is_admin)
    @commands.check(checks.not_in_wormhole)
    @commands.group(name="beam")
    async def beam(self, ctx):
        """Manage beams"""
        await self.delete(ctx)

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

        embed = self.get_embed(ctx=ctx, title="Beams", description=prefix)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        embed.add_field(
            name="Online help",
            value="https://sinus-x.github.io/discord-wormhole/administration#beam",
            inline=False,
        )
        await ctx.send(embed=embed)

    @beam.command(name="add", aliases=["create"])
    async def beam_add(self, ctx, name: str):
        """Add new beam"""
        # check names
        pattern = r"[a-zA-Z0-9_]+"
        if re.fullmatch(pattern, name) is None:
            raise errors.BadArgument(f"Beam name must match `{pattern}`")

        repo_b.add(name=name, admin_id=ctx.author.id)
        await self.event.sudo(ctx, f"Beam **{name}** created.")
        await self.feedback(ctx, private=False, message=f"Beam **{name}** created and opened.")

    @beam.command(name="open", aliases=["enable"])
    async def beam_open(self, ctx, name: str):
        """Open closed beam"""
        repo_b.set(name=name, key="active", value=1)
        await self.event.sudo(ctx, f"Beam **{name}** opened.")
        await self.announce(beam=name, message="Beam opened!")

    @beam.command(name="close", aliases=["disable"])
    async def beam_close(self, ctx, name: str):
        """Close beam"""
        repo_b.set(name=name, key="active", value=0)
        await self.event.sudo(ctx, f"Beam **{name}** closed.")
        await self.announce(beam=name, message="Beam closed.")

    @beam.command(name="edit", aliases=["set"])
    async def beam_edit(self, ctx, name: str, key: str, value: str):
        """Edit beam"""
        if not repo_b.exists(name):
            raise errors.BadArgument("Invalid beam")

        if key in ("active", "admin_id", "replace", "timeout"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        announce = True
        if key in ("admin_id"):
            announce = False

        repo_b.set(name=name, key=key, value=value)

        await self.event.sudo(ctx, f"Beam **{name}** updated: {key} = {value}.")
        if not announce:
            return
        await self.announce(beam=name, message=f"Beam updated: {key} is now {value}.")

    @beam.command(name="list")
    async def beam_list(self, ctx):
        """List all wormholes"""
        embed = discord.Embed(title="Beam list")

        beam_names = repo_b.list_names()
        for beam_name in beam_names:
            beam = repo_b.get(beam_name)
            ws = len(repo_w.list_ids(beam=beam.name))
            name = f"**{beam.name}** ({'in' if not beam.active else ''}active) | {ws} wormholes"
            value = f"Anonymity _{beam.anonymity}_, " + f"timeout _{beam.timeout} s_ "
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @commands.check(checks.is_admin)
    @commands.check(checks.not_in_wormhole)
    @commands.group(name="wormhole")
    async def wormhole(self, ctx):
        """Manage wormholes"""
        await self.delete(ctx)

        if ctx.invoked_subcommand is not None:
            return

        description = config["prefix"] + "wormhole…"
        values = [
            "add <beam> [<channel ID>, None]",
            "remove [<channel ID>, None]",
            "edit <channel ID> beam <beam>",
            "edit <channel ID> admin_id <member ID>",
            "edit <channel ID> active [0, 1]",
            "edit <channel ID> logo <string>",
            "edit <channel ID> readonly [0, 1]",
            "edit <channel ID> messages <int>",
            "edit <channel ID> invite <invite link>" "list",
        ]

        embed = self.get_embed(ctx=ctx, title="Wormholes", description=description)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        embed.add_field(
            name="Online help",
            value="https://sinus-x.github.io/discord-wormhole/administration#wormhole",
            inline=False,
        )
        await ctx.send(embed=embed)

    @wormhole.command(name="add", aliases=["create"])
    async def wormhole_add(self, ctx, beam: str, channel_id: int = None):
        """Open new wormhole"""
        channel = self._get_channel(ctx=ctx, channel_id=channel_id)
        if channel is None:
            raise errors.BadArgument("No such channel")

        repo_w.add(beam=beam, discord_id=channel.id)
        await self.event.sudo(
            ctx,
            f"{self._w2str_log(channel)} added. {ctx.author.mention}, can you set the local admin?",
        )
        await self.announce(beam=beam, message=f"Wormhole opened: {self._w2str_out(channel)}.")

    @wormhole.command(name="remove", aliases=["delete"])
    async def wormhole_remove(self, ctx, channel_id: int = None):
        """Remove wormhole from database"""
        if channel_id is None:
            if hasattr(ctx.channel, "id"):
                channel_id = ctx.channel.id
            else:
                raise errors.BadArgument("Missing channel ID")
        channel = self._get_channel(ctx=ctx, channel_id=channel_id)
        if channel is None:
            raise errors.BadArgument("No such channel")

        beam_name = repo_w.get_attribute(channel_id, "beam")
        repo_w.delete(discord_id=channel_id)
        await self.event.sudo(ctx, f"{self._w2str_log(channel)} removed.")
        await self.announce(beam=beam_name, message=f"Wormhole closed: {self._w2str_out(channel)}.")
        await channel.send(f"Wormhole closed: {self._w2str_out(channel)}.")

    @wormhole.command(name="edit", aliases=["set"])
    async def wormhole_edit(self, ctx, channel_id: int, key: str, value: str):
        """Edit wormhole"""
        if key in ("admin_id", "active", "readonly", "messages"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        announce = True
        if key in ("invite", "messages", "admin_id"):
            announce = False

        channel = self._get_channel(ctx=ctx, channel_id=channel_id)

        beam_name = repo_w.get_attribute(channel_id, "beam")
        repo_w.set(discord_id=channel.id, key=key, value=value)
        await self.event.sudo(ctx, f"{self._w2str_log(channel)}: {key} = {value}.")

        if not announce:
            return
        await self.announce(
            beam=beam_name,
            message=f"Womhole {self._w2str_out(channel)} updated: {key} is {value}.",
        )

    @wormhole.command(name="list")
    async def wormhole_list(self, ctx):
        """List all wormholes"""
        embed = self.get_embed(ctx=ctx, title="Wormholes")
        template = "**{mention}** ({guild}): active {active}, readonly {readonly}"

        beams = repo_b.list_names()
        for beam in beams:
            wormholes = repo_w.list_objects(beam=beam)
            value = []
            for db_w in wormholes:
                wormhole = self.bot.get_channel(db_w.discord_id)
                if wormhole is None:
                    value.append("Missing: " + str(db_w))
                    continue
                value.append(
                    template.format(
                        mention=wormhole.mention,
                        guild=wormhole.guild.name,
                        active=db_w.active,
                        readonly=db_w.readonly,
                    )
                )
            value = "\n".join(value)
            if len(value) == 0:
                value = "No wormholes"
            embed.add_field(name=beam, value=value, inline=False)

        await ctx.send(embed=embed)

    @commands.check(checks.is_mod)
    @commands.check(checks.not_in_wormhole)
    @commands.group(name="user")
    async def user(self, ctx):
        """Manage users"""
        await self.delete(ctx)

        if ctx.invoked_subcommand is not None:
            return

        description = config["prefix"] + "user…"
        values = [
            "add <member ID> <nickname>",
            "remove <member ID>",
            "edit <member ID> home_id:<beam> <channel ID>",
            "edit <member ID> mod [0, 1]",
            "edit <member ID> nickname <string>",
            "edit <member ID> readonly [0, 1]",
            "edit <member ID> restricted [0, 1]",
            "list [<beam>, <channel ID>, <user attribute>]",
        ]

        embed = self.get_embed(ctx=ctx, title="Users", description=description)
        embed.add_field(name="Commands", value="```" + "\n".join(values) + "```")
        embed.add_field(
            name="Online help",
            value="https://sinus-x.github.io/discord-wormhole/administration#user",
            inline=False,
        )
        await ctx.send(embed=embed)

    @user.command(name="add")
    async def user_add(self, ctx, member_id: int, nickname: str):
        """Add user"""
        repo_u.add(discord_id=member_id, nickname=nickname)
        self.event.sudo(ctx, f"{str(repo_u.get(member_id))}.")

    @user.command(name="remove", alises=["delete"])
    async def user_remove(self, ctx, member_id: int):
        """Remove user"""
        if ctx.author.id != config["admin id"] and repo_u.get_attribute(member_id, "mod") == 1:
            return await ctx.send("> You do not have permission to alter mod accounts")
        if ctx.author.id != config["admin id"] and member_id == config["admin id"]:
            return await ctx.send("> You do not have permission to alter admin account")

        repo_u.delete(member_id)
        await self.event.sudo(ctx, f"User **{member_id}** removed.")

    @user.command(name="edit", aliases=["set"])
    async def user_edit(self, ctx, member_id: int, key: str, value: str):
        """Edit user"""
        if ctx.author.id != config["admin id"] and repo_u.get_attribute(member_id, "mod") == 1:
            return await ctx.send("> You do not have permission to alter mod accounts")
        if ctx.author.id != config["admin id"] and member_id == config["admin id"]:
            return await ctx.send("> You do not have permission to alter admin account")

        if key in ("mod", "readonly", "restricted"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")
        elif key.startswith("home_id:"):
            try:
                value = int(value)
            except ValueError:
                raise errors.BadArgument("Value has to be integer.")

        repo_u.set(discord_id=member_id, key=key, value=value)
        await self.event.sudo(ctx, f"{member_id} updated: {key} = {value}.")

    @user.command(name="list")
    async def user_list(self, ctx, restraint: str = None):
        """List all registered users

        restraint: beam name, wormhole ID or user attribute
        """
        if restraint is None:
            db_users = repo_u.list_objects()
        elif repo_b.exists(restraint):
            db_users = repo_u.list_objects_by_beam(restraint)
        elif restraint in ("restricted", "readonly", "mod"):
            db_users = repo_u.list_objects_by_attribute(restraint)
        elif is_id(restraint) and repo_w.exists(int(restraint)):
            db_users = repo_u.list_objects_by_wormhole(int(restraint))
        else:
            raise errors.BadArgument("Value is not beam name nor wormhole ID.")

        template = "\n{nickname} ({name}, {id}):"
        template_home = "- {beam}: {home} ({name}, {guild})"

        # sort
        db_users.sort(key=lambda x: x.nickname)

        result = []
        for db_user in db_users:
            # get user
            user = self.bot.get_user(db_user.discord_id)
            user_name = str(user) if hasattr(user, "name") else "---"
            result.append(
                template.format(id=db_user.discord_id, name=user_name, nickname=db_user.nickname)
            )
            for beam, discord_id in db_user.home_ids.items():
                if restraint and restraint != beam and restraint != str(discord_id):
                    continue
                channel = self.bot.get_channel(discord_id)
                result.append(
                    template_home.format(
                        beam=beam,
                        home=discord_id,
                        name=channel.name if hasattr(channel, "name") else "---",
                        guild=channel.guild.name if hasattr(channel.guild, "name") else "---",
                    )
                )
            # attributes
            attrs = []
            if db_user.mod:
                attrs.append("MOD")
            if db_user.readonly:
                attrs.append("READ ONLY")
            if db_user.restricted:
                attrs.append("RESTRICTED")
            if len(attrs):
                result.append("- " + ", ".join(attrs))

        async def send_output(output: str):
            if hasattr(ctx.channel, "id") and repo_w.exists(ctx.channel.id):
                await ctx.author.send("```" + output + "```")
            else:
                await ctx.send("```" + output + "```")

        # iterate over the result
        output = ""
        for line in result:
            if len(output) > 1600:
                await send_output(output)
                output = ""
            output += "\n" + line
        if len(result) == 0:
            output = "No users."
        await send_output(output)

    def _get_channel(self, *, ctx: commands.Context, channel_id: int = None) -> discord.TextChannel:
        if channel_id:
            return self.bot.get_channel(channel_id)
        if isinstance(ctx.channel, discord.TextChannel):
            return ctx.channel

        raise errors.BadArgument("Missing channel ID.")

    def _get_member(self, *, member_id: int) -> discord.User:
        return self.bot.get_user(member_id)

    def _w2str_out(self, channel: discord.TextChannel) -> str:
        return f"**#{channel.name}** in **{channel.guild.name}**"

    def _w2str_log(self, channel: discord.TextChannel) -> str:
        return f"{channel.guild.name}/{channel.name} (ID {channel.id})"


def setup(bot):
    bot.add_cog(Admin(bot))
