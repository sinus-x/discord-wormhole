# CHANGELOG

Small fixes are not listed. See diffs for each version to see details.

## [unreleased]

## [0.2.3]

- `block` command ([PR-67] by [AlejandroGomezFrieiro])
- `spy messages` command

## [0.2.2]

- Bump discord.py to 1.5.0, use Intents

## [0.2.1]

- `announce` command
- Default prefix set to `+`
- Make `@` escaping transparent
- Fix wormhole to string function
- Remove hash from presence

## [0.2.0]

- Force registration in Wormhole
- Direct messages and non-wormhole errors are preserved
- `info` is sorted by count and is callable in DM
- Announcements are embeds, so they stand out
- Messages are sent at the same time ([PR-48] by [CrafterSvK])
- User list can be filtered by attribute and is sorted by nickname
- Wormholes are sorted by message count in public interface
- Discord tags are translated to Wormhole tags
- If the message is not replicated, checkmark reaction is added on success

## [0.1.1]

- Direct messages and non-wormhole errors are not self-deleted
- Info command is sorted by message count and is callable in DM
- Announcements are embeds, so they stand out more

## [0.1.0]

- Bump discord.py version to 1.4.0
- Check for user home before loading it (#19)
- Feedback on wormhole creation & removal
- Warnings on failed send/edit

<!-- Versions -->
[unreleased]: https://github.com/sinus-x/discord-wormhole/compare/v0.2.3...devel
[0.2.2]: https://github.com/sinus-x/discord-wormhole/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/sinus-x/discord-wormhole/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/sinus-x/discord-wormhole/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/sinus-x/discord-wormhole/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/sinus-x/discord-wormhole/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/sinus-x/discord-wormhole/releases/tag/v0.1.0

<!-- Descriptions -->
[PR-48]: https://github.com/sinus-x/discord-wormhole/pull/48
[PR-67]: https://github.com/sinus-x/discord-wormhole/pull/67
[CrafterSvK]: https://github.com/CrafterSvK
[AlejandroGomezFrieiro]: https://github.com/AlejandroGomezFrieiro
