# Overview

Wormhole is independent Discord bot, designed to connect mutiple guilds with one unified chat.


## Articles

- [Setup](setup.md)
- [Using the bot](commands.md)
- [Administration](administration.md)
- [The code](code.md)

## Principle

The wormholes are connected with beams, bot can have multiple beams with independent settings. Wormhole can only be registered to one beam.

Users can set their home wormhole. This will allow others to tag them with `((nickname))`.

## I want to host my wormhole

See [setup](setup.md)

## I want to connect my server

Find a Wormhole instance -- most likely on some other server you're in. In your server, prepare a text channel: usually called **#wormhole**, but that's not required.

Send the `invite` command, click the link and pick a guild -- you'll need administrator privileges there.

The next step, activation, can only be done by the Wormhole administrator. If they are not on your server, send them ID (or name) of your wormhole channel.

Every wormhole in the beam, including your new one, will get an announcement.
