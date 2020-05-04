import re
import json
import asyncio
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands

import init, wormcog

started = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

class Wormhole(wormcog.Wormcog):
	"""Transfer messages between guilds"""

	def __init__(self, bot):
		super().__init__(bot)

		self.transferred = 0
		try:
			self.stats = self.config['stats']
		except KeyError:
			self.stats = {}

		self.timer = None

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		# do not act if channel is not wormhole channel
		if message.channel.id not in self.config['wormholes']:
			return

		# do not act if author is bot
		if message.author.bot:
			return

		# do not act if message is bot command
		if message.content.startswith(self.config['prefix']):
			return

		# get wormhole channel objects
		self.wormholesUpdate()

		# copy remote message
		content = self.__process(message)

		if message.attachments:
			for f in message.attachments:
				content += '\n' + f.url

		if len(content) < 1:
			return

		# count the message
		self.transferred += 1
		if self.transferred % 50 == 0:
			self.confSave()
		try:
			self.stats[str(message.guild.id)] += 1
		except KeyError:
			self.stats[str(message.guild.id)] = 1

		# send the message
		await self.send(message, content, files=message.attachments)

		# no activity timer
		async def silent_callback():
			await self.send(message, text=self.config['no activity message'], announcement=True)
			self.timer = None

		if self.timer:
			self.timer.cancel()
		if self.config['no activity timeout'] > 0:
			self.timer = Timer(self.config['no activity timeout']*60, silent_callback)

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
			return

		content = self.__process(after)
		for m in forwarded[1:]:
			await m.edit(content=content)

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


	@commands.check(init.in_wormhole)
	@commands.command(aliases=["stat", "stats"])
	async def info(self, ctx: commands.Context):
		"""Display information about wormholes"""

		if len(self.wormholes) == 0:
			self.wormholesUpdate()
			await asyncio.sleep(.25)

		if len(self.wormholes) == 0:
			m = "> No wormhole has been opened."
		else:
			# get total message count
			total = 0
			for i in self.stats:
				total += self.stats[i]
			m = "> {} messages sent since the formation (**{}**); ping **{:.2f} s**.\n".format(self.transferred, started, self.bot.latency)

			m+= "> Currently opened wormholes:"
			for w in self.wormholes:
				# get logo
				try:
					logo = self.config['aliases'][str(w.guild.id)]
					logo = logo if isinstance(logo, str) else ''
				except KeyError:
					logo = ''

				# get names
				g = discord.utils.escape_markdown(w.guild.name)
				c = discord.utils.escape_markdown(w.name)

				# get message count
				try:
					cnt = self.stats[str(w.guild.id)]
				except KeyError:
					cnt = 0

				# get message
				m += f'\n> {logo} **{g}** (#{c}): **{cnt}** messages'
		await ctx.send(m, delete_after=self.removalDelay())
		await self.delete(ctx.message)

	@commands.check(init.in_wormhole)
	@commands.command()
	async def help(self, ctx: commands.Context):
		"""Display help"""
		embed = discord.Embed(title="Wormhole", color=discord.Color.light_grey())
		p = self.config['prefix']
		embed.add_field(value=f"**{p}e** | **{p}edit**", name="Edit last message")
		embed.add_field(value=f"**{p}d** | **{p}delete**", name="Delete last message")
		embed.add_field(value=f"**{p}info**", name="Connection information")
		embed.add_field(value=f"**{p}settings**", name="Display current settings")
		embed.add_field(value=f"**{p}link**", name="Link to GitHub repository")
		embed.add_field(value=f"**{p}invite**", name="Bot invite link")
		await ctx.send(embed=embed, delete_after=self.removalDelay())
		await self.delete(ctx.message)

	@commands.check(init.in_wormhole)
	@commands.group(name="wormhole")
	async def wormhole(self, ctx: commands.Context):
		"""Control the wormholes"""
		if ctx.invoked_subcommand is not None:
			return

		await self.help(ctx)

	@commands.check(init.is_admin)
	@wormhole.command()
	async def open(self, ctx: commands.Context):
		"""Open a wormhole"""
		if ctx.channel.id in self.config['wormholes']:
			return
		self.confAdd('wormholes', ctx.channel.id)
		self.wormholesUpdate()
		self.confSave()
		await asyncio.sleep(.25)
		await self.send(message=ctx.message, announcement=True,
			text="> Wormhole opened: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))

	@commands.check(init.is_admin)
	@wormhole.command()
	async def close(self, ctx: commands.Context):
		"""Close the current wormhole"""
		if ctx.channel.id not in self.config['wormholes']:
			return
		self.confDel('wormholes', ctx.channel.id)
		self.wormholesUpdate()
		self.confSave()
		await ctx.send("> **Woosh**. The wormhole is gone")
		await self.send(message=ctx.message, announcement=True,
			text="> Wormhole closed: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))
		if len(self.wormholes) == 0:
			self.transferred = 0

	@commands.check(init.in_wormhole)
	@commands.command(name="remove", aliases=["d", "delete", "r"])
	async def remove(self, ctx: commands.Context):
		"""Delete last sent message"""
		if len(self.sent) == 0:
			return

		for msgs in self.sent[::-1]:
			if isinstance(msgs[0], discord.Member) and ctx.author.id == msgs[0].id \
			or isinstance(msgs[0], discord.Message) and ctx.author.id == msgs[0].author.id:
				await self.delete(ctx.message)
				for m in msgs:
					await self.delete(m)
				return

	@commands.check(init.in_wormhole)
	@commands.command(name="edit", aliases=["e"])
	async def edit(self, ctx: commands.Context,  *, text: str):
		"""Edit last sent message

		text: A new text
		"""
		if len(self.sent) == 0:
			return

		for msgs in self.sent[::-1]:
			if isinstance(msgs[0], discord.Member) and ctx.author.id == msgs[0].id \
			or isinstance(msgs[0], discord.Message) and ctx.author.id == msgs[0].author.id:
				await self.delete(ctx.message)
				m = ctx.message
				m.content = m.content.split(' ', 1)[1]
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
		m = "> **Wormhole settings**: anonymity level **{}**, edit/delete timer **{}s**"
		await ctx.send(m.format(self.config['anonymity'], self.config['message window']))
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
		m = "> **Invite link:** https://discordapp.com/oauth2/authorize?client_id=" + \
			str(self.bot.user.id) + "&permissions=321600&scope=bot"
		await ctx.send(m)
		await self.delete(ctx.message)

	def __getPrefix(self, message: discord.Message, firstline: bool = True):
		"""Get prefix for message"""
		a = self.config['anonymity']
		u = discord.utils.escape_markdown(message.author.name)
		g = str(message.guild.id)
		logo = g in self.config['aliases'] and self.config['aliases'][g] is not None
		if logo:
			if not firstline:
				g = self.config['prefix fill']
			else:
				g = self.config['aliases'][g]
		else:
			g = discord.utils.escape_markdown(message.guild.name) + ','

		if a == 'none':
			return f'{g} **{u}**: '

		if a == 'guild' and logo:
			return f'**{g}** '
		if a == 'guild':
			return f'**{g}**: '

		return ''

	def __process(self, message: discord.Message):
		"""Escape mentions and apply anonymity"""
		content = message.content
		#FIXME This is not pretty at all

		users = re.findall(r"<@![0-9]+>", content)
		roles = re.findall(r"<@&[0-9]+>", content)
		chnls = re.findall(r"<#[0-9]+>", content)

		for u in users:
			try:
				user = str(self.bot.get_user(int(u.replace('<@!','').replace('>',''))))
			except:
				user = "unknown-user"
			content = content.replace(u, user)
		for r in roles:
			try:
				role = message.guild.get_role(int(r.replace('<@&','').replace('>',''))).name
			except:
				role = "unknown-role"
			content = content.replace(r, role)
		for c in chnls:
			try:
				ch = self.bot.get_channel(int(c.replace('<#','').replace('>','')))
				channel = '#['+ch.guild.name + ':' + ch.name + ']'
			except:
				channel = "unknown-channel"
			content = content.replace(c, channel)

		# line preprocessor (code)
		content_ = content.split('\n')
		if '```' in content:
			content = []
			for line in content_:
				# do not allow code block starting on text line
				line.replace(' ```', '\n```')
				# do not alow text on code block end
				line.replace('``` ', '```\n')
				line = line.split('\n')
				for l in line:
					content.append(l)
		else:
			content = content_

		# apply prefixes
		content_ = content.copy()
		content = ''
		p = self.__getPrefix(message)
		code = False
		for i in range(len(content_)):
			if i == 1:
				# use fill icon instead of guild one
				p = self.__getPrefix(message, firstline=False)
			line = content_[i]
			# add prefix if message starts with code block
			if i == 0 and line.startswith('```'):
				content += self.__getPrefix(message) + '\n'
			if line.startswith('```'):
				code = True
			if code:
				content += line + '\n'
			else:
				content += p + line + '\n'
			if line.endswith('```') and code and len(line) > 3:
				code = False
		if code:
			content += '```'

		return content.replace('@','@_').replace('&','&_')

class Timer:
	def __init__(self, timeout, callback):
		self._timeout = timeout
		self._callback = callback
		self._task = asyncio.ensure_future(self._job())

	async def _job(self):
		await asyncio.sleep(self._timeout)
		await self._callback()

	def cancel(self):
		self._task.cancel()

def setup(bot):
	bot.add_cog(Wormhole(bot))
