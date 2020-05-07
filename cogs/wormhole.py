import re
import json
import asyncio
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands

import init
from core import wormcog
from core.database import repo_b, repo_u, repo_w

started = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

config = json.load(open("config.json"))


class Wormhole(wormcog.Wormcog):
    """Transfer messages between guilds"""

    def __init__(self, bot):
        super().__init__(bot)

        self.transferred = 0
        """Global message counter"""
        self.stats = {}
        """Per-channel message couter"""
        # TODO Load stats from database

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # do not act if channel is not wormhole channel
        if message.channel.id not in [w.channel for w in repo_w.getAll()]:
            return

        # do not act if author is bot
        if message.author.bot:
            return

        # do not act if message is bot command
        if message.content.startswith(config["prefix"]):
            return

        # get current beam
        beam = self.getBeamName(message)

        # get wormhole channel objects
        if not beam in self.wormholes or len(self.wormholes[beam]) == 0:
            self.reconnect(beam)

        # process incoming message
        content = self.__process(message)

        # convert attachments to links
        if message.attachments:
            for f in message.attachments:
                content += "\n" + f.url

        if len(content) < 1:
            return

        # count the message
        self.transferred += 1
        if self.transferred % 50 == 0:
            self.__saveStats()
        try:
            self.stats[str(message.channel.id)] += 1
        except KeyError:
            self.stats[str(message.channel.id)] = 1

        # send the message
        await self.send(message, beam, content, files=message.attachments)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return

        # get forwarded messages
        forwarded = None
        for m in self.sent:
            if m[0].id == after.id:
                forwarded = m
                break
        if not forwarded:
            # TODO React with cross, wait, and delete
            return

        content = self.__process(after)
        for m in forwarded[1:]:
            await m.edit(content=content)
        # TODO React with check, wait, and delete

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # get forwarded messages
        forwarded = None
        for m in self.sent:
            if m[0].id == message.id:
                forwarded = m
                break
        if not forwarded:
            # TODO React with cross, wait, and delete
            return

        for m in forwarded[1:]:
            await m.delete()
        # TODO React with check, wait, and delete

    @commands.check(init.in_wormhole)
    @commands.command(aliases=["stat", "stats"])
    async def info(self, ctx: commands.Context):
        """Display information about wormholes"""

        if len(self.wormholes) == 0:
            self.reconnect()
            await asyncio.sleep(0.25)

        if len(self.wormholes) == 0:
            m = "> No wormhole has been opened."
        else:
            # get total message count
            total = 0
            for i in self.stats:
                total += self.stats[i]
            m = "> {} messages sent since the formation (**{}**); ping **{:.2f} s**.\n".format(
                self.transferred, started, self.bot.latency
            )

            m += "> Currently opened wormholes:"
            # FIXME What happens if the guild/channel does not exist?
            for w in self.wormholes:
                # get logo
                logo = repo_w.get(w.id).logo
                if not logo:
                    logo = ""

                # get names
                g = discord.utils.escape_markdown(w.guild.name)
                c = discord.utils.escape_markdown(w.name)

                # get message count
                try:
                    cnt = self.stats[str(w.id)]
                except KeyError:
                    cnt = 0

                # get message
                m += f"\n> {logo} **{g}** (#{c}): **{cnt}** messages"
        await ctx.send(m, delete_after=self.removalDelay())
        await self.delete(ctx.message)

    @commands.check(init.in_wormhole)
    @commands.command()
    async def help(self, ctx: commands.Context):
        """Display help"""
        embed = discord.Embed(title="Wormhole", color=discord.Color.light_grey())
        p = config["prefix"]
        embed.add_field(value=f"**{p}e** | **{p}edit**", name="Edit last message")
        embed.add_field(value=f"**{p}d** | **{p}delete**", name="Delete last message")
        embed.add_field(value=f"**{p}info**", name="Connection information")
        embed.add_field(value=f"**{p}settings**", name="Display current settings")
        embed.add_field(value=f"**{p}link**", name="Link to GitHub repository")
        embed.add_field(value=f"**{p}invite**", name="Bot invite link")
        await ctx.send(embed=embed, delete_after=self.removalDelay())
        await self.delete(ctx.message)

    @commands.check(init.in_wormhole)
    @commands.command(name="remove", aliases=["d", "delete", "r"])
    async def remove(self, ctx: commands.Context):
        """Delete last sent message"""
        if len(self.sent) == 0:
            return

        for msgs in self.sent[::-1]:
            if (
                isinstance(msgs[0], discord.Member)
                and ctx.author.id == msgs[0].id
                or isinstance(msgs[0], discord.Message)
                and ctx.author.id == msgs[0].author.id
            ):
                await self.delete(ctx.message)
                for m in msgs:
                    await self.delete(m)
                return

    @commands.check(init.in_wormhole)
    @commands.command(name="edit", aliases=["e"])
    async def edit(self, ctx: commands.Context, *, text: str):
        """Edit last sent message

		text: A new text
		"""
        if len(self.sent) == 0:
            return

        for msgs in self.sent[::-1]:
            if (
                isinstance(msgs[0], discord.Member)
                and ctx.author.id == msgs[0].id
                or isinstance(msgs[0], discord.Message)
                and ctx.author.id == msgs[0].author.id
            ):
                await self.delete(ctx.message)
                m = ctx.message
                m.content = m.content.split(" ", 1)[1]
                c = self.__process(m)
                for m in msgs:
                    try:
                        await m.edit(content=c)
                    except Exception as e:
                        print(e)
                        pass
                return

    @commands.check(init.in_wormhole)
    @commands.command()
    async def settings(self, ctx: commands.Context):
        return
        # TODO Update
        m = "> **Wormhole settings**: anonymity level **{}**, edit/delete timer **{}s**"
        await ctx.send(m.format(config["anonymity"], config["message window"]))
        await self.delete(ctx.message)

    @commands.check(init.in_wormhole)
    @commands.command()
    async def link(self, ctx: commands.Context):
        """Send a message with link to the bot"""
        await ctx.send("> **GitHub link:** https://github.com/sinus-x/discord-wormhole")
        await self.delete(ctx.message)

    @commands.check(init.in_wormhole)
    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Invite the wormhole to your guild"""
        # permissions:
        # - send messages      - attach files
        # - manage messages    - use external emojis
        # - embed links        - add reactions
        m = (
            "> **Invite link:** https://discordapp.com/oauth2/authorize?client_id="
            + str(self.bot.user.id)
            + "&permissions=321600&scope=bot"
        )
        await ctx.send(m)
        await self.delete(ctx.message)

    def __getPrefix(self, message: discord.Message, firstline: bool = True):
        """Get prefix for message"""
        dbw = repo_w.get(self.getBeamName(message))
        dbb = repo_b.get(dbw.beam)
        a = dbb.anonymity
        u = discord.utils.escape_markdown(message.author.name)
        g = str(message.guild.id)
        logo = g in config["aliases"] and config["aliases"][g] is not None
        if logo:
            if not firstline:
                g = config["prefix fill"]
            else:
                g = config["aliases"][g]
        else:
            g = discord.utils.escape_markdown(message.guild.name) + ","

        if a == "none":
            return f"{g} **{u}**: "

        if a == "guild" and logo:
            return f"**{g}** "
        if a == "guild":
            return f"**{g}**: "

        return ""

    def __process(self, message: discord.Message):
        """Escape mentions and apply anonymity"""
        content = message.content
        # FIXME This is not pretty at all

        users = re.findall(r"<@![0-9]+>", content)
        roles = re.findall(r"<@&[0-9]+>", content)
        chnls = re.findall(r"<#[0-9]+>", content)

        for u in users:
            try:
                user = str(self.bot.get_user(int(u.replace("<@!", "").replace(">", ""))))
            except:
                user = "unknown-user"
            content = content.replace(u, user)
        for r in roles:
            try:
                role = message.guild.get_role(int(r.replace("<@&", "").replace(">", ""))).name
            except:
                role = "unknown-role"
            content = content.replace(r, role)
        for c in chnls:
            try:
                ch = self.bot.get_channel(int(c.replace("<#", "").replace(">", "")))
                channel = "#[" + ch.guild.name + ":" + ch.name + "]"
            except:
                channel = "unknown-channel"
            content = content.replace(c, channel)

        # line preprocessor (code)
        content_ = content.split("\n")
        if "```" in content:
            content = []
            for line in content_:
                # do not allow code block starting on text line
                line.replace(" ```", "\n```")
                # do not alow text on code block end
                line.replace("``` ", "```\n")
                line = line.split("\n")
                for l in line:
                    content.append(l)
        else:
            content = content_

        # apply prefixes
        content_ = content.copy()
        content = ""
        p = self.__getPrefix(message)
        code = False
        for i in range(len(content_)):
            if i == 1:
                # use fill icon instead of guild one
                p = self.__getPrefix(message, firstline=False)
            line = content_[i]
            # add prefix if message starts with code block
            if i == 0 and line.startswith("```"):
                content += self.__getPrefix(message) + "\n"
            if line.startswith("```"):
                code = True
            if code:
                content += line + "\n"
            else:
                content += p + line + "\n"
            if line.endswith("```") and code and len(line) > 3:
                code = False
        if code:
            content += "```"

        return content.replace("@", "@_").replace("&", "&_")

    def __saveStats(self):
        """Save message statistics to the database"""
        for w, n in self.stats.values():
            repo_w.set(int(w), n)
        return


def setup(bot):
    bot.add_cog(Wormhole(bot))
