import json

import discord
from discord.ext import commands

from core import wormcog

config = json.load(open("config.json"))


class Notifications(wormcog.Wormcog):
    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # fmt: off
        embed = self.get_embed(
            title="New guild: " + guild.name,
            description=f"ID {guild.id}\nCreated: {guild.created_at}",
        )
        embed.set_thumbnail(url=guild.icon_url_as(size=1024))

        embed.add_field(
            name="Owner",
            value=f"{guild.owner.mention}\n{guild.owner.name} (id {guild.owner.id})",
            inline=False,
        )

        embed.add_field(
            name="Members",
            value=f"Total {guild.member_count}, {len(guild.premium_subscribers)} boosters",
        )
        embed.add_field(
            name="Nitro level",
            value=str(guild.premium_tier)
        )

        wormhole = discord.utils.get(guild.channels, name="wormhole")
        if wormhole is not None:
            embed.add_field(
                name="Wormhole channel",
                value=f"{wormhole.mention}\nID {wormhole.id}")
        else:
            embed.add_field(
                name="No wormhole channel found",
                value=f"{len(guild.channels)} channels in total"
            )

        log_channel = self.bot.get_channel(config.get("log channel"))
        await log_channel.send(embed=embed)
        # fmt: on


def setup(bot):
    bot.add_cog(Notifications(bot))
