import logging

# discord stuff
token = 'token goes here'
prefix = 'j!'

# api stuff
WOLFRAMALPHA_APP_ID = 'app id for wolframalpha'
OWM_APIKEY = 'api key for OpenWeatherMap'

# set those to whatever
SPEAK_PREFIXES = ['josé ', 'José ', 'jose ', 'Jose ']

# enable/disable datadog reporting
datadog = False

# https://github.com/lnmds/elixir-docsearch
# fill in the address of the server
elixir_docsearch = 'localhost:6969'

# channel for interesting packets
PACKET_CHANNEL = 361685197852508173

# channel log levels
LEVELS = {
    logging.INFO: 361685197852508173,
    logging.WARNING: 361685197852508173,
    logging.ERROR: 361685197852508173
}
