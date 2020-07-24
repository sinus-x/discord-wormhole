[<< back to home](index.md)

# Commands

Generally, users shouldn't need to do anything to interact with the wormhole. To display available commands, run **help**.

You have to prepend bot's prefix before the command name; you can see it in its presence (Game activity).

**e [text]** (**edit [text]**)

Edit your last message: its text will be replaced with new content. For technical reasons, this command has to be invoked within specified time window after sending the message. Default limit is 60 seconds.

**d** (**delete**)

Delete your last message. For technical reasons, this command has to be invoked within specified time window after sending the message. Default limit is 60 seconds.

**info**

Display information about the current wormhole beam, connected wormholes and their message statistics.

**settings**

Display current settings.

**invite**

Invite link for the bot.

**link**

Link to the Github repository.

## Registering

If the user is registered, they can be tagged with `((nickname))`. Otherwise there aren't any significant benefits; user accounts define both mod permissions and restrictions like read-only access.

**register**

That's it. If the user sent the message to a wormhole, that wormhole will become their home. If the user used DMs, home is not set.

**set home**

Set home wormhole. This has to be invoked inside of a valid wormhole channel.

**set name [name]**

Set new nickname. Some characters are disallowed (`()*/\@`, as well as some zero-width characters).

**me**

Display your information.

**whois [name]**

Display information about some user. If the user is found, it will show their home wormhole and optional attributes like mod or readonly status.

[<< back to home](index.md)
