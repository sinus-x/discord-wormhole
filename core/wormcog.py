import asyncio
import json
import git

import discord
from discord.ext import commands

from core.database import repo_w, repo_u, repo_s

#TODO Add support to manage bot from DMs
#TODO Download and re-upload images that fit under the limit - and delete them afterwards
#TODO User aliases
#TODO Use Black for formatting & pre-commit
#TODO Add blacklisting - full and cooldown
#TODO When the message is removed, remove it from sent[], too
#TODO Add reactions

async def presence(bot: commands.Bot, prefix: str, messages: int = None):
	git_repo = git.Repo(search_parent_directories=True)
	git_hash = git_repo.head.object.hexsha[:7]
	if messages:
		s = f"{prefix}wormhole | {messages} | " + git_hash
	else:
		s = f"{prefix}wormhole | " + git_hash
	await bot.change_presence(activity=discord.Game(s))

class Wormcog(commands.Cog):
	def __init__(self, bot):
		super().__init__()
		self.bot = bot
		self.config = json.load(open('config.json'))

		# active text channels acting as wormholes
		self.wormholes = []

		# sent messages still held in memory
		self.sent = []

	##
	## FUNCTIONS
	##

	def wormholesUpdate(self):
		self.wormholes = []
		for wormhole in repo_w.getAll():
			self.wormholes.append(self.bot.get_channel(wormhole.id))

	def removalDelay(self, key: str = 'user'):
		if key == 'user':
			return 60
		if key == 'admin':
			return 15

	def confGet(self, key: str):
		"""Get value from config"""
		try:
			return self.config[key]
		except KeyError:
			raise

	def confSet(self, *args):
		"""Set value in config"""
		if len(args) == 2:
			self.config[args[0]] = args[1]
		elif len(args) == 3:
			self.config[args[0]][args[1]] = args[2]

	def confAdd(self, *args):
		if len(args) == 2:
			self.config[args[0]].append(args[1])
		elif len(args) == 3:
			self.config[args[0]][args[1]].append(args[2])

	def confDel(self, *args):
		if len(args) == 2:
			self.config[args[0]].remove(args[1])
		elif len(args) == 3:
			self.config[args[0]][args[1]].remove(args[2])
	
	def confSave(self):
		"""Save config"""
		with open('config.json', 'w', encoding='utf-8') as c:
			json.dump(self.config, c, ensure_ascii=False, indent=4)

	async def send(self, message: discord.Message, text: str, files: list = None, announcement: bool = False):
		"""Distribute the message"""
		msgs = [message]
		# if the bot has 'Manage messages' permission, remove the original
		if self.confGet('replace original') and not files:
			try:
				msgs[0] = message.author
				await self.delete(message)
				announcement = True
			except discord.Forbidden:
				pass

		# limit message length
		if len(text) > 1000:
			text = text[:1000]

		# distribute the message
		for w in self.wormholes:
			if w.id == message.channel.id and not announcement:
				continue
			m = await w.send(content=text)
			msgs.append(m)

		# save message objects in case of editing/deletion
		self.sent.append(msgs)
		await asyncio.sleep(self.confGet('message window'))
		self.sent.remove(msgs)

	async def delete(self, message: discord.Message):
		"""Try to delete original message"""
		try:
			await message.delete()
		except:
			return
