List of Commands
=================

### `jose`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!info`       | Shows Info | |
`j!ping`       | Pings José | `j!ping` |
`j!rand min max` | Generates a Random Number from `min` to `max` | `j!rand 0 10` |
`j!escolha a;b;c` | Chooses between any amount of choices | `j!escolha A;B;C` | `j!pick`
`j!version` | Shows José version | |
`j!modlist` | Shows all loaded modules | |
`j!clist module` | List commands that a module creates | |
`j!report` | Makes a quick report on some stats | |
`j!uptime` | Shows uptime | | |

### `joselang`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!confighelp` | Shows a little summary of server configuration | |
`j!language lang` | Sets a language for the current server | `j!language en` |
`j!listlang` | Shows all available languages for josé | |
`j!botblock` | Toggles botblock | |
`j!jcprob probability` | Changes your server's probability of josé saying text, default is 0 | `j!jcprob 3` |

### `josemagicword`

[Documentation for `josemagicword`](https://github.com/lkmnds/jose/blob/master/doc/cmd/magicwords.md)

### `josemath`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!wolframalpha terms` | Sends a request to [WolframAlpha](http://wolframalpha.com/) | `j!wolframalpha average dick size` | `j!wa`
`j!temperature location` | Requests current temperature of a place using [OpenWeatherMap](openweathermap.org) | `j!temperature Sydney, Australia` | `j!temp`, `j!weather`
`j!money quantity base to` | Converts currency, use `j!money list` to see available currencies | `j!money 1 AUD USD` |
`j!roll <amount>d<sides>` | Rolls `amount` dice of `sides` sides | `j!roll 20d6` |
`j!percent amount total` | Calculates `amount`% out of `total` | `j!percent 50 100` |

`j!bitcoin amount currency` | Get XBP price info | `j!bitcoin 20 USD`, shows 20 BTC to USD | `j!btc`
`j!crypto amount from to` | Converts between various cryptocurrencies

### `josememes`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!aprovado` | Approved! | |
`j!htmpr` | Help when `j!meme` breaks up(portuguese text) | |
`j!meme` | MEMES, use `j!meme` to see possible uses(portuguese text) | | `j!m`
`j!emoji [n]` | Shows `n` emoji, default is a random number from 1 to 5 | `j!emoji 10` |
`j!blackmiror` | SHOWS VERY BLACK MIRROR STUFF | |
`j!8ball stuff` | Asks 8ball. | `j!8ball Is the universe going to die?` |
`j!fullwidth text` | Makes a text ｆｕｌｌｗｉｄｔｈ | `j!fw hello world` | `j!fw`
`j!ri text` | Converts text to *Regional Indicators* | `j!ri hello world` |

### `josespeak`

[Documentation for the whole `josespeak` thing, it is complicated](https://github.com/lkmnds/jose/blob/master/doc/josespeak.md)

### `josestats`

[Documentation for the `j!query` command](https://github.com/lkmnds/jose/blob/master/doc/cmd/queries.md)

### `josextra`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!xkcd [num]` | XKCD. (num can be any number or "rand" for a random comic) | `j!xkcd 1000` |
`j!tm text` | Transform a Text In A Trademark™ | `j!tm Hell` |
`j!docs [topic or "list"]` | Searches documentation for josé | |
`j!yt search_terms` | Search YouTube | `j!yt Tunak Tunak Tun sped up every time they say Tunak` |
`j!sndc search_terms` | Search Soundcloud | `j!sndc Tunak Tunak Tun` |
`j!color "rand"\|#aabbcc\|red,green,blue` | show colors | `j!color #DEADAF`, `j!color 100,50,100`, `j!color rand` |

### `jcoin`

[Documentation for JoséCoin](https://github.com/lkmnds/jose/blob/master/doc/jcoin.md)

### `joseimages`

Some commands in `joseimages` have special syntax:
 * `-latest` gets the latest post from an image board
 * `-random` gets a random post from an image board

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!urban stuff` | Searches the *Urban Dictionary* | `j!urban kys` |
`j!hypno tags` | Searches *HypnoHub* | |
`j!e621 tags` | Searches *e621* | |
`j!yandere tags` | Searches *yande.re* | |
`j!derpibooru tags` | Searches *Derpibooru* | |

### `josedatamosh`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!datamosh url` | Datamoshes a file | `j!datamosh https://discordapp.com/api/users/202587271679967232/avatars/93ac51b863fde7c38578693947dab6bc.jpg` |

### `josegambling`

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!jcrhelp` | Help about JoséCoin Roulette™| |
`j!jrstart` | Starts a JoséCoin Roulette™ session in your server | |
`j!jrbet amount` | Bet on the currently running JCR™ session | `j!jrbet 1` |
`j!jrdo` | Do the JCR™ aka see the winner | |
`j!jreport` | JCR™ report, shows what amount each one paid in the session | |
`j!jrcheck` | Shows if a JCR™ session is on/off | |
`j!flip` | Flips a coin. | |
`j!slots amount` | little slot machine | `j!slots 0.2` |
`j!duel @someone amount` | Makes a duel with someone | `j!duel @aaa 1` |
