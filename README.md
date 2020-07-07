# Wormhole
A discord bot to connect multiple guilds.

<p align="center">
  <!-- Discord -->
  <a href="https://discord.com/invite/9N3cP2E">
    <img src="https://img.shields.io/badge/Home%20guild-VUT%20FEKT-success?style=flat-square" alt="VUT FEKT" />
  </a>
  <!-- Build status -->
  <a href="https://github.com/sinus-x/discord-wormhole/actions?query=workflow%3AWormhole">
    <img src="https://img.shields.io/github/workflow/status/sinus-x/discord-wormhole/Wormhole/redis?style=flat-square" alt="Build" />
  </a>
  <!-- Mantained? -->
  <a href="https://github.com/sinus-x/discord-wormhole/graphs/commit-activity">
    <img src="https://img.shields.io/badge/mantained-yes-success?style=flat-square" alt="Mantained" />
  </a>
</p>
<p align="center">
  <!-- License -->
  <a href="https://github.com/sinus-x/discord-wormhole/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-GPLv3-success?style=flat-square" alt="GPLv3 license" />
  </a>
  <!-- Python version -->
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python 3.7+" />
  <!-- Black -->
  <a href="https://github.com/psf/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000?style=flat-square" alt="Formatted with Black" />
  </a>
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
