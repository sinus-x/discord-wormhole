import asyncio
import json
import git

import discord
from discord.ext import commands

from core import database
from core.database import repo_b, repo_w

#TODO Add support to manage bot from DMs
#TODO Download and re-upload images that fit under the limit - and delete them afterwards
#TODO User aliases
#TODO Use Black for formatting & pre-commit
#TODO Add blacklisting - full and cooldown
#TODO When the message is removed, remove it from sent[], too
#TODO Add reactions
#TODO Specify log channel for each beam

config = json.load(open('config.json'))

async def presence(bot: commands.Bot):
	git_repo = git.Repo(search_parent_directories=True)
	git_hash = git_repo.head.object.hexsha[:7]
	s = f"{config['prefix']}wormhole | " + git_hash
	await bot.change_presence(activity=discord.Game(s))

class Wormcog(commands.Cog):
	def __init__(self, bot):
		super().__init__()
		self.bot = bot

		# active text channels acting as wormholes
		self.wormholes = {}

		# sent messages still held in memory
		self.sent = []

	##
	## FUNCTIONS
	##

	def reconnect(self, beam: str):
		self.wormholes[beam] = []
		for w in repo_w.getByBeam(beam):
			self.wormholes[beam].append(self.bot.get_channel(w.channel))

	def removalDelay(self, key: str = 'user'):
		if key == 'user':
			return 60
		if key == 'admin':
			return 15

	async def send(self, message: discord.Message, beam: database.Beam, text: str, files: list = None, announcement: bool = False):
		"""Distribute the message"""
		msgs = [message]
		# if the bot has 'Manage messages' permission, remove the original
		if beam is not None:
			beam = database.repo_b.get(database.repo_w.get(message.channel.id).beam)
		if beam and beam.replace and not files:
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
		if beam is None:
			ws = self.wormholes.values()
		else:
			ws = self.wormholes[beam.name]
		for w in ws:
			if w.id == message.channel.id and not announcement:
				continue
			m = await w.send(content=text)
			msgs.append(m)

		# save message objects in case of editing/deletion
		if beam.timeout > 0:
			self.sent.append(msgs)
			await asyncio.sleep(beam.timeout)
			self.sent.remove(msgs)

	async def delete(self, message: discord.Message):
		"""Try to delete original message"""
		try:
			await message.delete()
		except:
			return

	def getBeamName(self, message: discord.Message):
		dbw = repo_w.get(message.channel.id)
		print(f"found dbw {dbw.channel} in beam {dbw.beam}")
		return dbw.beam
