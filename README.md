José
=========

*The documentation for José is available in English as well as in Portuguese*

*Este arquivo em português pode ser encontrado em [README-pt.md](https://github.com/lkmnds/jose/blob/master/README-pt.md)*

José is a general-purpose bot for Discord written in Python.
The bot talks in portuguese and only that, no translation module is available for now, nor is planned.

**Python 3.5+ is needed**

Instructions for Debian-based Linuxes:
```bash
$ git clone https://github.com/lkmnds/jose.git
$ cd jose
$ nano joseconfig.py
$ sudo apt-get install unixodbc unixodbc-dev

# Make sure pip references python 3.5+
$ sudo pip install install -U -r requirements.txt
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

Using:
```
python3 jose-bot.py
```
