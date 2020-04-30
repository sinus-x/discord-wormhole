import re
import json
import asyncio
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands

config = json.load(open('config.json'))

init = datetime.today().strftime("%Y-%m-%d %H:%M:%S")

class Wormhole(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		self.wormholes = []
		self.sent = []

		self.transferred = 0
		self.timer = None

	def is_admin(ctx: commands.Context):
		return ctx.author.id == config['admin id']

	def in_wormhole(ctx: commands.Context):
		return ctx.author.id == config['admin id'] \
		or ctx.channel.id in config['wormholes']

	#TODO Add support to manage bot from DMs
	#TODO Use guild nickname
	#TODO Split into public and admin commands
	#TODO Add on_typing listener
	#TODO Download and re-upload images that fit under the limit - and delete them afterwards

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		# do not act if channel is not wormhole channel
		if message.channel.id not in config['wormholes']:
			return

		# do not act if author is bot
		if message.author.bot:
			return

		# do not act if message is bot command
		if message.content.startswith(config['prefix'] + 'wormhole'):
			return

		# get wormhole channel objects
		self.__update()

		# copy remote message
		content = self.__process(message)

		if message.attachments:
			for f in message.attachments:
				content += ' ' + f.url + '\n'

		if len(content) < 1:
			return

		# send the message
		self.transferred += 1
		await self.__send(message, content, files=message.attachments)

		# no activity timer
		async def silent_callback():
			for w in self.wormholes:
				await w.send(config['no activity message'])
				self.timer = None

		if self.timer:
			self.timer.cancel()
		if config['no activity timeout'] > 0:
			self.timer = Timer(config['no activity timeout']*60, silent_callback)

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

	@commands.check(in_wormhole)
	@commands.group(name="wormhole")
	async def wormhole(self, ctx: commands.Context):
		if ctx.invoked_subcommand is None:
			m = "**{}** messages sent since the formation ({}). " \
				"Connected to **{}** wormholes."
			await ctx.send(m.format(self.transferred, init, len(config['wormholes'])))

	@wormhole.command()
	async def settings(self, ctx: commands.Context):
		m = "**Wormhole settings**: anonymity level **{}**, edit/delete timer **{}s**, "
		m+= "maximal attachment size **{}kB**"
		await ctx.send(m.format(config['anonymity'], config['message window'], config['max size']))

	@wormhole.command()
	async def link(self, ctx: commands.Context):
		"""Send a message with link to the bot"""
		await ctx.send("https://github.com/sinus-x/discord-wormhole")

	@commands.check(is_admin)
	@wormhole.command()
	async def open(self, ctx: commands.Context):
		if ctx.channel.id in config['wormholes']:
			return
		config['wormholes'].append(ctx.channel.id)
		self.__update()
		self.__save()
		await asyncio.sleep(1)
		await self.__send(message=ctx.message, announcement=True,
			text="Wormhole opened: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))

	@commands.check(is_admin)
	@wormhole.command()
	async def close(self, ctx: commands.Context):
		if ctx.channel.id not in config['wormholes']:
			return
		config['wormholes'].remove(ctx.channel.id)
		self.__update()
		self.__save()
		await ctx.send("**Woosh**. The wormhole is gone")
		await self.__send(message=ctx.message, announcement=True,
			text="Wormhole closed: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))

	@commands.check(is_admin)
	@wormhole.command()
	async def anonymity(self, ctx: commands.Context, value: str):
		opts = ['none', 'guild', 'full']
		if value not in opts:
			ctx.send("Options are: " + ', '.join(opts))
		else:
			config['anonymity'] = value
			self.__save()
			await self.__send(message=ctx.message, announcement=True,
				text="New anonymity policy: **{}**".format(value))

	@commands.check(is_admin)
	@wormhole.command()
	async def edittimeout(self, ctx: commands.Context, value: str):
		try:
			value = int(value)
		except:
			return
		if value < 5 or value > 900:
			return
		config['message window'] = value
		self.__save()
		await ctx.send("New message windows: **{} s**".format(value))

	@commands.check(is_admin)
	@wormhole.command()
	async def silenttimeout(self, ctx: commands.Context, value: str):
		try:
			value = int(value)
		except:
			return
		if value < 0:
			value = 0
		config['no activity timeout'] = value
		self.__save()
		await ctx.send("New 'no activity' timeout: **{} min**".format(value))

	@commands.check(is_admin)
	@wormhole.command()
	async def silentmessage(self, ctx: commands.Context, *args):
		value = ' '.join(args)
		config['no activity message'] = value
		self.__save()
		await ctx.send("New 'no activity' message:\n> {}".format(value))

	@commands.check(is_admin)
	@wormhole.command()
	async def size(self, ctx: commands.Context, value: str):
		try:
			value = int(value)
		except:
			return
		if value < 10 or value > 10000:
			return
		config['max size'] = value
		self.__save()
		await ctx.send("New maximal attachment size: **{} kB**".format(value))

	@commands.check(is_admin)
	@wormhole.command()
	async def replace(self, ctx: commands.Context, value: str):
		if value == 'true':
			v = True
		elif value == 'false':
			v = False
		else:
			return
		config['replace original'] = v
		self.__save()
		await ctx.send(f"Try to replace original messages: **{value}**")

	@commands.check(in_wormhole)
	@commands.command()
	async def wormholes(self, ctx: commands.Context):
		if len(self.wormholes) == 0:
			self.__update()
			await asyncio.sleep(1)

		if len(self.wormholes) == 0:
			m = "No wormhole has been opened."
		else:
			m = "Currently opened wormholes:"
			for w in self.wormholes:
				m += "\n- **{}** in {}".format(w.name, w.guild.name)
		await ctx.send(m)

	@commands.check(is_admin)
	@wormhole.command()
	async def say(self, ctx: commands.Context, *args):
		"""Say as a wormhole"""
		m = ' '.join(args)

		a = config['anonymity']
		if a == 'guild' or a == 'none':
			content = f'**WORMHOLE**: {m}'
		await self.__send(ctx.message, text=m, announcement=True)

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
				channel = ch.guild.name + ":" + ch.name
			except:
				channel = "unknown-channel"
			content = content.replace(c, channel)

		# apply anonymity option
		a = config.get('anonymity')
		u = discord.utils.escape_markdown(message.author.name)
		g = discord.utils.escape_markdown(message.guild.name)
		if a == 'none':
			content = f'**{u}, {g}**: ' + content
		elif a == 'guild':
			g = discord.utils.escape_mentions(message.guild.name)
			content = f'**{g}**: ' + content
		elif a == 'all':
			pass

		# done
		content = content.replace("@", "")
		return content

	async def __send(self, message: discord.Message, text: str, files: list = None,
					 announcement: bool = False):
		# if the bot has 'Manage messages' permission, remove original
		if config['replace original'] and not files:
			try:
				await message.delete()
				announcement = True
			except discord.Forbidden:
				pass

		# redistribute the message
		msgs = [message]
		for w in self.wormholes:
			if w.id == message.channel.id and not announcement:
				continue
			m = await w.send(content=text)
			msgs.append(m)

		if announcement:
			return

		self.sent.append(msgs)
		await asyncio.sleep(config['message window'])
		self.sent.remove(msgs)


	def __update(self):
		self.wormholes = []
		for w in config['wormholes']:
			self.wormholes.append(self.bot.get_channel(w))

	def __save(self):
		with open('config.json', 'w', encoding='utf-8') as f:
			json.dump(config, f, ensure_ascii=False, indent=4)

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
