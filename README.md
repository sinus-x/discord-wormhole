# Wormhole
A simple discord bot to connect multiple guilds.

Features:

- Display author and source guild OR just the source guild OR just the message
- Edit sent messages on all connected servers
- Use custom emotes instead of guild names
- Full control over your data by hosting it on your own server

Required permissions:

- Read messages
- Send messages
- Manage messages
- Use external emojis
- Attach files
- Embed links

## Set up
- Clone the repository
- Create `config.json` file with `config.default.json` as a reference
- Run the bot with `python3 bot.py`

## Management
Commands:

- `~e` Edit last message

- `~d` Delete last message

- `~info` Connection information

- `~settings` Display current settings

- `~link` Link to GitHub repository

- `~invite` Bot invite link


Admin commands:
- `~wormhole open`: Open new wormhole in current channel

- `~wormhole close`: Close the wormhole in current channel

- `~admin anonymity [none|guild|full]` Anonymity level

- `~admin edittimeout [# of seconds]` Editing timeout

- `~admin silenttimeout [# of minutes]` No activity timeout

- `~admin silentmessage [text]` No activity message

- `~admin size [# of kB]` Maximal attachment size

- `~admin replace [true|false]` Replace user messages?

- `~alias <guild id> [set|unset] [emote]` Change guild prefix

- `~say [text]` Say as a wormhole

## License
Released under the GNU GPL v3
