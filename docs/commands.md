[<< back to home](index.md)

# Commands

Generally, users shouldn't need to do anything to interact with the wormhole. To display available commands, run **help**. You can see bot's prefix in its presence (Game activity).

**e [text]** (**edit [text]**)

Edit your last message. For technical reasons, full original message will be replaced with the new content, and this command has to be invoked within the defined limit, which is by default 60 seconds.

**d** (**delete**)

Delete your last message. For technical reasons, this command has to be invoked within the defined limit, which is by default 60 seconds.

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

[<< back to home](index.md)
