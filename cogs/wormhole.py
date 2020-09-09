import asyncio
import json
import re
from datetime import datetime

import discord
from discord.ext import commands

from core import checks, wormcog
from core.database import repo_b, repo_u, repo_w

started = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

config = json.load(open("config.json"))


class Wormhole(wormcog.Wormcog):
    """Transfer messages between guilds"""

    def __init__(self, bot):
        super().__init__(bot)

        # Global message counter
        self.transferred = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignore non-textchannel sources
        if not isinstance(message.channel, discord.TextChannel):
            return

        # do not act if author is bot
        if message.author.bot:
            return

        # get wormhole
        db_w = repo_w.get(message.channel.id)
        if db_w is None:
            return
        # get additional information
        db_b = repo_b.get(db_w.beam)

        # check for attributes
        # fmt: off
        if db_b.active == 0 \
        or db_w.active == 0 \
        or repo_u.get_attribute(message.author.id, "readonly") == 1:
            return await self.delete(message)
        # fmt: on

        # do not act if message is bot command
        if message.content.startswith(config["prefix"]):
            return await self.delete(message)

        # get wormhole channel objects
        if db_b.name not in self.wormholes or len(self.wormholes[db_b.name]) == 0:
            self.reconnect(db_b.name)

        # process incoming message
        content = await self.__process(message)

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
        self.__update_stats(message)

        # send the message
        await self.send(message=message, text=content, files=message.attachments)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return

        if after.author.bot:
            return

        if not repo_w.exists(after.channel.id):
            return

        # get forwarded messages
        forwarded = None
        for m in self.sent:
            if m[0].id == after.id:
                forwarded = m
                break
        if not forwarded:
            await after.add_reaction("❎")
            await asyncio.sleep(1)
            await after.remove_reaction("❎", self.bot.user)
            return

        content = await self.__process(after)
        beam_name = repo_w.get_attribute(after.channel.id, "beam")
        users = self.__get_users_from_tags(beam_name=beam_name, text=content)
        for message in forwarded[1:]:
            await message.edit(
                content=self.__process_tags(
                    beam_name=beam_name, wormhole_id=after.channel.id, users=users, text=content
                )
            )
        await after.add_reaction("✅")
        await asyncio.sleep(1)
        await after.remove_reaction("✅", self.bot.user)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        # get forwarded messages
        forwarded = None
        for m in self.sent:
            if m[0].id == message.id:
                forwarded = m
                break
        if not forwarded:
            return
        for m in forwarded[1:]:
            await m.delete()

    @commands.command()
    async def help(self, ctx: commands.Context):
        """Display help"""
        embed = self.get_embed(ctx=ctx, title="User commands")
        p = config["prefix"]
        # fmt: off
        embed.add_field(name=f"**{p}e** | **{p}edit**",   value="Edit last message")
        embed.add_field(name=f"**{p}d** | **{p}delete**", value="Delete last message")
        embed.add_field(name=f"**{p}info**",              value="Connection information")
        embed.add_field(name=f"**{p}settings**",          value="Display current settings")
        embed.add_field(name=f"**{p}link**",              value="Link to GitHub repository")
        embed.add_field(name=f"**{p}invite**",            value="Bot invite link")

        db_u = repo_u.get(ctx.author.id)
        if "User" in self.bot.cogs and db_u is None:
            embed.add_field(name=f"**{p}register**",      value="Register your username")
            embed.add_field(name=f"**{p}whois**",         value="Get information about user")

        if "User" in self.bot.cogs and db_u is not None:
            embed.add_field(name=f"**{p}me**",            value="Display your information")
            embed.add_field(name=f"**{p}whois**",         value="Get information about user")
            embed.add_field(name=f"**{p}set**",           value="Edit nickname or home")

        if "User" in self.bot.cogs:
            embed.add_field(
                name=f"{p}invites",
                value="Invite links to wormhole channels",
                inline=False
            )

        embed.add_field(
            name="Online help",
            value="https://sinus-x.github.io/discord-wormhole/commands",
            inline=False
        )
        # fmt: on
        if hasattr(ctx.channel, "id"):
            # we are in public channel
            await ctx.send(embed=embed, delete_after=self.delay())
        else:
            # private channel, we can keep the message
            await ctx.send(embed=embed)
        await self.delete(ctx.message)

    @commands.guild_only()
    @commands.check(checks.in_wormhole)
    @commands.command(name="remove", aliases=["d", "delete", "r"])
    async def remove(self, ctx: commands.Context):
        """Delete last sent message"""
        if len(self.sent) == 0:
            return

        for msgs in self.sent[::-1]:
            # fmt: off
            if isinstance(msgs[0], discord.Member) and ctx.author.id == msgs[0].id \
            or isinstance(msgs[0], discord.Message) and ctx.author.id == msgs[0].author.id:
                await self.delete(ctx.message)
                for m in msgs:
                    await self.delete(m)
                break
            # fmt: on

        # TODO Remove from self.sent

    @commands.guild_only()
    @commands.check(checks.in_wormhole)
    @commands.command(name="edit", aliases=["e"])
    async def edit(self, ctx: commands.Context, *, text: str):
        """Edit last sent message

        text: A new text
        """
        if len(self.sent) == 0:
            return

        for msgs in self.sent[::-1]:
            # fmt: off
            if isinstance(msgs[0], discord.Member)  and ctx.author.id == msgs[0].id \
            or isinstance(msgs[0], discord.Message) and ctx.author.id == msgs[0].author.id:
                await self.delete(ctx.message)
                m = ctx.message
                m.content = m.content.split(" ", 1)[1]
                content = await self.__process(m)

                beam_name = repo_w.get_attribute(m.channel.id, "beam")
                users = self.__get_users_from_tags(beam_name=beam_name, text=content)
                for message in msgs[1:]:
                    try:
                        await message.edit(
                            content=self.__process_tags(
                                beam_name=beam_name,
                                wormhole_id=message.channel.id,
                                users=users,
                                text=content,
                            )
                        )
                    except Exception as e:
                        self.event.user(
                            ctx, (
                                f"Could not edit message in {self.sanitise(message.guild.name)}"
                                f"/{self.sanitise(message.channel.name)}:\n>>> {e}"
                            )
                        )
                        await message.channel.send(
                            f"> **{self.sanitise(ctx.author.name)}**: " +
                            f"Could not replicate in **{self.sanitise(message.guild.name)}**.",
                            delete_after=0.5,
                        )
                break
            # fmt: on

    @commands.cooldown(rate=1, per=20, type=commands.BucketType.channel)
    @commands.command(aliases=["stat", "stats"])
    async def info(self, ctx: commands.Context):
        """Display information about wormholes"""
        public = hasattr(ctx.channel, "id") and repo_w.get(ctx.channel.id) is not None

        if public:
            await ctx.send(
                self.__get_info(repo_w.get_attribute(ctx.channel.id, "beam")),
                delete_after=self.delay(),
            )
            return

        user_beams = repo_u.get_home(ctx.author.id).keys()
        for beam_name in user_beams:
            await ctx.send(self.__get_info(beam_name, title=True))

    @commands.guild_only()
    @commands.check(checks.in_wormhole)
    @commands.command()
    async def settings(self, ctx: commands.Context):
        """Display settings for current beam"""
        db_w = repo_w.get(ctx.channel.id)
        db_b = repo_b.get(db_w.beam)
        db_u = repo_u.get(ctx.author.id)

        msg = ">>> **Settings**:\n"
        # beam settings
        pars = []
        # fmt: off
        pars.append("active" if db_b.active else "inactive")
        pars.append(f"replacing (timeout **{db_b.timeout} s**)" if db_b.replace else "not replacing")
        pars.append(f"anonymity level **{db_b.anonymity}**")
        # fmt: on
        msg += ", ".join(pars)

        # wormhole settings
        pars = []
        if db_w.active is False:
            pars.append("inactive")
        if db_w.readonly is True:
            pars.append("read only")
        if len(pars) > 0:
            msg += "\n**Wormhole overrides**:\n"
            msg += ", ".join(pars)

        # user settings
        if db_u is not None and db_u.readonly is True:
            msg += "\n**User overrides**:\n"
            msg += "read only"

        await ctx.send(msg, delete_after=self.delay())

    @commands.command()
    async def link(self, ctx: commands.Context):
        """Send a message with link to the bot"""
        text = "> **GitHub link:** https://github.com/sinus-x/discord-wormhole"
        if hasattr(ctx.channel, "id"):
            await ctx.send(text, delete_after=self.delay())
        else:
            await ctx.send(text)
        await self.delete(ctx.message)

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Invite the wormhole to your guild"""
        # permissions:
        # - send messages      - attach files
        # - manage messages    - use external emojis
        # - embed links        - add reactions
        text = (
            "> **Invite link:** https://discordapp.com/oauth2/authorize?client_id="
            + str(self.bot.user.id)
            + "&permissions=321600&scope=bot"
        )
        if hasattr(ctx.channel, "id"):
            await ctx.send(text, delete_after=self.delay())
        else:
            await ctx.send(text)
        await self.delete(ctx.message)

    def __get_prefix(self, message: discord.Message, first_line: bool = True):
        """Get prefix for message"""
        db_w = repo_w.get(message.channel.id)
        db_b = repo_b.get(db_w.beam)
        db_u = repo_u.get(message.author.id)

        # get user nickname
        if db_u is not None:
            if db_b.name in db_u.home_ids:
                # user has home wormhole
                home = repo_w.get(db_u.home_ids[db_b.name])
            else:
                # user is registered without home
                home = None

            if home is not None:
                name = "__" + db_u.nickname + "__"
            else:
                name = db_u.nickname
        else:
            name = self.sanitise(message.author.name, limit=32)
            home = db_w

        # get logo
        if hasattr(home, "logo") and len(home.logo):
            if first_line:
                logo = home.logo
            else:
                logo = config["logo fill"]
        else:
            logo = self.sanitise(message.guild.name)

        # get prefix
        if db_b.anonymity == "none":
            # display everything
            prefix = f"{logo} **{name}**: "
        elif db_b.anonymity == "guild" and len(logo):
            # display guild logo
            prefix = logo + " "
        elif db_b.anonymity == "guild" and len(logo) == 0:
            # display guild name
            prefix = f"{logo}, **{name}**"
        else:
            # wrong configuration or full anonymity
            prefix = ""

        return prefix

    async def __process(self, message: discord.Message):
        """Escape mentions and apply anonymity"""
        content = message.content

        users = re.findall(r"<@!?[0-9]+>", content)
        roles = re.findall(r"<@&[0-9]+>", content)
        channels = re.findall(r"<#[0-9]+>", content)
        emojis = re.findall(r"<:[a-zA-Z0-9_]+:[0-9]+>", content)

        # prevent tagging
        for u in users:
            try:
                # Get discord user tags. If they're registered, translate to
                # their ((nickname)); it will be converted on send.
                user_id = int(u.replace("<@!", "").replace("<@", "").replace(">", ""))
                nickname = repo_u.get_attribute(user_id, "nickname")
                if nickname is not None:
                    user = "((" + nickname + "))"
                else:
                    user = str(self.bot.get_user(user_id))
            except Exception as e:
                user = "unknown-user"
                await self.event.user(message, "Problem in user retrieval:\n>>>{e}")
            content = content.replace(u, user)
        for r in roles:
            try:
                role = message.guild.get_role(int(r.replace("<@&", "").replace(">", ""))).name
            except Exception as e:
                role = "unknown-role"
                await self.event.user(message, "Problem in role retrieval:\n>>>{e}")
            content = content.replace(r, role)
        # convert channel tags to universal names
        for channel in channels:
            try:
                ch = self.bot.get_channel(int(channel.replace("<#", "").replace(">", "")))
                channel_name = self.sanitise(ch.name)
                guild_name = self.sanitise(ch.guild.name)
                content = content.replace(channel, f"__**{guild_name}/{channel_name}**__")
            except Exception as e:
                await self.event.user(message, "Problem in channel retrieval:\n>>>{e}")
        # remove unavailable emojis
        for emoji in emojis:
            emoji_ = emoji.replace("<:", "").replace(">", "")
            emoji_name = emoji_.split(":")[0]
            emoji_id = int(emoji_.split(":")[1])
            if self.bot.get_emoji(emoji_id) is None:
                content = content.replace(emoji, ":" + emoji_name + ":")

        # line preprocessor for codeblocks
        if "```" in content:
            backticks = re.findall(r"```[a-z0-9]*", content)
            for b in backticks:
                content = content.replace(f" {b}", f"\n{b}", 1)
                content = content.replace(f"{b} ", f"{b}\n", 1)

        # apply prefixes
        content_ = content.split("\n")
        content = ""
        p = self.__get_prefix(message)
        code = False
        for i in range(len(content_)):
            if i == 1:
                # use fill icon instead of guild one
                p = self.__get_prefix(message, first_line=False)
            line = content_[i]
            # add prefix if message starts with code block
            if i == 0 and line.startswith("```"):
                content += self.__get_prefix(message) + "\n"
            if line.startswith("```"):
                code = True
            if code:
                content += line + "\n"
            else:
                content += p + line + "\n"
            if line.endswith("```") and code:
                code = False

        return content.replace("@", "@_")

    def __update_stats(self, message: discord.Message):
        """Increment wormhole's statistics"""
        current = repo_w.get_attribute(message.channel.id, "messages")
        repo_w.set(message.channel.id, "messages", current + 1)
        beam_name = repo_w.get_attribute(message.channel.id, "beam")
        if beam_name in self.transferred:
            self.transferred[beam_name] += 1
        else:
            self.transferred[beam_name] = 1

    def __get_info(self, beam_name: str, title: bool = False) -> str:
        """Get beam statistics.

        If title is True, the message has beam information.
        """
        # heading
        msg = ["**Beam __" + beam_name + "__**"] if title else []

        since = self.transferred[beam_name] if beam_name in self.transferred else 0
        msg += [
            f">>> **[[total]]** messages sent in total "
            f"(**{since}** since {started}); "
            f"ping **{self.bot.latency:.2f}s**",
            "",
            "Currently opened wormholes:",
        ]

        wormholes = repo_w.list_objects(beam_name)
        wormholes.sort(key=lambda x: x.messages, reverse=True)

        # loop over wormholes in current beam
        count = 0
        for wormhole in wormholes:
            count += wormhole.messages
            line = []
            # logo
            if len(wormhole.logo):
                line.append(wormhole.logo)
            # guild, channel, counter
            channel = self.bot.get_channel(wormhole.discord_id)
            line.append(
                f"**{self.sanitise(channel.guild.name)}** ({self.sanitise(channel.name)}): "
                f"**{wormhole.messages}** messages"
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

        return "\n".join(msg).replace("[[total]]", str(count))


def setup(bot):
    bot.add_cog(Wormhole(bot))
