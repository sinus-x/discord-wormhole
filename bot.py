import json
import traceback
from datetime import datetime

import discord
from discord.ext import commands

config = json.load(open('config.json'))
bot = commands.Bot(command_prefix=config['prefix'], help_command=None)

@bot.event
async def on_ready():
	print("Ready at " + datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
	s = f"{config['prefix']}wormhole"
	await bot.change_presence(activity=discord.Game(s))

@bot.event
async def on_error(event, *args, **kwargs):
	if config['supress errors']:
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
