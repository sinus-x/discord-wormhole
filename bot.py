import json
import traceback

import discord
from discord.ext import commands

config = json.load(open('config.json'))

bot = commands.Bot(command_prefix=config['prefix'], help_command=None)

@bot.event
async def on_ready():
	print("Ready")
	#TODO set presence

@bot.event
async def on_error(event, *args, **kwargs):
	return

bot.load_extension('wormhole')

bot.run(config.get('bot key'))
