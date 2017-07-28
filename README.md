José
=========

Installation
```bash
# You'll need mongo
# and Python 3.6+
git clone https://github.com/lkmnds/jose.git

cd jose

python3.6 -m venv env
env/bin/python3.6 -m pip install -Ur requirements.txt

# fill in stuff from the example config file
# as you wish
nano joseconfig.py

# profit
env/bin/python3.6 jose.py
```

Example config file
```python
# discord stuff
token = 'discord token'
prefix = 'j!'

# api stuff
WOLFRAMALPHA_APP_ID = 'app id for wolframalpha'
OWM_APIKEY = 'api key for OpenWeatherMap'
WEATHER_API = {
    'base_url': 'Base URL for a custom Weather API',
    'key': 'something',
    'secret': 'something',
}

# set those to whatever
SPEAK_PREFIXES = ['josé ', 'José ', 'jose ', 'Jose ']

# enable/disable datadog reporting
datadog = False

# https://github.com/lnmds/elixir-docsearch
# fill in the address of the server
elixir_docsearch = 'localhost:6969'
```
