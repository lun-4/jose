JoséSpeak
====

:ok_hand: **THIS IS HIGHLY RECOMMENDED TOP NOTCH READING FOR PEOPLE ADDING JOSÉ TO NEW SERVERS** :ok_hand:

In José, `josespeak` is the module responsible for Text Generation, or, more generally, speaking.

When you add José to a new server, it **automatically** starts getting messages from this server, let me say again, **automatically** it will start recording everything said, on every channel, from the time josé is added. There is **no opt-out** from this, at least not now. From the time of this reading, every message, from every channel, from every server becomes permanent in José's "memory." **(Be sure of this before adding José.)**


In technical terms, `josespeak` has an `on_message` event and gets every message into a filter and then to a SQL database. The database relates each serverid to its message. When needed, `josespeak` gets all messages for that server, those messages are loaded into its `Texter`, each `Texter` is related to its server ID. When it is time to generate text for a server, the `Texter` of that server generates it. Another thing `josespeak` does is calculate the average word length of an entire server by analyzing the messages, when a `Texter` doesn't have the maximum words it should generate, it uses the average of the server's.


There are 2 extra `Texter`s after the server ones, one is the "cult" generator, which uses the file `jose-data.txt` to generate formal texts, and the "global" generator, which uses the file `zelao.txt`, this file has **ALL MESSAGES FROM EVERY SERVER** but without separation for "who said what", the messages are just dumped there. Those `Texters` are only generated in José's startup.


### List of commands

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!speaktrigger ["fw"]` | Triggers your server's `Texter` to generate text, if fw is listed as in argument, then the `Texter` will generate in Ｆｕｌｌ　Ｗｉｄｔｈ | `j!spt fw` | `j!spt`
`j!falar` | Triggers the "cult" generator to generate text | |
`j!sfalar` | Triggers your server's `Texter` to generate text | |
`j!gfalar` | Triggers the global `Texter` to generate text | |
`j!jwormhole` | Uses your server's `Texter` to send messages through Septapus Wormhole | | `j!jw`
`j!tatsu` | Prefixes output from `j!speaktrigger` with `"^"`, for Tatsumaki's call function | |

### Coming Soon™

 * Removal of `j!sfalar` and `j!gfalar`