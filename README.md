José
=========

*The documentation for José is available in English as well as in Portuguese*

*Este arquivo em português pode ser encontrado em [README-pt.md](https://github.com/lkmnds/jose/blob/master/README-pt.md)*

José is a general-purpose bot for Discord written in Python.

**Redis and Python 3.5+ is needed**

Instructions for Linuxes:
```bash
$ git clone https://github.com/lkmnds/jose.git
$ cd jose
$ nano joseconfig.py

# For Ubuntu-based Linuxes
$ sudo apt-get install gettext

# Make sure pip references python 3.5+
$ sudo pip install -U -r requirements.txt
```

Setup a cron job to make backups every hour:
```
0 * * * * /path/to/jose/backup.bash
```

Example `joseconfig.py` file:
```python
discord_token = 'DISCORD OAUTH2 BOT TOKEN'
soundcloud_id = 'SOUNDCLOUD API ID'
jcoin_path = 'jcoin/josecoin.db'
WOLFRAMALPHA_APP_ID = 'WOLFRAM|ALPHA APP ID'
OWM_APIKEY = 'OpenWeatherMap API Key'
MAGICWORD_PATH = 'db/magicwords.json'
```

Run Redis somewhere:
```
redis-server jose/redis.conf
```

Starting:
```
python3 jose-bot.py
```
