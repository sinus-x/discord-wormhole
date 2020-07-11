import asyncio
import datetime
import git
import json
import re

import discord
from discord.ext import commands

from core import output
from core.database import repo_b, repo_u, repo_w

# TODO When the message is removed, remove it from sent[], too


config = json.load(open("config.json"))


async def presence(bot: commands.Bot):
    git_repo = git.Repo(search_parent_directories=True)
    git_hash = git_repo.head.object.hexsha[:7]
    s = f"{config['prefix']}help | " + git_hash
    await bot.change_presence(activity=discord.Game(s))


class Wormcog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        # active text channels acting as wormholes
        self.wormholes = {}

        # sent messages still held in memory
        self.sent = []

        # missing manage_messages permission notification
        self.missing_notify = []

        # bot management logging
        self.event = output.Event(self.bot)

    ##
    ## FUNCTIONS
    ##

    def reconnect(self, beam: str = None):
        if beam is None:
            self.wormholes = {}
        else:
            self.wormholes[beam] = []

        wormholes = repo_w.listObjects(beam)
        for wormhole in wormholes:
            self.wormholes[beam].append(self.bot.get_channel(wormhole.discord_id))

    def delay(self, key: str = "user"):
        if key == "user":
            return 20
        if key == "admin":
            return 10

    async def smartSend(self, ctx, *, content: str = None, embed: discord.Embed = None):
        if content is None and embed is None:
            return

        if hasattr(ctx.channel, "id") and repo_w.get(ctx.channel.id) is not None:
            await ctx.send(content=content, embed=embed, delete_after=self.delay())
        else:
            await ctx.send(content=content, embed=embed)

    async def send(
        self, *, message: discord.Message, text: str, files: list = None,
    ):
        """Distribute the message"""
        # get variables
        messages = [message]
        db_w = repo_w.get(message.channel.id)
        db_b = repo_b.get(db_w.beam)

        # access control
        if db_b.active == 0:
            return
        if db_w.active == 0 or db_w.readonly == 1:
            return
        if repo_u.getAttribute(message.author.id, "readonly") == 1:
            return

        # remove the original, if possible
        manage_messages_perm = message.guild.me.permissions_in(message.channel).manage_messages
        if manage_messages_perm and db_b.replace == 1 and not files:
            try:
                messages[0] = message.author
                await self.delete(message)
            except discord.Forbidden:
                pass

        # limit message length
        text = text[:1024]

        # update wormhole list
        if db_b.name not in self.wormholes.keys():
            self.reconnect(db_b.name)
        wormholes = self.wormholes[db_b.name]

        # get tags in the message
        users = [repo_u.getByNickname(t) for t in re.findall(r"\(\(([^\(\)]*)\)\)", text)]
        users = [u for u in users if u is not None and u.home_ids[db_b.name] is not None]

        # replicate messages
        for wormhole in wormholes:
            # If the source message cannot be removed for technical reasons (bot doesn't have
            # permissions to do so), send notification message for the first time.
            if wormhole.id == message.channel.id and db_b.replace and not manage_messages_perm:
                if str(wormhole.id) not in self.missing_notify:
                    admin_id = repo_w.getAttribute(wormhole.id, "admin_id")
                    notify_text = (
                        "**I do not have permissions to manage messages. "
                        "Grant it, please, for smoother experience.**"
                    )
                    if admin_id != 0:
                        wormhole_admin = "<@!" + str(admin_id) + ">"
                        notify_text += (
                            "\n" + wormhole_admin + ", you are configured as an local admin. "
                            "Can you do it?"
                        )
                    await message.channel.send(notify_text)
                    self.missing_notify.append(str(wormhole.id))

            # skip not active wormholes
            if repo_w.getAttribute(wormhole.id, "active") == 0:
                continue

            # skip source if message has attachments
            if wormhole.id == message.channel.id and len(files) > 0:
                continue

            # skip source if bot hasn't got manage_messages permission
            if wormhole.id == message.channel.id and not manage_messages_perm:
                continue

            # apply tags
            w_text = text
            for user in users:
                if wormhole.id == user.home_ids[db_b.name]:
                    w_text = w_text.replace(f"(({user.nickname}))", f"<@!{user.discord_id}>")
                else:
                    w_text = w_text.replace(f"(({user.nickname}))", f"**__{user.nickname}__**")

            # send message
            try:
                m = await wormhole.send(w_text)
                messages.append(m)
            except discord.Forbidden:
                await self.event.user(message, f"Could not send message to {wormhole.id}!")

        # save message objects in case of editing/deletion
        if db_b.timeout > 0:
            self.sent.append(messages)
            await asyncio.sleep(db_b.timeout)
            self.sent.remove(messages)

    async def announce(self, *, beam: str, message: str):
        """Send information to all channels"""
        db_ws = repo_w.listObjects(beam=beam)
        for db_w in db_ws:
            await self.bot.get_channel(db_w.discord_id).send("**WORMHOLE:** " + message)

    async def feedback(self, ctx, *, private: bool = True, message: str):
        target = ctx.author if private else ctx
        await target.send(message)

    async def delete(self, message: discord.Message):
        """Try to delete original message"""
        try:
            await message.delete()
        except:
            return

    def sanitise(self, string: str, *, limit: int = 500):
        """Return cleaned-up string ready for output"""
        return discord.utils.escape_markdown(string).replace("@", "")[:limit]

    def getEmbed(
        self,
        *,
        ctx: commands.Context = None,
        message: discord.Message = None,
        author: discord.User = None,
        title: str = None,
        description: str = None,
        url: str = None,
    ) -> discord.Embed:
        """Create embed"""
        # author
        if hasattr(ctx, "author"):
            footer_text = "Reply for " + str(ctx.author)
            footer_image = ctx.author.avatar_url
        elif hasattr(message, "author"):
            footer_text = "Reply for " + str(message.author)
            footer_image = message.author.avatar_url
        else:
            footer_text = discord.Embed.Empty
            footer_image = discord.Embed.Empty

        # title
        if title is not None:
            pass
        elif hasattr(ctx, "command") and hasattr(ctx.command, "qualified_name"):
            title = config.prefix + ctx.command.qualified_name
        else:
            title = "Wormhole"

        # description
        if description is not None:
            pass
        elif hasattr(ctx, "cog_name"):
            description = f"**{ctx.cog_name}**"
        else:
            description = ""

        # create embed
        embed = discord.Embed(
            title=title, description=description, url=url, color=discord.Color.light_grey()
        )

        # add footer timestamp
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

        if discord.Embed.Empty not in (footer_image, footer_text):
            embed.set_footer(icon_url=footer_image, text=footer_text)

        # done
        return embed
