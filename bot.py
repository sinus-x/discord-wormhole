import json
import git
import traceback
from datetime import datetime

import discord
from discord.ext import commands

config = json.load(open('config.json'))
bot = commands.Bot(command_prefix=config['prefix'], help_command=None)


"""
NOTE:

This master branch is frozen. Only bugfixes will be merged.

Development is focused on `split` branch, which is for now considered unstable
and may change in following weeks.
"""

@bot.event
async def on_ready():
	print("Ready at " + datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
	git_repo = git.Repo(search_parent_directories=True)
	git_hash = git_repo.head.object.hexsha[:7]
	s = f"{config['prefix']}wormhole | " + git_hash
	await bot.change_presence(activity=discord.Game(s))

@bot.event
async def on_error(event, *args, **kwargs):
	if config['suppress errors']:
		return

	output = traceback.format_exc()
	print(output)

@bot.command()
async def reload(ctx: commands.Context):
	"""Reload the wormhole"""
	if ctx.author.id != config['admin id']:
		return
	try:
		bot.reload_extension('wormhole')
		await ctx.send('Reloaded.')
	except Exception:
		await ctx.send('An error occured. RIP.')

bot.load_extension('wormhole')
bot.run(config.get('bot key'))
