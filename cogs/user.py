import json

import discord
from discord.ext import commands

from core import errors, objects, wormcog
from core.database import repo_u, repo_w

config = json.load(open("config.json"))


class User(wormcog.Wormcog):
    """Let users manage their database account"""

    def __init__(self, bot):
        super().__init__(bot)
        self.p = config["prefix"]

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @commands.command()
    async def register(self, ctx):
        """Add yourself to the database"""
        if repo_u.exists(ctx.author.id):
            return await ctx.author.send("You are already registered.")

        nickname = self.sanitise(ctx.author.name, limit=12).replace(")", "").replace("(", "")

        # get first available nickname
        i = 0
        name_orig = nickname
        while repo_u.nicknameIsUsed(nickname):
            nickname = f"{name_orig}{i}"
            i += 1

        # register
        if isinstance(ctx.channel, discord.TextChannel) and repo_w.get(ctx.channel.id):
            home_id = ctx.channel.id
        else:
            home_id = 0

        repo_u.add(discord_id=ctx.author.id, nickname=nickname, home_id=home_id)
        await ctx.author.send(
            f"You are now registered as `{nickname}`. "
            f"You can display your information with `{self.p}me`.\n"
            f"To see information about another user, enter `{self.p}whois [nickname]`.\n\n"
            f"You can tag others with `((nickname))`, if they have set their home guild."
        )
        await self.event.user(ctx, f"User registered: **{str(ctx.author)}** as **{nickname}**.")

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
        embed = self.getEmbed(
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

    @commands.cooldown(rate=1, per=1, type=commands.BucketType.user)
    @set.command(name="home")
    async def set_home(self, ctx):
        """Set current channel as your home wormhole"""
        if not repo_u.exists(ctx.author.id):
            return await ctx.author.send(f"Register with `{self.p}register`", delete_after=5)
        if repo_u.getAttribute(ctx.author.id, "restricted") == 1:
            return await ctx.author.send(f"You are forbidden to alter your settings.")
        if not isinstance(ctx.channel, discord.TextChannel) or not repo_w.exists(ctx.channel.id):
            return await ctx.author.send(f"Home has to be a wormhole", delete_after=5)

        repo_u.set(ctx.author.id, key="home_id", value=ctx.channel.id)
        await ctx.author.send("Home set to " + ctx.channel.mention)
        await self.event.user(ctx, f"Home set to **{ctx.channel.id}** ({ctx.guild.name}).")

    @commands.cooldown(rate=2, per=1, type=commands.BucketType.user)
    @set.command(name="name", aliases=["nick", "nickname"])
    async def set_name(self, ctx, *, name: str):
        """Set new display name"""
        if not repo_u.exists(ctx.author.id):
            return await ctx.author.send(f"Register with `{self.p}register`", delete_after=5)
        if repo_u.getAttribute(ctx.author.id, "restricted") == 1:
            return await ctx.author.send(f"You are forbidden to alter your settings.")
        name = self.sanitise(name, limit=32)
        u = repo_u.getByNickname(name)
        if u is not None:
            return await ctx.author.send("This name is already used by someone.")
        disallowed = (
            "(",
            ")",
            "`",
            "@",
            "\u200B",
            "\u200C",
            "\u200D",
            "\u2028",
            "\u2060",
            "\uFEFF",
        )
        for char in disallowed:
            if char in name:
                return await ctx.author.send("The name contains forbidden characters.")

        before = repo_u.getAttribute(ctx.author.id, "nickname")
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
        await self.displayUserInfo(ctx, db_u)

    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    @commands.command()
    async def whois(self, ctx, member: str):
        """Get information about member"""
        await self.delete(ctx.message)
        await self.event.user(ctx, f"Whois lookup for **{member}**.")

        u = repo_u.getByNickname(member)
        if u:
            return await self.displayUserInfo(ctx, u)
        await ctx.author.send("User not found")

    async def displayUserInfo(self, ctx, db_u: objects.User):
        """Display user info"""
        user = self.bot.get_user(db_u.discord_id)
        if db_u is None:
            return await ctx.author.send("User not in database.")
        if user is None:
            return await ctx.author.send("User not found.")

        description = f"{user.mention} (ID {user.id})\n_Taggable via_ `(({db_u.nickname}))`"
        if db_u.home_id == 0:
            description += "_, once they've set their home wormhole_"
        embed = self.getEmbed(ctx=ctx, title=db_u.nickname, description=description)

        information = []
        if db_u.mod:
            information.append("mod")
        if db_u.readonly:
            information.append("read only")
        if db_u.restricted:
            information.append("restricted")
        if len(information):
            embed.add_field(name="Information", value=", ".join(information))

        if db_u.home_id:
            channel = self.bot.get_channel(db_u.home_id)
            value = "{}, {}".format(channel.name, channel.guild.name)
            embed.add_field(name="Home wormhole", value=value)

        await ctx.author.send(embed=embed)


def setup(bot):
    bot.add_cog(User(bot))
