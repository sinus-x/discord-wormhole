import json

import discord
from discord.ext import commands

from core import checks, objects, wormcog
from core.database import repo_u, repo_w

config = json.load(open("config.json"))


class User(wormcog.Wormcog):
    """Let users manage their database account"""

    def __init__(self, bot):
        super().__init__(bot)
        self.p = config["prefix"]

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @commands.check(checks.in_wormhole)
    @commands.command()
    async def register(self, ctx):
        """Add yourself to the database"""
        if repo_u.exists(ctx.author.id):
            return await ctx.author.send("You are already registered.")

        nickname = self.sanitise(ctx.author.name, limit=32).replace(")", "").replace("(", "")
        nickname = self.get_free_nickname(nickname)

        # register
        repo_u.add(discord_id=ctx.author.id, nickname=nickname)
        if isinstance(ctx.channel, discord.TextChannel) and repo_w.get(ctx.channel.id):
            beam_name = repo_w.get(ctx.channel.id).beam
            repo_u.set(ctx.author.id, key=f"home_id:{beam_name}", value=ctx.channel.id)

        await self.event.user(ctx, f"Registered as **{nickname}**.")
        await ctx.author.send(
            f"You are now registered as `{nickname}`. "
            f"You can display your information with `{self.p}me`.\n"
            f"To see information about another user, enter `{self.p}whois nickname`.\n\n"
            f"You can tag other registered users with `((nickname))`."
        )

    @commands.group(name="set")
    async def set(self, ctx):
        """Edit your information"""
        await self.delete(ctx.message)

        if ctx.invoked_subcommand is not None:
            return

        description = (
            f"**NOTE**: _You have to register first with_ `{self.p}register`"
            if repo_u.get(ctx.author.id) is None
            else ""
        )
        # fmt: off
        embed = self.get_embed(
            title="Wormhole: **set**",
            description=description,
        )
        embed.add_field(
            name="Set home wormhole",
            value=f"**{self.p}set home**",
            inline=False,
        )
        embed.add_field(
            name="Set new nickname",
            value=f"**{self.p}set name [new name]**",
            inline=False
        )
        # fmt: on
        await ctx.send(embed=embed, delete_after=self.delay())

    @commands.cooldown(rate=1, per=14400, type=commands.BucketType.user)
    @commands.check(checks.in_wormhole)
    @set.command(name="home")
    async def set_home(self, ctx):
        """Set current channel as your home wormhole"""
        if not repo_u.exists(ctx.author.id):
            return await ctx.author.send(f"Register with `{self.p}register`")
        if repo_u.get_attribute(ctx.author.id, "restricted") == 1:
            return await ctx.author.send("You are forbidden to alter your settings.")
        if not isinstance(ctx.channel, discord.TextChannel) or not repo_w.exists(ctx.channel.id):
            return await ctx.author.send("Home has to be a wormhole")

        beam_name = repo_w.get(ctx.channel.id).beam
        repo_u.set(ctx.author.id, key=f"home_id:{beam_name}", value=ctx.channel.id)
        await ctx.author.send("Home set to " + ctx.channel.mention)
        await self.event.user(
            ctx,
            f"Home in **{beam_name}** set to **{ctx.channel.id}** ({ctx.guild.name}).",
        )

    @commands.cooldown(rate=2, per=14400, type=commands.BucketType.user)
    @set.command(name="name", aliases=["nick", "nickname"])
    async def set_name(self, ctx, *, name: str):
        """Set new display name"""
        if not repo_u.exists(ctx.author.id):
            return await ctx.author.send(f"Register with `{self.p}register`")
        if repo_u.get_attribute(ctx.author.id, "restricted") == 1:
            return await ctx.author.send("You are forbidden to alter your settings.")
        name = self.sanitise(name, limit=32)
        u = repo_u.get_by_nickname(name)
        if u is not None:
            return await ctx.author.send("This name is already used by someone.")
        # fmt: off
        disallowed = (
            "(", ")", "*", "/", "@", "\\", "_", "`",
            "\u200B", "\u200C", "\u200D", "\u2028", "\u2060", "\uFEFF",
            # guild emojis
            "<:", "<a:",
        )
        # fmt: on
        for char in disallowed:
            if char in name:
                return await ctx.author.send("The name contains forbidden characters.")

        before = repo_u.get_attribute(ctx.author.id, "nickname")
        repo_u.set(ctx.author.id, key="nickname", value=name)
        await ctx.author.send(f"Your nickname was changed to **{name}**")
        await self.event.user(ctx, f"Nickname changed from **{before}** to **{name}**.")

    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    @commands.command()
    async def me(self, ctx):
        """See your information"""
        await self.delete(ctx.message)
        db_u = repo_u.get(ctx.author.id)
        if db_u is None:
            return await ctx.author.send("You are not registered.")
        await self.display_user_info(ctx, db_u)

    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    @commands.command()
    async def whois(self, ctx, *, member: str):
        """Get information about member"""
        await self.delete(ctx.message)

        u = repo_u.get_by_nickname(member)
        if u is not None:
            await self.event.user(ctx, f"Whois lookup for **{member}**.")
            return await self.display_user_info(ctx, u)
        await self.event.user(ctx, f"Invalid whois lookup for **{member}**.")
        await ctx.author.send("User not found")

    async def display_user_info(self, ctx, db_u: objects.User):
        """Display user info"""

        """
        title:  name#0000
        descr:  @name (ID 000000000000000)
                _Taggable via `((nickname))`_ | _, once they've set their home wormhole_

        field:  Home wormhole
                **main**: wormhole, GUILD NAME
                **devel**: wormhole, TEST GUILD NAME
        """

        user = self.bot.get_user(db_u.discord_id)
        if db_u is None:
            return await ctx.author.send("User not in database.")
        if user is None:
            return await ctx.author.send("User not found.")

        description = f"{user.mention} (ID {user.id})\n_Taggable via_ `(({db_u.nickname}))`"
        if len(db_u.home_ids) == 0:
            description += "_, once they've set their home wormhole_"
        embed = self.get_embed(ctx=ctx, title=str(user), description=description)

        information = []
        if db_u.mod:
            information.append("mod")
        if db_u.readonly:
            information.append("read only")
        if db_u.restricted:
            information.append("restricted")
        if len(information):
            embed.add_field(name="Information", value=", ".join(information), inline=False)

        if len(db_u.home_ids):
            value = []
            for beam, discord_id in db_u.home_ids.items():
                channel = self.bot.get_channel(discord_id)
                value.append("**{}**: {}, {}".format(beam, channel.name, channel.guild.name))
            embed.add_field(name="Home wormhole", value="\n".join(value), inline=False)

        await ctx.author.send(embed=embed)

    @commands.command()
    @commands.check(checks.in_wormhole_or_dm)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.channel)
    async def invites(self, ctx):
        """Get invite links"""
        await self.delete(ctx)

        result = []
        template = "{logo} **{guild}**, {name}: {link}"
        for wormhole in repo_w.list_objects(repo_w.get_attribute(ctx.channel.id, "beam")):
            if wormhole.invite is None:
                continue
            channel = self.bot.get_channel(wormhole.discord_id)
            if channel is None:
                continue
            result.append(
                template.format(
                    logo=wormhole.logo if len(wormhole.logo) else "",
                    name=channel.name,
                    guild=channel.guild.name,
                    link=wormhole.invite,
                )
            )
        result = "\n".join(result) if len(result) else "No public invites."
        await self.smart_send(ctx, content=result)


def setup(bot):
    bot.add_cog(User(bot))
