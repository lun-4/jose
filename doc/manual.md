José Manual v0.0.1
=====

# How to Install in new server??????????

 * Make sure you have Python 3.5+ installed
 * Make sure you have `gettext` installed
```bash
git clone https://github.com/lkmnds/jose.git
cd jose
pip3 install discord.py Pillow wolframalpha pyowm psutil

# generate language files
cd po
make mofiles
```

### Configuration

`joseconfig.py` looks like this:
```python
# paths for databases
jcoin_path = 'jcoin/josecoin.db'
MAGICWORD_PATH = 'db/magicwords.json'

# tokens 'n' stuff
discord_token = 'DISCORD OAUTH2 BOT TOKEN'
soundcloud_id = 'SOUNDCLOUD API ID'
WOLFRAMALPHA_APP_ID = 'WOLFRAM|ALPHA APP ID' # https://developer.wolframalpha.com/portal/signin.html
OWM_APIKEY = 'OpenWeatherMap API Key' # https://openweathermap.org/api
```

### Running

in a shell(probably on tmux so it doesn't exits when you exit the shell):
```
python3 jose-bot.py
```

CTRL-C unloads and stops everything(use that AFTER josé logs on, you can use if errors happen in startup)
