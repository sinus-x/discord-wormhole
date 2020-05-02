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
		self.stats = {}
		self.timer = None

	def is_admin(ctx: commands.Context):
		return ctx.author.id == config['admin id']

	def in_wormhole(ctx: commands.Context):
		return ctx.author.id == config['admin id'] \
		or ctx.channel.id in config['wormholes']

	#TODO Add support to manage bot from DMs
	#TODO Download and re-upload images that fit under the limit - and delete them afterwards
	#TODO React with checkmark if message was successfully edited, else with cross
	#TODO Remove admin messages after some delay

	@commands.Cog.listener()
	async def on_message(self, message: discord.Message):
		# do not act if channel is not wormhole channel
		if message.channel.id not in config['wormholes']:
			return

		# do not act if author is bot
		if message.author.bot:
			return

		# do not act if message is bot command
		if message.content.startswith(config['prefix']):
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
		try:
			self.stats[str(message.guild.id)] += 1
		except KeyError:
			self.stats[str(message.guild.id)] = 1
		await self.send(message, content, files=message.attachments)

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
	@commands.command(aliases=["stat", "stats"])
	async def info(self, ctx: commands.Context):
		"""Display information about wormholes"""
		if len(self.wormholes) == 0:
			self.__update()
			await asyncio.sleep(.25)

		if len(self.wormholes) == 0:
			m = "No wormhole has been opened."
		else:
			# get total message count
			total = 0
			for i in self.stats:
				total += self.stats[i]
			m = "Wormhole formation time: **{}**, ping **{:.2f} s**.\n".format(init, self.bot.latency)
			m+= "Currently opened wormholes:"
			for w in self.wormholes:
				# get logo
				try:
					logo = config['aliases'][str(w.guild.id)]
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
				m += f'\n{logo} **{g}** (#{c}): **{cnt}** messages'
		await ctx.send(m)

	@commands.check(in_wormhole)
	@commands.command()
	async def help(self, ctx: commands.Context):
		"""Display help"""
		embed = discord.Embed(title="Wormhole", color=discord.Color.light_grey())
		p = config['prefix']
		embed.add_field(value=f"**{p}e** | **{p}edit**", name="Edit last message")
		embed.add_field(value=f"**{p}d** | **{p}delete**", name="Delete last message")
		embed.add_field(value=f"**{p}info**", name="Connection information")
		embed.add_field(value=f"**{p}settings**", name="Display current settings")
		embed.add_field(value=f"**{p}link**", name="Link to GitHub repository")
		embed.add_field(value=f"**{p}invite**", name="Bot invite link")
		await ctx.send(embed=embed)

	@commands.check(in_wormhole)
	@commands.group(name="wormhole")
	async def wormhole(self, ctx: commands.Context):
		"""Control the wormholes"""
		if ctx.invoked_subcommand is not None:
			return

		await self.help(ctx)

	@commands.check(is_admin)
	@wormhole.command()
	async def open(self, ctx: commands.Context):
		"""Open a wormhole"""
		if ctx.channel.id in config['wormholes']:
			return
		config['wormholes'].append(ctx.channel.id)
		self.__update()
		self.__save()
		await asyncio.sleep(1)
		await self.send(message=ctx.message, announcement=True,
			text="Wormhole opened: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))

	@commands.check(is_admin)
	@wormhole.command()
	async def close(self, ctx: commands.Context):
		"""Close the current wormhole"""
		if ctx.channel.id not in config['wormholes']:
			return
		config['wormholes'].remove(ctx.channel.id)
		self.__update()
		self.__save()
		await ctx.send("**Woosh**. The wormhole is gone")
		await self.send(message=ctx.message, announcement=True,
			text="Wormhole closed: **{}** in **{}**".format(
				ctx.channel.name, ctx.channel.guild.name))
		if len(self.wormholes) == 0:
			self.transferred = 0

	@commands.check(in_wormhole)
	@commands.command(name="delete", aliases=["remove", "d", "r"])
	async def delete(self, ctx: commands.Context):
		"""Delete last sent message"""
		if len(self.sent) == 0:
			return

		for msgs in self.sent[::-1]:
			if isinstance(msgs[0], discord.Member) and ctx.author.id == msgs[0].id \
			or isinstance(msgs[0], discord.Message) and ctx.author.id == msgs[0].author.id:
				try:
					await ctx.message.delete()
				except:
					pass
				for m in msgs:
					try:
						await m.delete()
					except:
						pass
				return

	@commands.check(in_wormhole)
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
				try:
					await ctx.message.delete()
				except:
					pass
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

	@commands.check(in_wormhole)
	@commands.command()
	async def settings(self, ctx: commands.Context):
		m = "**Wormhole settings**: anonymity level **{}**, edit/delete timer **{}s**, "
		m+= "maximal attachment size **{}kB**"
		await ctx.send(m.format(config['anonymity'], config['message window'], config['max size']))

	@commands.check(in_wormhole)
	@commands.command()
	async def link(self, ctx: commands.Context):
		"""Send a message with link to the bot"""
		await ctx.send("https://github.com/sinus-x/discord-wormhole")

	@commands.check(in_wormhole)
	@commands.command()
	async def invite(self, ctx: commands.Context):
		"""Invite the wormhole to your guild"""
		# permissions:
		# - send messages      - attach files
		# - manage messages    - use external emojis
		# - embed links        - add reactions
		l = "https://discordapp.com/oauth2/authorize?client_id=" + str(self.bot.user.id)
		l+= "&permissions=321600&scope=bot"
		await ctx.send(l)

	@commands.check(is_admin)
	@commands.group(name="admin")
	async def admin(self, ctx: commands.Context):
		if ctx.invoked_subcommand is not None:
			return

		embed = discord.Embed(title="Wormhole administration", color=discord.Color.red())
		p = config['prefix']
		pa = config['prefix'] + 'admin'
		embed.add_field(name=f"{pa} anonymity", value="Anonymity level\n_none | guild | full_")
		embed.add_field(name=f"{pa} edittimeout", value="Editing timeout\n_# of seconds_")
		embed.add_field(name=f"{pa} silenttimeout", value="No activity timeout\n_# of minutes_")
		embed.add_field(name=f"{pa} silentmessage", value="No activity message\n_A message_")
		embed.add_field(name=f"{pa} size", value="Max attachment size\n_# of kilobytes_")
		embed.add_field(name=f"{pa} replace", value="Replace user messages?\n_true | false_")

		embed.add_field(name=f"{p}say", value="Say as a wormhole\n_A message_")

		embed.add_field(name=f"{p}alias <guild id> [set|unset] [emote]", value="Guild prefix")
		await ctx.send(embed=embed)

	@commands.check(is_admin)
	@admin.command()
	async def anonymity(self, ctx: commands.Context, value: str):
		"""Set anonymity level

		value: [none | guild | full]
		"""
		opts = ['none', 'guild', 'full']
		if value not in opts:
			ctx.send("Options are: " + ', '.join(opts))
		else:
			config['anonymity'] = value
			self.__save()
			await self.send(message=ctx.message, announcement=True,
				text="New anonymity policy: **{}**".format(value))

	@commands.check(is_admin)
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
		config['message window'] = value
		self.__save()
		await self.send("New time limit for message edit/deletion: **{value} s**", announcement=True)

	@commands.check(is_admin)
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
		config['no activity timeout'] = value
		self.__save()
		await ctx.send("New 'no activity' timeout: **{} min**".format(value))

	@commands.check(is_admin)
	@admin.command()
	async def silentmessage(self, ctx: commands.Context, *args):
		"""The content of the message

		value: A message
		"""
		value = ' '.join(args)
		config['no activity message'] = value
		self.__save()
		await ctx.send("New 'no activity' message:\n> {}".format(value))

	@commands.check(is_admin)
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
		config['max size'] = value
		self.__save()
		await self.send("New maximal attachment size: **{} kB**".format(value), announcement=True)

	@commands.check(is_admin)
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
		config['replace original'] = v
		self.__save()
		await self.send(ctx.message, text=f"New replacing policy: **{value}**", announcement=True)

	@commands.check(is_admin)
	@commands.command()
	async def say(self, ctx: commands.Context, *args):
		"""Say as a wormhole

		value: A message
		"""
		m = ' '.join(args)

		a = config['anonymity']
		if a == 'guild' or a == 'none':
			m = f'**WORMHOLE**: {m}'
		await self.send(ctx.message, text=m, announcement=True)

	@commands.check(is_admin)
	@commands.command()
	async def alias(self, ctx: commands.Context, guild: str, key: str, *, value: str = None):
		"""Set guild prefix alias

		guild: Guild ID. Dot (.) to use current guild
		key: [set | unset] 
		value: A new prefix for current guild
		"""
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
			config['aliases'][guild] = None
			self.__save()
			m = f"Alias for guild {guild_obj.name} unset."
		elif key == 'set':
			config['aliases'][guild] = value
			self.__save()
			m = f"New alias for guild **{guild_obj.name}** is: {value}"
		else:
			return

		await asyncio.sleep(.5)
		await self.send(ctx.message, text=m, announcement=True)


	def __getPrefix(self, message: discord.Message):
		"""Get prefix for message"""
		a = config['anonymity']
		u = discord.utils.escape_markdown(message.author.name)
		g = str(message.guild.id)
		if g in config['aliases'] and config['aliases'][g] is not None:
			g = config['aliases'][g]
		else:
			g = discord.utils.escape_markdown(message.guild.name) + ','

		if a == 'none':
			return f'{g} **{u}**: '
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

		# apply prefixes
		prefix = self.__getPrefix(message)
		content = content.split('\n')
		c = ''
		for line in content:
			c += prefix + line + '\n'

		# done
		c = c.replace("@", "")
		return c

	async def send(self, message: discord.Message, text: str, files: list = None, announcement: bool = False):
		msgs = [message]
		# if the bot has 'Manage messages' permission, remove original
		if config['replace original'] and not files:
			try:
				msgs[0] = message.author
				await message.delete()
				announcement = True
			except discord.Forbidden:
				pass

		if len(text) > 1000:
			text = text[:1000]
		# redistribute the message
		for w in self.wormholes:
			if w.id == message.channel.id and not announcement:
				continue
			m = await w.send(content=text)
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
