# Wormhole

<p align="center">
  <a href="https://github.com/sinus-x/discord-wormhole/graphs/commit-activity">
    <img src="https://img.shields.io/badge/maintained-no-critical?style=flat-square" alt="Maintained" />
  </a>
  <a href="https://github.com/sinus-x/discord-wormhole/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-GPLv3-blue?style=flat-square" alt="GPLv3 license" />
  </a>
  <img src="https://img.shields.io/badge/discord.py-1.7.3-blue?style=flat-square" alt="discord.py 1.7.3" />
  <img src="https://img.shields.io/badge/python-3.7+-blue?style=flat-square" alt="Python 3.7+" />
</p>


*Update 2021-04-27: I don't have time for the development anymore. The bot still works, but no new features are being added.*

*Update 2021-11-22: The production instance has been shut down. As no further development is planned, the repository was archived.*

---

A Discord bot able to connect multiple guilds with one shared chat.

Features:

- Various levels of anonymity
- Edit sent messages on all connected servers
- Guild aliases (emoji and guild emote support)
- Full control over your data

Required permissions:

- Read messages
- Send messages
- Manage messages
- Use external emojis
- Embed links

## Set up
- Clone the repository
- Install redis: `apt install redis-server`
- Install requirements: `pip3 install -r requirements.txt`
- Create `config.json` file with `config.default.json` as a reference
- Run the bot with `python3 init.py`

## Development

Issues and PRs are welcome -- maybe let me know before you start working on something.

All pull requests should be targeted to the `devel` branch.

## Contributors

- [CrafterSvK](https://github.com/CrafterSvK): parallel message sending, variable name unification (v0.2)
- [jirkavrba](https://github.com/jirkavrba): character `&` is not escaped (pre-v0.1)

## License
Released under the GNU GPL v3.
