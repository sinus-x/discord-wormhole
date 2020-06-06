import json

import discord
from discord.ext import commands

from core import errors, wormcog
from core.database import repo_u, repo_w

config = json.load(open("config.json"))


class User(wormcog.Wormcog):
    """Let users manage their database account"""

    def __init__(self, bot):
        super().__init__(bot)
        self.p = config["prefix"]

    def getUserObject(self, ctx):
        u = repo_u.get(ctx.author.id)
        if u is None:
            raise errors.NotRegistered()
        return u

    def getHomeString(self, channel: discord.TextChannel):
        return (
            f"{channel.mention} on server **{discord.utils.escape_markdown(channel.guild.name)}**"
        )

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @commands.command()
    async def register(self, ctx):
        """Add yourself to the database"""
        u = repo_u.get(ctx.author.id)
        if u is not None:
            raise errors.WormholeException("You are already registered")

        name = discord.utils.escape_markdown(ctx.author.name).replace("]", "").replace("[", "")

        # get first available nickname
        u = repo_u.getByNickname(name)
        i = 0
        while u is not None:
            u = repo_u.getByNickname(f"{name}{i}")
            i += 1
        if i > 0:
            name = f"{name}{i}"

        # register
        try:
            home = ctx.channel.id if isinstance(ctx.channel, discord.TextChannel) else None
            home = home if repo_w.get(home) is not None else None
            repo_u.add(ctx.author.id, nickname=ctx.author.name, home=home)
            await ctx.author.send(
                "You are now registered. "
                f"You can display your information with `{self.p}me`.\n"
                f"To see information about another user, enter `{self.p}whois [nickname]`.\n\n"
                f"You can tag others with `((nickname))`, if they have set their home guild."
            )
        except errors.DatabaseException as e:
            await ctx.author.send("There was an error: " + str(e))

    @commands.group(name="set")
    async def set(self, ctx):
        """Edit your information"""
        if ctx.invoked_subcommand is not None:
            return

        description = (
            f"**NOTE**: _You have to register first with_ `{self.p}register`"
            if repo_u.get(ctx.author.id) is None
            else ""
        )
        # fmt: off
        embed = discord.Embed(
            title="Wormhole: **set**",
            description=description,
            color=discord.Color.light_grey()
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
        await ctx.send(embed=embed, delete_after=self.removalDelay())
        await self.delete(ctx.message)

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @set.command(name="home")
    async def set_home(self, ctx):
        """Set current channel as your home wormhole"""
        if self.getUserObject(ctx) is None:
            return await ctx.author.send(f"You have to register first with `{self.p}register`")
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.author.send("Home has to be a text channel")
        if repo_w.get(ctx.channel.id) is None:
            return await ctx.author.send("Home has to be a wormhole")

        repo_u.set(ctx.author.id, home=ctx.channel.id)
        await ctx.author.send("Your home wormhole is " + self.getHomeString(ctx.channel))

    @commands.cooldown(rate=2, per=3600, type=commands.BucketType.user)
    @set.command(name="name", aliases=["nick", "nickname"])
    async def set_name(self, ctx, *, name: str):
        """Set new display name"""
        name = discord.utils.escape_markdown(name)
        u = repo_u.getByNickname(name)
        if u is not None:
            return await ctx.author.send("This name is already used by someone")
        if "(" in name or ")" in name:
            return await ctx.author.send("The name cannot contain `(` or `)`")

        repo_u.set(ctx.author.id, nickname=name)
        await ctx.author.send(f"Your nickname was changed to **{name}**")

    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
    @commands.command()
    async def me(self, ctx):
        """See your information"""
        me = self.getUserObject(ctx)
        await self.displayUserInfo(ctx, me)

    @commands.cooldown(rate=3, per=30, type=commands.BucketType.user)
    @commands.command()
    async def whois(self, ctx, member: str):
        """Get information about member"""
        u = repo_u.getByNickname(member)
        if u is not None:
            return await self.displayUserInfo(ctx, u)
        await ctx.author.send("User not found")

    async def displayUserInfo(self, ctx, user: object):
        """Display user info"""
        u = self.bot.get_user(user.id)
        msg = [
            f"User **{discord.utils.escape_markdown(u.name)}**",
            f"_Taggable via_ `(({user.nickname}))`",
            "Information: ",
        ]

        par = []
        if user.mod is not None:
            par.append("**MOD**")
        if user.readonly is True:
            par.append("silenced")
        if user.home is None:
            msg[1] += "_, once they have set their home wormhole_"
        else:
            home = self.bot.get_channel(user.home)
            par.append("their home wormhole is " + self.getHomeString(home))
        msg[2] += ", ".join(par)

        await ctx.author.send("\n".join(msg))


def setup(bot):
    bot.add_cog(User(bot))
