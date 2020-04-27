import os
import json
from io import BytesIO
import asyncio

import discord
from discord.ext import commands

config = json.load(open('config.json'))

class Wormhole(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		self.wormholes = []
		self.transferred = 0

	def is_admin(ctx: commands.Context):
		return ctx.author.id == config['admin id']

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

		content = None
		files = []

		# copy remote message
		if message.content:
			a = config.get('anonymity')
			u = discord.utils.escape_mentions(message.author.name)
			g = discord.utils.escape_mentions(message.guild.name)
			if a == 'none':
				content = f'**{u}, {g}**: ' + message.content
			elif a == 'guild':
				g = discord.utils.escape_mentions(message.guild.name)
				content = f'**{g}**: ' + message.content
			else:
				content = message.content

		if message.attachments:
			for f in message.attachments:
				fp = BytesIO()
				await f.save(fp)
				files.append(discord.File(fp, filename=f.filename))

		# send the message
		self.transferred += 1
		await self.__send(message, content, files)



	@commands.group(name="wormhole")
	async def wormhole(self, ctx: commands.Context):
		if ctx.invoked_subcommand is None:
			m = "**{}** messages sent since the first formation."
			await ctx.send(m.format(self.transferred))

	@commands.check(is_admin)
	@wormhole.command()
	async def add(self, ctx: commands.Context, channel: discord.TextChannel):
		config['wormholes'].append(channel.id)
		self.__update()
		self.__save()
		await asyncio.sleep(1)
		await self.__send(ctx=ctx, source=True,
			text="Wormhole opened: **{}** in **{}**".format(
				channel.name, channel.guild.name), files=None)

	@commands.check(is_admin)
	@wormhole.command(aliases=["delete"])
	async def remove(self, ctx: commands.Context, channel: discord.TextChannel):
		config['wormholes'].remove(channel.id)
		self.__update()
		self.__save()
		await self.__send(ctx=ctx, source=True,
			text="Wormhole closed: **{}** in **{}**".format(
				channel.name, channel.guild.name), files=None)

	@commands.check(is_admin)
	@wormhole.command()
	async def anonymity(self, ctx: commands.Context, value: str):
		opts = ['none', 'guild', 'full']
		if value not in opts:
			ctx.send("Options are: " + ', '.join(opts))
		else:
			config['anonymity'] = value
			self.__save()
			await self.__send(ctx=ctx, source=True,
				text="New anonymity policy: **{}**".format(value), files=None)

	async def __send(self, ctx: commands.Context, text: str, files: list, source: bool = False):
		# redistribute the message
		for w in self.wormholes:
			if w.id == ctx.channel.id and not source:
				continue
			await w.send(content=text, files=files)

	def __update(self):
		self.wormholes = []
		for w in config['wormholes']:
			self.wormholes.append(self.bot.get_channel(w))

	def __save(self):
		with open('config.json', 'w', encoding='utf-8') as f:
			json.dump(config, f, ensure_ascii=False, indent=4)


def setup(bot):
	bot.add_cog(Wormhole(bot))
