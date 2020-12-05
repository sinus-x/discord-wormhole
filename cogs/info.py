import json
import tempfile

import discord
from discord.ext import commands

from core import wormcog


class Info(wormcog.Wormcog):
    """Gather information"""

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.group(name="spy")
    async def spy(self, ctx):
        await self.delete(ctx)

        if ctx.invoked_subcommand is not None:
            return

        embed = self.get_embed(
            ctx=ctx,
            title="Get information",
            description="Get to know your guilds better.",
        )
        # fmt: off
        embed.add_field(
            name="spy guilds [guild ID]",
            value="Basic guild information",
            inline=False,
        )
        embed.add_field(
            name="spy channels [guild ID]",
            value="List channels",
            inline=False,
        )
        embed.add_field(
            name="spy roles [guild ID]",
            value="List roles",
            inline=False,
        )
        embed.add_field(
            name="spy guild [guild ID]",
            value="Aggregate information",
            inline=False,
        )
        # fmt: on
        await ctx.send(embed=embed, delete_after=self.delay("admin"))

    @spy.command(name="guilds")
    async def spy_guilds(self, ctx, guild_id: int = None):
        """Get all information"""
        if guild_id is None:
            guilds = self.bot.guilds
        else:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return await ctx.send("Guild not found.")
            guilds = [guild]

        template = """> __**[{ctr}/{total}]**__ **{gname}** ({gid})
                      > Owner **{oname}** ({oid}). **{count} members** ({nitro} nitro).
                      > Created {created}, level {tier}, {boost} boosts.
                      > Bot roles: {roles}"""
        result = ""
        for i, guild in enumerate(guilds):
            info = template.format(
                ctr=i + 1,
                total=len(guilds),
                gname=guild.name,
                gid=guild.id,
                created=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                count=guild.member_count,
                nitro=len(guild.premium_subscribers),
                oname=guild.owner.name,
                oid=guild.owner.id,
                tier=guild.premium_tier,
                boost=guild.premium_subscription_count,
                roles=", ".join([f"`{x.name}`" for x in guild.me.roles]),
            )
            if len(result) + len(info) > 2000:
                await ctx.send(result)
                result = ""
            result += "\n\n" + info
        await ctx.send(result)

    @spy.command(name="channels")
    async def spy_channels(self, ctx, guild_id: int = None):
        """Print channels"""
        if guild_id is None:
            guilds = self.bot.guilds
        else:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return await ctx.send("Guild not found.")
            guilds = [guild]

        template_h1 = "> __**[{ctr}/{total}]**__ GUILD **{gname}** ({gid})"
        template_h2 = "> **{cname}** ({cid})"
        template_p = "> `{chid}` `{perms:>10}` **{chname}**"

        for i, guild in enumerate(guilds):
            member = guild.get_member(self.bot.user.id)
            result = [
                template_h1.format(ctr=i + 1, total=len(guilds), gname=guild.name, gid=guild.id)
            ]
            for category, channels in guild.by_category():
                if hasattr(category, "id"):
                    result.append(template_h2.format(cname=category.name, cid=category.id))
                else:
                    result.append("> **No category**")
                for channel in channels:
                    result.append(
                        template_p.format(
                            chid=channel.id,
                            perms=channel.permissions_for(member).value,
                            chname=channel.name,
                        )
                    )
            text = ""
            for line in result:
                if len(text) + len(line) > 2000:
                    await ctx.send(text)
                    text = ""
                text += "\n" + line
            await ctx.send(text)

    @spy.command(name="roles")
    async def spy_roles(self, ctx, guild_id: int = None):
        """Print roles and their permissions"""
        if guild_id is None:
            guilds = self.bot.guilds
        else:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return await ctx.send("Guild not found.")
            guilds = [guild]

        template_h = "> __**[{ctr}/{total}]**__ GUILD **{gname}** ({gid})"
        template_p = "> `{rid}` `{perms:>10}` **{rname}**"

        for i, guild in enumerate(guilds):
            result = [
                template_h.format(ctr=i + 1, total=len(guilds), gname=guild.name, gid=guild.id)
            ]
            for role in guild.roles[::-1]:
                result.append(
                    template_p.format(
                        rid=role.id,
                        perms=role.permissions.value,
                        rname=role.name.replace("@", "@\u200b"),
                    )
                )
            text = ""
            for line in result:
                if len(text) + len(line) > 2000:
                    await ctx.send(text)
                    text = ""
                text += "\n" + line
            await ctx.send(text)

    @spy.command(name="emotes")
    async def spy_emotes(self, ctx, guild_id: int = None):
        """Get all available emotes"""
        return await ctx.send("Emotes not implemented.")

        result = []
        for guild in self.bot.guilds:
            result.append(f"**{guild.name}** ({guild.id})")
            result.append(" ".join(str(x) for x in guild.emojis))
            result.append("")
        await ctx.send("\n".join(result))

    @spy.command(name="guild")
    async def spy_guild(self, ctx, guild_id: int):
        """Get information about guild"""
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.send("Guild not found.")

        await self.spy_guilds(ctx, guild_id)
        await self.spy_channels(ctx, guild_id)
        await self.spy_roles(ctx, guild_id)
        await self.spy_emotes(ctx, guild_id)

    @spy.command(name="messages")
    async def spy_messages(self, ctx, channel_id: int, count: int = 100):
        """Download messages from given channel. May fail if permissions are missing."""
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return await ctx.send("Channel not found.")

        messages = []
        try:
            async for message in channel.history(limit=count, oldest_first=False):
                message_dict = {
                    "id": message.id,
                    "author": message.author.id,
                    "content": message.content,
                }
                if len(message.attachments):
                    attmnts = []
                    for attachment in message.attachments:
                        try:
                            attmnts.append(attachment.url)
                        except:
                            pass
                    if len(attmnts):
                        message_dict["attachments"] = attmnts

                messages.append(message_dict)
        except Exception as e:
            return await ctx.send(str(e))

        # Convert to json
        with tempfile.TemporaryFile() as fp:
            fp.write(bytes(json.dumps(messages), "utf-8"))
            fp.seek(0)
            await ctx.send(file=discord.File(fp=fp, filename="dump.json"))

        return


def setup(bot):
    bot.add_cog(Info(bot))
