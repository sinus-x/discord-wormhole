import discord
from discord.ext import commands

from core import checks, errors, wormcog
from core.database import repo_u, repo_w


class user(wormcog.Wormcog):
    """Let users manage their database account"""

    def __init__(self, bot):
        super().__init__(bot)

    def getUserObject(self, ctx):
        u = repo_u.get(ctx.author.id)
        if u == None:
            raise errors.NotRegistered()
        return u

    def getHomeString(self, channel: discord.TextChannel):
        return (
            f"{channel.mention} on server **{discord.utils.escape_markdown(channel.guild.name)}**"
        )

    @commands.command()
    async def register(self, ctx):
        """Add yourself to the database"""
        await self.delete(ctx)

        u = repo_u.get(ctx.author.id)
        if u != None:
            raise errors.WormholeException("User already registered")

        name = discord.utils.escape_markdown(ctx.author.name)
        # get first available nickname
        u = repo_u.getByNickname(name)
        i = 0
        while u != None:
            u = repo_u.getByNickname(f"{name}{i}")
            i += 1
        if i > 0:
            name = f"{name}{i}"

        # register
        try:
            home = ctx.channel.id if isinstance(ctx.channel, discord.TextChannel) else None
            home = home if repo_w.get(home) != None else None
            repo_u.add(ctx.author.id, nickname=ctx.author.name, home=home)
            await ctx.author.send("You are now registered.")
        except errors.DatabaseException as e:
            await ctx.author.send("There was an error: " + str(e))

    @commands.command()
    async def me(self, ctx):
        """See your information"""
        await self.delete(ctx)

        me = self.getUserObject(ctx)
        await self._displayUserInfo(ctx, me)

    @commands.group(name="set")
    async def set(self, ctx):
        """Edit your information"""
        await self.delete(ctx)

        if ctx.invoked_subcommand != None:
            return

        # TODO Display help here

    @set.command(name="home")
    async def set_home(self, ctx):
        """Set current channel as your home wormhole"""
        me = self.getUserObject(ctx)
        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.author.send("Home has to be a text channel")
        if repo_w.get(ctx.channel.id) == None:
            return await ctx.author.send("Home has to be a wormhole")
        repo_u.set(ctx.author.id, home=ctx.channel.id)
        await ctx.author.send(f"Your home wormhole is " + self.getHomeString(ctx.channel))

    @set.command(name="name", aliases=["nick", "nickname"])
    async def set_name(self, ctx, *, name: str):
        """Set new display name"""
        name = discord.utils.escape_markdown(name)
        u = repo_u.getByNickname(name)
        if u != None:
            return await ctx.author.send("This name is already used by someone")
        repo_u.set(ctx.author.id, nickname=name)
        await ctx.author.send(f"Your nickname was changed to **{name}**")

    @commands.command(aliases=["whois"])
    async def stalk(self, ctx, member: str):
        """Get information about member"""
        await self.delete(ctx)

        u = repo_u.getByNickname(member)
        if u != None:
            return await self._displayUserInfo(ctx, u)
        await ctx.author.send("User not found")

    async def _displayUserInfo(self, ctx, user: object):
        """Display user info"""
        s = (
            f"User **{user.nickname}**:\n"
            f"_You can tag this person via _`[[{user.nickname}]]`\n"
            f"Information: "
        )
        par = []
        if user.mod != None:
            par.append("**MOD**")
        if user.readonly == True:
            par.append("silenced")
        if user.home != None:
            home = self.bot.get_channel(user.home)
            par.append("their home wormhole is " + self.getHomeString(home))
        s += ", ".join(par)

        await ctx.author.send(s)


def setup(bot):
    bot.add_cog(user(bot))
