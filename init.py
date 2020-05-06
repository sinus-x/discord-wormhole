import json
import traceback
from datetime import datetime

import discord
from discord.ext import commands

from core import wormcog

config = json.load(open('config.json'))
bot = commands.Bot(command_prefix=config['prefix'], help_command=None)


##
## CHECKS
##

def is_admin(ctx: commands.Context):
	return ctx.author.id == config['admin id']

def is_mod(ctx: commands.Context):
	return

def in_wormhole(ctx: commands.Context):
	return ctx.author.id == config['admin id'] \
	or ctx.channel.id in config['wormholes']

##
## EVENTS
##

@bot.event
async def on_ready():
	print("Ready at " + datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
	await wormcog.presence(bot)

@bot.event
async def on_error(event, *args, **kwargs):
	if config['suppress errors']:
		return

	output = traceback.format_exc()
	print(output)

##
## COMMANDS
##

@bot.command()
async def reload(ctx: commands.Context, cog: str):
	"""Reload the wormhole"""
	if ctx.author.id != config['admin id']:
		return
	try:
		bot.reload_extension(f'cogs.{cog}')
		m = f'**{cog}** reloaded.'
		print(m)
		await ctx.send(m)
	except Exception:
		await ctx.send('An error occured. RIP.')

##
## INIT
##

for c in ['wormhole', 'admin']:
	bot.load_extension(f'cogs.{c}')
	print(f'{c.upper()} loaded')

bot.run(config.get('bot key'))
