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

    def getUserObject(self, ctx):
        u = repo_u.get(ctx.author.id)
        if u is None:
            raise errors.NotRegistered()
        return u

    def getHomeString(self, channel: discord.TextChannel):
        return f"{channel.mention} in **{self.sanitise(channel.guild.name)}**"

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @commands.command()
    async def register(self, ctx):
        """Add yourself to the database"""
        db_u = repo_u.get(ctx.author.id)
        if db_u is not None:
            raise errors.WormholeException("You are already registered")

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

        repo_u.add(ctx.author.id, nickname=nickname, home_id=home_id)
        await ctx.author.send(
            "You are now registered. "
            f"You can display your information with `{self.p}me`.\n"
            f"To see information about another user, enter `{self.p}whois [nickname]`.\n\n"
            f"You can tag others with `((nickname))`, if they have set their home guild."
        )

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
        await ctx.send(embed=embed, delete_after=self.delay())
        await self.delete(ctx.message)

    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @set.command(name="home")
    async def set_home(self, ctx):
        """Set current channel as your home wormhole"""
        if self.getUserObject(ctx) is None:
            return await ctx.author.send(
                f"{ctx.author.mention}, you have to register first with `{self.p}register`",
                delete_after=5,
            )
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.author.send(
                f"{ctx.author.mention}, home has to be a text channel", delete_after=5
            )
        if repo_w.get(ctx.channel.id) is None:
            return await ctx.author.send(
                f"{ctx.author.mention}, home has to be a wormhole", delete_after=5
            )

        repo_u.set(ctx.author.id, home_id=ctx.channel.id)
        await ctx.author.send("Your home wormhole is " + self.getHomeString(ctx.channel))

    @commands.cooldown(rate=2, per=3600, type=commands.BucketType.user)
    @set.command(name="name", aliases=["nick", "nickname"])
    async def set_name(self, ctx, *, name: str):
        """Set new display name"""
        name = discord.utils.escape_markdown(name)
        u = repo_u.getByNickname(name)
        if u:
            return await ctx.author.send("This name is already used by someone")
        if "(" in name or ")" in name or "@" in name:
            return await ctx.author.send("The name cannot contain characters `()@`")

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
        if u:
            return await self.displayUserInfo(ctx, u)
        await ctx.author.send("User not found")

    async def displayUserInfo(self, ctx, user: objects.User):
        """Display user info"""
        u = self.bot.get_user(user.id)
        msg = [
            f"User **{self.sanitise(u.nickname)}**",
            f"_Taggable via_ `(({user.nickname}))`",
            "Information: ",
        ]

        par = []
        if user.mod:
            par.append("**MOD**")
        if user.readonly:
            par.append("silenced")
        if user.home:
            home = self.bot.get_channel(user.home)
            par.append("their home wormhole is " + self.getHomeString(home))
        else:
            msg[1] += "_, once they have set their home wormhole_"
        msg[2] += ", ".join(par)

        await ctx.author.send("\n".join(msg))


def setup(bot):
    bot.add_cog(User(bot))
