import re
import json
from datetime import datetime

import discord
from discord.ext import commands

from core import checks, wormcog
from core.database import repo_u, repo_w

started = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

config = json.load(open("config.json"))


class Wormhole(wormcog.Wormcog):
    """Transfer messages between guilds"""

    def __init__(self, bot):
        super().__init__(bot)

        # Global message counter
        self.transferred = 0

        # Per-channel message couter
        self.stats = {}
        for w in repo_w.getAll():
            self.stats[str(w.channel)] = w.messages

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
            await self.delete(message)
            return

        # get current beam
        beam = self.message2Beam(message).name

        # get wormhole channel objects
        if beam not in self.wormholes or len(self.wormholes[beam]) == 0:
            self.reconnect(beam)

        # process incoming message
        content = self.__process(message)

        # convert attachments to links
        firstline = True
        if message.attachments:
            for f in message.attachments:
                # don't add newline if message has only attachments
                if firstline:
                    content += " " + f.url
                    firstline = False
                else:
                    content += "\n" + f.url

        if len(content) < 1:
            return

        # count the message
        self.__updateStats(message)

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

    @commands.check(checks.in_wormhole)
    @commands.command()
    async def help(self, ctx: commands.Context):
        """Display help"""
        embed = discord.Embed(title="Wormhole", color=discord.Color.light_grey())
        p = config["prefix"]
        # fmt: off
        embed.add_field(value=f"**{p}e** | **{p}edit**",   name="Edit last message")
        embed.add_field(value=f"**{p}d** | **{p}delete**", name="Delete last message")
        embed.add_field(value=f"**{p}info**",              name="Connection information")
        embed.add_field(value=f"**{p}settings**",          name="Display current settings")
        embed.add_field(value=f"**{p}link**",              name="Link to GitHub repository")
        embed.add_field(value=f"**{p}invite**",            name="Bot invite link")

        if "User" in self.bot.cogs and repo_u.get(ctx.author.id) is None:
            embed.add_field(value="**VISITOR COMMANDS**", name="\u200b", inline=False)
            embed.add_field(value=f"**{p}register**", name="Register your username")
            embed.add_field(value=f"**{p}whois**",    name="Get information about user")

        if "User" in self.bot.cogs and repo_u.get(ctx.author.id) is not None:
            embed.add_field(value="**USER COMMANDS**",   name="\u200b", inline=False)
            embed.add_field(value=f"**{p}me**",       name="Get your information")
            embed.add_field(value=f"**{p}whois**",    name="Get information about user")
            embed.add_field(value=f"**{p}set**",      name="Edit nickname or home")

        if "Admin" in self.bot.cogs and ctx.author.id in [x.id for x in repo_u.getMods()]:
            embed.add_field(value=f"**MOD COMMANDS   |   {p}user edit ...**", name="\u200b", inline=False)
            embed.add_field(value="... **nickname [name]**",       name="Nickname")
            embed.add_field(value="... **readonly [true|false]**", name="Write permission")
            embed.add_field(value="... **home [wormhole]**",       name="Home guild")
        # fmt: on
        await ctx.send(embed=embed, delete_after=self.removalDelay())
        await self.delete(ctx.message)

    @commands.check(checks.in_wormhole)
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
                    try:
                        await self.delete(m)
                    except Exception as e:
                        await self.console.critical(
                            f"Could not delete message in {m.channel.id}", error=e
                        )
                return

    @commands.check(checks.in_wormhole)
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
                        await self.console.critical(
                            f"Could not edit message in {m.channel.id}", error=e
                        )
                return

    @commands.check(checks.in_wormhole)
    @commands.command(aliases=["stat", "stats"])
    async def info(self, ctx: commands.Context):
        """Display information about wormholes"""
        # heading
        msg = [
            f">>> **[[total]]** messages sent in total "
            f"(**{self.transferred}** since {started}); "
            f"ping **{self.bot.latency:.2f}s**",
            "",
            "Currently opened wormholes:",
        ]
        beam = self.message2Beam(ctx.message).name
        wormholes = repo_w.getByBeam(beam)
        # loop over wormholes in current beam
        count = 0
        for wormhole in wormholes:
            count += wormhole.messages
            line = []
            # logo
            if wormhole.logo is not None:
                line.append(wormhole.logo)
            # guild, channel, counter
            channel = self.bot.get_channel(wormhole.channel)
            line.append(
                f"**{discord.utils.escape_markdown(channel.guild.name)}** "
                f"(#{discord.utils.escape_markdown(channel.name)}): "
                f"**{self.stats[str(wormhole.channel)]}** messages"
            )
            # inactive, ro
            pars = []
            if wormhole.active is False:
                pars.append("inactive")
            if wormhole.readonly is True:
                pars.append("read only")
            if len(pars) > 0:
                line.append(f"({', '.join(pars)})")
            # join and send
            msg.append(" ".join(line))

        # in total count, include messages not yet saved into the database
        count = count + self.transferred % 50
        await ctx.send(
            "\n".join(msg).replace("[[total]]", str(count)), delete_after=self.removalDelay()
        )

    @commands.check(checks.in_wormhole)
    @commands.command()
    async def settings(self, ctx: commands.Context):
        """Display settings for current beam"""

        # beam settings
        beam = self.message2Beam(ctx.message)
        msg = ">>> **Settings**:\n"
        pars = []
        # fmt: off
        pars.append("active" if beam.active else "inactive")
        pars.append(f"replacing (timeout **{beam.timeout} s**)" if beam.replace else "not replacing")
        pars.append(f"anonymity level **{beam.anonymity}**")
        # fmt: on
        msg += ", ".join(pars)

        # wormhole settings
        wormhole = repo_w.get(ctx.channel.id)
        pars = []
        if wormhole.active is False:
            pars.append("inactive")
        if wormhole.readonly is True:
            pars.append("read only")
        if len(pars) > 0:
            msg += "\n**Wormhole overrides**:\n"
            msg += ", ".join(pars)

        # user settings
        user = repo_u.get(ctx.author.id)
        if user is not None and user.readonly is True:
            msg += "\n**User overrides**:\n"
            msg += "read only"

        await ctx.send(msg, delete_after=self.removalDelay())

    @commands.check(checks.in_wormhole)
    @commands.command()
    async def link(self, ctx: commands.Context):
        """Send a message with link to the bot"""
        await ctx.send("> **GitHub link:** https://github.com/sinus-x/discord-wormhole")
        await self.delete(ctx.message)

    @commands.check(checks.in_wormhole)
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
        beam = self.message2Beam(message)
        wormhole = repo_w.get(message.channel.id)
        user = repo_u.get(message.author.id)

        # get user nickname
        if user is not None:
            name = user.nickname
        else:
            name = discord.utils.escape_markdown(message.author.name)

        # get logo
        if wormhole.logo is not None:
            if firstline:
                logo = wormhole.logo
            else:
                logo = config["logo fill"]
        else:
            logo = None

        # get prefix
        if beam.anonymity == "none":
            # display everything
            return f"{logo} **{name}**: "
        if beam.anonymity == "guild" and logo is not None:
            # display guild logo
            return logo + " "
        if beam.anonymity == "guild" and logo is None:
            # display guild name
            return f"{discord.utils.escape_markdown(message.guild.name)}, **{name}**"
        # wrong configuration or full anonymity
        return ""

    def __process(self, message: discord.Message):
        """Escape mentions and apply anonymity"""
        content = message.content

        # FIXME This is not pretty at all
        users = re.findall(r"<@![0-9]+>", content)
        roles = re.findall(r"<@&[0-9]+>", content)

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

        # line preprocessor (code)
        if "```" in content:
            backticks = re.findall(r"```[a-z0-9]*", content)
            for b in backticks:
                content = content.replace(f" {b}", f"\n{b}", 1)
                content = content.replace(f"{b} ", f"{b}\n", 1)

        # apply prefixes
        content_ = content.split("\n")
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
            if line.endswith("```") and code:
                code = False

        return content.replace("@", "@_")

    def __updateStats(self, message: discord.Message):
        """Increment wormhole's statistics"""
        # get wormhole ID
        author = repo_u.get(message.channel.id)
        if author is not None:
            wormhole_id = author.home
        else:
            wormhole_id = message.channel.id

        try:
            self.stats[str(wormhole_id)] += 1
        except KeyError:
            self.stats[str(wormhole_id)] = 1

        # save
        self.transferred += 1
        if self.transferred % 50 == 0:
            self.__saveStats()

    def __saveStats(self):
        """Save message statistics to the database"""
        for wormhole, count in self.stats.items():
            repo_w.set(int(wormhole), messages=count)


def setup(bot):
    bot.add_cog(Wormhole(bot))
