[<< back to home](index.md)

# Administration

The **Admin cog** allows the bot administrator to manage beams, wormholes and users.

## Beam

There can be multiple independent shared chats. These chats, called beams, may have multiple wormholes connected to them. Wormhole can only be connected to one beam.

Invoker has to be bot administrator in order to edit these settings.

### Beam settings

| Key       | Value            | Description                               |
|-----------|------------------|-------------------------------------------|
| active    | **1**, 0         | Whether the beam should transfer messages |
| admin_id  | **0**, _user ID_ | Pingable user account in case of problems |
| anonymity | **none**, guild, full | Anonymity level for names            |
| replace   | **1**, 0         | Whether to replace original messages      |
| timeout   | 60               | Time interval in seconds, in which the bot holds original messages in memory. This is used for editing and removing sent messages. |

### Beam commands

**beam add [name]**

Creates new beam and opens it. The name must be unique and has to match `[a-zA-Z0-9_]+` pattern.

**beam open [name]**

Open previously closed beam. This will allow messages to be sent.

_This is an alias for **beam set [name] active 1**._

**beam close [name]**

Close previously opened beam. This will block all messages from being sent.

_This is an alias for **beam set [name] active 0**._

**beam set [name] [key] [value]**

Alter beam settings. See the table above for available options.

**beam list**

List opened beams

## Wormhole

Each wormhole is a text channel in some guild, connected to specified beam.

Invoker has to be bot administrator in order to edit these settings.

### Wormhole settings

| Key       | Value            | Description                               |
|-----------|------------------|-------------------------------------------|
| beam      | _beam name_      | Beam the wormhole is connected to         |
| admin_id  | **0**, _user ID_ | Pingable user account in case of problems |
| active    | **1**, 0         | Whether the wormhole should transfer messages. This will not override beam settings. |
| logo      | _string_         | String, displayed instead of the guild name. Guild emojis are supported. |
| readonly  | **0**, 1         | Do not send messages, just recieve them   |
| messages  | _integer_        | Number of messages the wormhole has sent  |

### Wormhole commands

**wormhole add [beam name] [channel ID]**

Add current text channel as new wormhole to specified beam. If the channel ID is omitted, current channel is used.

**wormhole remove [channel ID]**

Remove current wormhole. If the channel ID is omitted, current channel is used.

**wormhole set [channel ID] [key] [value]**

Alter wormhole settings. See the table above for available options.

**wormhole list**

List beams and their wormholes.


## User

Users can register their accounts if they want to be able to be tagged or to have their home wormhole linked to them.

Invoker has to be mod or bot administrator in order to edit these settings.

### User settings

| Key                  | Value           | Description                                  |
|----------------------|-----------------|----------------------------------------------|
| home_id:[beam name]  | _channel ID_, 0 | Wormhole text channel. There is an entry for every beam the user is registered in. |
| mod                  | **0**, 1        | Whether they are mod                         |
| nickname             | _string_        | Display name. Default is their Discord name. |
| readonly             | **0**, 1        | Ignore their messages                        |
| restricted           | **0**, 1        | Wheter they should be disallowed to alter their nickname and home wormhole |

### User commands

**user add [member ID] [nickname] [home wormhole ID]**

Add new user to database. Member must not exist in database, nickname must not be already used, home wormhole must exist.

**user remove [member ID]**

Remove user from database.

**user set [member ID] [key] [value]**

Alter user's settings. See the table above for available options.

**user list**

List users and their parameters. Note that this output may be huge, depending on number of registered users.

[<< back to home](index.md)
