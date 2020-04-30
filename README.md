# Wormhole
A simple discord bot to connect multiple guilds.

## Set up
- Clone the repository
- Create `config.json` file with `config.default.json` as a reference
- Run the bot with `python3 bot.py`

## Management
Commands:
- `~wormhole` Print session information
- `~wormholes` Display information about opened wormholes
- `~wormhole settings` Display public settings
- `~wormhole link` Link to the github repository

Admin commands:
- `~wormhole open` Open wormhole in current channel
- `~wormhole close` Close wormhole in current channel
- `~wormhole say [text]` Say something as wormhole
- `~wormhole anonymity [none|guild|full]` will change the presentation of incoming messages
- `~wormhole size [int]` Change maximal size of attachments, in kB
- `~wormhole replace [true|false]` Replace original messages? (Makes editing impossible)
- `~wormhole edittimeout [int (s)]` Change edit countdown timer
- `~wormhole silenttimeout [int (min)]` When to send a message declaring no activity. `0` to disable
- `~wormhole silentmessage [text]` What to say on timeout

## License
Released under the GNU GPL v3
