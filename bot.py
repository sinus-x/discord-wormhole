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
	#TODO set presence

@bot.event
async def on_error(event, *args, **kwargs):
	if config['supress errors']:
		return

	output = traceback.format_exc()
	print(output)

bot.load_extension('wormhole')
bot.run(config.get('bot key'))
