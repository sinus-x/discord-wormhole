# Wormhole
A discord bot to connect multiple guilds.

<p align="center">
  <!-- Build status -->
  <a href="https://github.com/sinus-x/discord-wormhole/actions?query=workflow%3AWormhole"><img src="https://github.com/sinus-x/discord-wormhole/workflows/Wormhole/badge.svg?branch=split" alt="Build" /></a>
  <!-- Mantained? -->
  <a href="https://github.com/sinus-x/discord-wormhole/graphs/commit-activity"><img src="https://img.shields.io/badge/Maintained%3F-yes-brightgreen.svg" alt="Maintenance" /></a>
  <!-- License -->
  <a href="https://github.com/sinus-x/discord-wormhole/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-brightgreen.svg" alt="GPLv3 license" /></a>
  <!-- Python version -->
  <img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python 3.7+" />
  <!-- Black -->
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Formatted with Black" /></a>
</p>

Features:

- Various levels of anonymity
- Edit sent messages on all connected servers
- Wormhole aliases (emoji and guild emote support)
- Full control over your data by self-hosting

Required permissions:

- Read messages
- Send messages
- Manage messages
- Use external emojis
- Attach files
- Embed links

## Set up
- Clone the repository
- Install redis: `apt install redis-server`
- Install requirements: `pip3 install -r requirements.txt`
- Create `config.json` file with `config.default.json` as a reference
- Run the bot with `python3 bot.py`

## License
Released under the GNU GPL v3
