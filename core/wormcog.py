import asyncio
import datetime
import json
import re
from typing import List, Union

import discord
from discord.ext import commands

from core import output, objects
from core.database import repo_b, repo_u, repo_w

# TODO When the message is removed, remove it from sent[], too


config = json.load(open("config.json"))


async def presence(bot: commands.Bot):
    s = f"{config['prefix']}help"
    await bot.change_presence(activity=discord.Game(s))


class Wormcog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        # active text channels acting as wormholes
        self.wormholes = {}

        # sent messages still held in memory
        self.sent = []

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

        wormholes = repo_w.list_objects(beam)
        for wormhole in wormholes:
            self.wormholes[beam].append(self.bot.get_channel(wormhole.discord_id))

    def delay(self, key: str = "user"):
        if key == "user":
            return 20
        if key == "admin":
            return 10

    def get_free_nickname(self, nickname: str) -> str:
        i = 0
        orig_name = nickname
        while repo_u.is_nickname_used(nickname):
            nickname = f"{orig_name}{i}"
            i += 1
        return nickname

    async def smart_send(self, ctx, *, content: str = None, embed: discord.Embed = None):
        if content is None and embed is None:
            return

        if hasattr(ctx.channel, "id") and repo_w.get(ctx.channel.id) is not None:
            await ctx.send(content=content, embed=embed, delete_after=self.delay())
        else:
            await ctx.send(content=content, embed=embed)

    async def send(
        self,
        *,
        message: discord.Message,
        text: str,
        files: list = None,
    ):
        """Distribute the message"""
        deleted_original = False

        # get variables
        messages = [message]
        db_w = repo_w.get(message.channel.id)
        db_b = repo_b.get(db_w.beam)

        # access control
        if db_b.active == 0:
            return
        if db_w.active == 0 or db_w.readonly == 1:
            return
        if repo_u.get_attribute(message.author.id, "readonly") == 1:
            return

        # remove the original, if possible
        manage_messages_perm = message.guild.me.permissions_in(message.channel).manage_messages
        if manage_messages_perm and db_b.replace == 1 and not files:
            try:
                messages[0] = message.author
                await self.delete(message)
                deleted_original = True
            except discord.Forbidden:
                pass

        # limit message length
        text = text[:1900]
        # this is a safe space before the usernames are expanded and it should be enough.
        # if someone intentionally sends a message that will be expanded over 2k characters,
        # it will be rejected by the API

        # update wormhole list
        if db_b.name not in self.wormholes.keys():
            self.reconnect(db_b.name)
        wormholes = self.wormholes[db_b.name]

        users = self._get_users_from_tags(beam_name=db_b.name, text=text)

        # replicate messages
        tasks = []
        for wormhole in wormholes:
            task = asyncio.ensure_future(
                self.replicate(
                    wormhole,
                    message,
                    messages,
                    users,
                    text,
                    files,
                    db_b,
                    manage_messages_perm,
                )
            )
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)

        # add checkmark to original, if it hasn't been deleted
        if not deleted_original:
            try:
                await message.add_reaction("✅")
            except discord.Forbidden:
                await message.channel.send(f"_Successfully distributed_ ✅")

        # save message objects in case of editing/deletion
        if db_b.timeout > 0:
            self.sent.append(messages)
            await asyncio.sleep(db_b.timeout)
            self.sent.remove(messages)

    async def replicate(
        self,
        wormhole,
        message,
        messages,
        users,
        text,
        files,
        db_b,
        manage_messages_perm,
    ):
        # skip not active wormholes
        if repo_w.get_attribute(wormhole.id, "active") == 0:
            return

        # skip source if message has attachments
        if wormhole.id == message.channel.id and len(files) > 0:
            return

        # skip source if bot hasn't got manage_messages permission
        if wormhole.id == message.channel.id and not manage_messages_perm:
            return

        # send message
        try:
            m = await wormhole.send(
                self._process_tags(
                    beam_name=db_b.name, wormhole_id=wormhole.id, users=users, text=text
                )
            )
            messages.append(m)
        except discord.Forbidden:
            await self.event.user(
                message,
                (
                    f"Forbidden to send message to {self.sanitise(message.guild.name)}"
                    f"/{self.sanitise(message.channel.name)}."
                ),
            )
        except Exception as e:
            await self.event.user(
                message,
                (
                    f"Could not send message to {self.sanitise(message.guild.name)}"
                    f"/{self.sanitise(message.channel.name)}:\n"
                    f">>>{type(e).__name__}\n{str(e)}"
                ),
            )

    def _get_users_from_tags(self, beam_name: str, text: str) -> List[objects.User]:
        tags = [repo_u.get_by_nickname(tag) for tag in re.findall(r"\(\(([^\(\)]*)\)\)", text)]
        users = [user for user in tags if user is not None and beam_name in user.home_ids.keys()]
        return users

    def _process_tags(
        self, beam_name: str, wormhole_id: int, users: List[objects.User], text: str
    ) -> str:
        for user in users:
            if wormhole_id == user.home_ids[beam_name]:
                text = text.replace(f"(({user.nickname}))", f"<@!{user.discord_id}>")
            else:
                text = text.replace(f"(({user.nickname}))", f"**__{user.nickname}__**")
        return text

    async def announce(self, *, beam: str, message: str):
        """Send information to all channels"""
        if len(message) <= 256:
            embed = self.get_embed(title=message)
        else:
            embed = self.get_embed(description=message)

        for db_w in repo_w.list_objects(beam=beam):
            await self.bot.get_channel(db_w.discord_id).send(embed=embed)

    async def feedback(self, ctx, *, private: bool = True, message: str):
        target = ctx.author if private else ctx
        await target.send(message)

    async def delete(self, message: discord.Message):
        """Try to delete original message"""
        try:
            await message.delete()
        except:
            return

    def sanitise(self, string: str, *, limit: int = 500) -> str:
        """Return cleaned-up string ready for output"""
        return discord.utils.escape_markdown(string).replace("@", "@\u200b")[:limit]

    def get_embed(
        self,
        *,
        ctx: commands.Context = None,
        message: discord.Message = None,
        author: discord.User = None,
        title: str = None,
        description: str = None,
        url: Union[str, discord.embeds._EmptyEmbed] = discord.Embed.Empty,
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
            title=title,
            description=description,
            url=url,
            color=discord.Color.light_grey(),
        )

        # add footer timestamp
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

        if discord.Embed.Empty not in (footer_image, footer_text):
            embed.set_footer(icon_url=footer_image, text=footer_text)

        # done
        return embed
