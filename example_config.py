import logging

# discord stuff
token = 'token goes here'

# default prefix for josé
prefix = 'j!'

# where is mongo
# if docker, uncomment
#  MONGO_LOC = 'mongo'

# api stuff
WOLFRAMALPHA_APP_ID = 'app id for wolframalpha'
OWM_APIKEY = 'api key for OpenWeatherMap'
MSFT_TRANSLATION = {
    'name': 'name for the project',
    'key': 'subscription key',
}

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
# 60 is used for transaction logs
LEVELS = {
    logging.INFO: 'https://discordapp.com/api/webhooks/:webhook_id/:token',
    logging.WARNING: 'https://discordapp.com/api/webhooks/:webhook_id/:token',
    logging.ERROR: 'https://discordapp.com/api/webhooks/:webhook_id/:token',
    60: 'https://discordapp.com/api/webhooks/:webhook_id/:token',
}

# lottery configuration
JOSE_GUILD = 273863625590964224
LOTTERY_LOG = 368509920632373258

postgres = {
    'user': 'slkdjkjlsfd',
    'password': 'dlkgajkgj',
    'database': 'jose',
    'host': 'memeland.com'
}

JOSECOIN_API = 'http://0.0.0.0:8080/api'
# If on docker
# JOSECOIN_API = 'http://josecoin:8080/api'

