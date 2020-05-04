import asyncio
import json
import re
from datetime import datetime
from io import BytesIO

import discord
from discord.ext import commands

import init, wormcog

class Edit(wormcog.Wormcog):
	"""Configuration"""
	def __init__(self, bot):
		super().__init__(bot)

	@commands.check(init.is_admin)
	@commands.group(name="admin")
	async def admin(self, ctx: commands.Context):
		if ctx.invoked_subcommand is not None:
			return

		embed = discord.Embed(title="Wormhole administration", color=discord.Color.red())
		p = self.config['prefix']
		pa = self.config['prefix'] + 'admin'
		embed.add_field(name=f"{p}wormhole open", value="Open wormhole in current channel", inline=False)
		embed.add_field(name=f"{p}wormhole close", value="Close wormhole in current channel", inline=False)
		embed.add_field(name=f"{pa} anonymity", value="Anonymity level\n_none | guild | full_")
		embed.add_field(name=f"{pa} edittimeout", value="Editing timeout\n_# of seconds_")
		embed.add_field(name=f"{pa} silenttimeout", value="No activity timeout\n_# of minutes_")
		embed.add_field(name=f"{pa} silentmessage", value="No activity message\n_A message_")
		embed.add_field(name=f"{pa} size", value="Max attachment size\n_# of kilobytes_")
		embed.add_field(name=f"{pa} replace", value="Replace user messages?\n_true | false_")

		embed.add_field(name=f"{p}say", value="Say as a wormhole\n_A message_")

		embed.add_field(name=f"{p}alias <guild id> [set|unset] [emote]", value="Guild prefix")
		await ctx.send(embed=embed, delete_after=self.removalDelay('admin'))
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def anonymity(self, ctx: commands.Context, value: str):
		"""Set anonymity level

		value: [none | guild | full]
		"""
		opts = ['none', 'guild', 'full']
		if value not in opts:
			await ctx.send("> Options are: " + ', '.join(opts))
		else:
			self.config['anonymity'] = value
			print(value)
			self.confSave()
			await self.send(message=ctx.message, announcement=True,
				text="> New anonymity policy: **{}**".format(value))
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def edittimeout(self, ctx: commands.Context, value: str):
		"""Time period for keeping sent messages in memory, in seconds

		value: # of seconds
		"""
		try:
			value = int(value)
		except:
			return
		if value < 5 or value > 900:
			return
		self.config['message window'] = value
		self.confSave()
		await self.send("> New time limit for message edit/deletion: **{value} s**", announcement=True)
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def silenttimeout(self, ctx: commands.Context, value: str):
		"""Time period, after which the wormhole should send a message
		
		value: # of minutes, zero to disable
		"""
		try:
			value = int(value)
		except:
			return
		if value < 0:
			value = 0
		self.config['no activity timeout'] = value
		self.confSave()
		await ctx.send("> New 'no activity' timeout: **{} min**".format(value))
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def silentmessage(self, ctx: commands.Context, *args):
		"""The content of the message

		value: A message
		"""
		value = ' '.join(args)
		self.confSet('no activity message', value)
		self.confSave()
		await ctx.send("> New 'no activity' message:\n> {}".format(value))
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def size(self, ctx: commands.Context, value: str):
		"""Maximal size for attachments
	
		value: # of kilobytes
		"""
		try:
			value = int(value)
		except:
			return
		if value < 10 or value > 10000:
			return
		self.confSet('max size', value)
		self.confSave()
		await self.send("> New maximal attachment size: **{} kB**".format(value), announcement=True)
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@admin.command()
	async def replace(self, ctx: commands.Context, value: str):
		"""Whether to replace original messages
	
		value: [true | false]
		"""
		if value == 'true':
			v = True
		elif value == 'false':
			v = False
		else:
			return
		self.confSet('replace original', v)
		self.confSave()
		await self.send(ctx.message, text=f"> New replacing policy: **{value}**", announcement=True)
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@commands.command()
	async def say(self, ctx: commands.Context, *, text: str):
		"""Say as a wormhole

		value: A message
		"""
		a = self.config['anonymity']
		await self.send(ctx.message, text=text, announcement=True)
		await self.delete(ctx.message)

	@commands.check(init.is_admin)
	@commands.command()
	async def alias(self, ctx: commands.Context, guild: str, key: str, *, value: str = None):
		"""Set guild prefix alias

		guild: Guild ID. Dot (.) to use current guild
		key: [set | unset] 
		value: A new prefix for current guild
		"""
		await self.delete(ctx.message)
		try:
			guild_id = int(guild)
			guild_obj = self.bot.get_guild(guild_id)
		except:
			if guild == '.':
				guild_id = ctx.guild.id
				guild_obj = ctx.guild
				guild = str(guild_id)
			else:
				return

		if key == 'unset':
			self.confSet('aliases', guild, None)
			self.confSave()
			m = f"> Alias for guild {guild_obj.name} unset."
		elif key == 'set':
			self.confSet('aliases', guild, value)
			self.confSave()
			m = f"> New alias for guild **{guild_obj.name}** is: {value}"
		else:
			return

		await asyncio.sleep(.5)
		await self.send(ctx.message, text=m, announcement=True)


def setup(bot):
	bot.add_cog(Edit(bot))
