[<< back to home](index.md)

# Setup

The obvious step is registering the bot on the [Discord webpage][developers]. Duck or Google around if you don't know what to do.

Install required tools, clone the repository and install python packages:

```bash
apt install git redis-server python3
git clone git@github.com:sinus-x/discord-wormhole.git wormhole
cd wormhole
pip3 install -r requirements.txt
```

Fill the config file and run the bot with `python3 init.py`. To get the wormhole to work, you must create beam and open wormholes; see [administration](administration.md).

## Systemd

You probably want to have your bot started as soon as the server is booted. Edit the example below it so it matches your setup.

```
[Unit]
Description=Wormhole Discord bot
After=multi-user.target

[Service]
Restart=on-failure
User=wormhole
StandardOutput=journal+console

WorkingDirectory=/home/wormhole/wormhole
ExecStart=python3 init.py

[Install]
WantedBy=multi-user.target
```

Copy the file to `/etc/systemd/system/wormhole.service` and run

```sh
sudo systemctl enable wormhole.service
sudo systemctl start wormhole.service
```

[<< back to home](index.md)


[developers]: https://discord.com/developers
[systemd]: https://github.com/sinus-x/rubbergoddess/blob/master/resources/systemd.standalone.service
