# Wormhole

## Overview

Wormhole is independent Discord bot, designed to connect mutiple guilds with one unified chat.

## Setup

The obvious step is registering the bot on the [Discord webpage][developers]. Duck or Google around if you don't know what to do.

Install required tools, clone the repository and install python packages:

```bash
apt install git redis-server python3
git clone git@github.com:sinus-x/discord-wormhole.git wormhole
cd wormhole
pip3 install -r requirements.txt
```

Fill the config file and run the bot with `python3 init.py`. You can set up a systemd service ([like this, for example][systemd]) to do this on server boot.

## Commands

Generally, users shouldn't need to do anything to interact with the wormhole. To display available commands, run **~help**. You can see bot's prefix in its presence (Game activity).

**~e [text]** (**~edit [text]**)

Edit your last message. For technical reasons, full original message will be replaced with the new content, and this command has to be invoked within the defined limit, which is by default 60 seconds.

**~d** (**~delete**)

Delete your last message. For technical reasons, this command has to be invoked within the defined limit, which is by default 60 seconds.

**~info**

Display information about the current wormhole beam, connected wormholes and their message statistics.

**~settings**

Display current settings.

**~invite**

Invite link for the bot.

**~link**

Link to the Github repository.

### Registering

_TODO_

### Moderator commands

_TODO_

## The code

The wormholes are connected with beams. Bot can have multiple beams with independent settings. Wormhole can only be registered to one beam.

Users can set their home wormhole. This will allow others to tag them with `((nickname))`. For technical reasons, user can only be registered to one wormhole, meaning that other's won't be able to tag them from wormholes in another beams.

### Database

[Redis][redis] is in-memory database, allowing fast and easy access to data. Unlike traditional databases like MySQL or Postgres, it has no concept of tables and objects; information is stored under a semicolon separated keys, while the value can be a string or number.

```
127.0.0.1:6379> set foo:bar baz
OK
127.0.0.1:6379> get foo:bar
"baz"
127.0.0.1:6379> del foo:bar
(integer) 1
```

Wormhole uses `type:identifier:attribute` style: `beam:main:admin_id`.

```python
from core.database import repo_b, repo_w, repo_u

wormhole = repo_w.get(message.channel.id)
beam = repo_b.get(wormhole.beam)
user = repo_u.get(message.author.id)
```

### Contributing

All issues, bug or functionality submissions are welcome.

Please, [file an issue][issues] before sending an PR.


[developers]: https://discord.com/developers
[issues]: https://github.com/sinus-x/discord-wormhole/issues
[redis]: https://redis.io
[systemd]: https://github.com/sinus-x/rubbergoddess/blob/master/resources/systemd.standalone.service