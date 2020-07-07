import discord
from discord.ext import commands


class Gather(commands.Cog):
    """Gather information"""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(name="spy")
    async def spy(self, ctx):
        return

    @spy.command(name="guilds")
    async def spy_guilds(self, ctx):
        """Get all information"""
        result = []
        for guild in self.bot.guilds:
            result.append(f"**{guild.name}** ({guild.id})")
            result.append(f"Created {guild.created_at}, {guild.member_count} members")
            result.append(f"Owner **{guild.owner.name}** ({guild.owner.id})")
            bot_user = guild.get_member(self.bot.user.id)
            roles = [f"`{x.name}`" for x in bot_user.roles]
            result.append(f"My roles: {', '.join(roles)}")
            result.append("")
        await ctx.send("\n".join(result))

    @spy.command(name="channels")
    async def spy_channels(self, ctx):
        """Print channels"""
        result = []
        for guild in self.bot.guilds:
            result.append(f"{guild.name} ({guild.id})")
            for category, channels in guild.by_category():
                if hasattr(category, "id"):
                    result.append(f"CATEGORY {category.id} {category.name}")
                else:
                    result.append(f"CATEGORY")
                for channel in channels:
                    result.append(f"{channel.id} {channel.name}")
            result.append("")

        output = "\n".join(result)
        output = list(output[0 + i : 1990 + i] for i in range(0, len(output), 1990))
        for o in output:
            await ctx.send(f"```{o}```")

    @spy.command(name="roles")
    async def spy_roles(self, ctx):
        """Print roles and their permissions"""
        result = []
        s = "`{id}` `{perms:<10}` {name}"
        for guild in self.bot.guilds:
            result.append(f">> {guild.name} ({guild.id})")
            for role in guild.roles[::-1]:
                # fmt: off
                result.append(s.format(
                    id=role.id,
                    perms=role.permissions.value,
                    name=role.name
                ))
                # fmt: on
            result.append("")
        output = "\n".join(result)
        output = list(output[0 + i : 1990 + i] for i in range(0, len(output), 1990))
        for o in output:
            await ctx.send(f"```{o}```")

    @spy.command(name="emotes")
    async def spy_emotes(self, ctx):
        """Get all available emotes"""
        return await ctx.send("TODO")

        result = []
        for guild in self.bot.guilds:
            result.append(f"**{guild.name}** ({guild.id})")
            result.append(" ".join(str(x) for x in guild.emojis))
            result.append("")
        await ctx.send("\n".join(result))

    @spy.command(name="invites")
    async def spy_invites(self, ctx):
        """Get invites for all guilds"""
        result = []
        for guild in self.bot.guilds:
            result.append(f"**{guild.name}** ({guild.id})")
            # look for invites
            try:
                for invite in await guild.invites():
                    result.append(invite.url)
            except:
                # try to generate one
                try:
                    channel = guild.text_channels[0]
                    invite = await channel.create_invite()
                    result.append(invite.url)
                except:
                    # no luck
                    result.append("No permission")

        await ctx.send("\n".join(result))


def setup(bot):
    bot.add_cog(Gather(bot))
