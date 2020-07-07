[<< back to home](index.md)

# Code

## Contributing

All issues, bug or functionality submissions are welcome.

Please, [file an issue][issues] or join our Discord server (linked in README) before sending an PR.

## Database

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

[issues]: https://github.com/sinus-x/discord-wormhole/issues
[redis]: https://redis.io
