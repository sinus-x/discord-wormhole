import re
import json
import asyncio
import io
import copy

import discord
from discord.ext import commands

config = json.load(open('config.json'))

class Wormhole(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		self.wormholes = []
		self.sent = []

		self.transferred = 0

	def is_admin(ctx: commands.Context):
		return ctx.author.id == config['admin id']

	def in_wormhole(ctx: commands.Context):
		return ctx.author.id == config['admin id'] \
		or ctx.channel.id in config['wormholes']

	#TODO Add support to manage bot from DMs
	#TODO Add prefix to wormhole management messages

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
		content = None
		files = []
		if message.content:
			content = self.__process(message)

		if message.attachments:
			for f in message.attachments:
				if not 0 <= f.size < config['max size']*1000:
					await message.channel.send(
						"{}, that file is too big.".format(message.author.mention))
					continue
				fp = io.BytesIO()
				await f.save(fp)
				files.append(discord.File(fp, filename=f.filename))

		if content is None and files is None:
			return

		# send the message
		self.transferred += 1
		await self.__send(message, content, files)

	@commands.Cog.listener()
	async def on_message_edit(self, before: discord.Message, after: discord.Message):
		"""If the message was sent in 'message window' seconds, edit it"""
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
		"""If the message was sent in 'message window' seconds, delete it"""
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
			m = "**{}** messages sent since the formation. " \
				"Connected to **{}** wormholes."
			await ctx.send(m.format(self.transferred, len(config['wormholes'])))

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
				ctx.channel.name, ctx.channel.guild.name), files=None)

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
				ctx.channel.name, ctx.channel.guild.name), files=None)

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
				text="New anonymity policy: **{}**".format(value), files=None)


	@commands.check(is_admin)
	@wormhole.command()
	async def timer(self, ctx: commands.Context, value: str):
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
		return content.replace("@", "")

	async def __send(self, message: discord.Message, text: str, files: list,
						   announcement: bool = False):
		"""Redistribute the message under guild's name"""
		msgs = [message]
		for w in self.wormholes:
			if w.id == message.channel.id and not announcement:
				continue
			whs = await w.webhooks()
			#TODO Save webhook alongside the channel object
			wh = discord.utils.get(whs, name='Wormhole')
			if wh is None:
				wh = await w.create_webhook(name='Wormhole', adapter=AsyncWebhookAdapter())

			a = config['anonymity']
			if a == 'guild' and not announcement:
				m = await wh.send(text, files=files,
					username=message.guild.name,
					avatar_url=message.guild.icon_url)
			elif a == 'none' and not announcement:
				m = await wh.send(text, files=files,
					username=message.author.name,
					avatar_url=message.author.avatar_url)
			else:
				m = await w.send(text, files=copy.deepcopy(files))
			msgs.append(m)

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


def setup(bot):
	bot.add_cog(Wormhole(bot))
