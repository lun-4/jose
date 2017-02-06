The `josespeak` module
====

:ok_hand: **THIS IS HIGHLY RECOMMENDED TOP NOTCH READING FOR PEOPLE ADDING JOSÉ TO NEW SERVERS** :ok_hand:

In José, `josespeak` is the module responsible for Text Generation, or more generally, speaking.

When you add José to a new server, it **automatically** starts getting messages from this server, let me say again, **automatically** it will start recording everything said, on every channel, from the time josé is added. There is **no opt-out** from this, at least not now. From the time of this reading, every message, from every channel, from every server becomes permanent in josé's "memory". (**Be sure of that before adding José**)


In technical terms, `josespeak` has a `on_message` event and gets every message into a filter and then to a JSON database, that database is saved into disk every 3 minutes. The database is separated per-server ID. For each server ID in the database, there is an array lines, those lines are loaded into `Texter`s every 10 minutes, each `Texter` is related to its server ID, when it is time to generate text for a server, the `Texter` of that server generates it. Another thing `josespeak` does is calculate the average word length of an entire server by analyzing the messages, when a `Texter` doesn't have the maximum words it should generate, it uses the average of the server's.


There are 2 extra `Texter`s after the server ones, one is the "cult" generator, which uses the file `jose-data.txt` to generate formal texts, and the "global" generator, which uses the file `zelao.txt`, this file has **ALL MESSAGES FROM EVERY SERVER** but without separation for "who said what", the messages are just dumped there. Those `Texters` are only generated in josé's startup.


### List of commands

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`!speaktrigger` | Triggers your server's `Texter` to generate text | | `!spt`
`!falar [wordmax]` | Triggers the "cult" generator to generate text(wordmax default is 10) | `!falar 30` |
`!sfalar [wordmax]` | Triggers your server's `Texter` to generate text(wordmax default is 10) | `!sfalar 40` |
`!gfalar [wordmax]` | Triggers the global `Texter` to generate text(wordmax default is 10) | `!gfalar 20` |
`!jwormhole` | Uses your server's `Texter` to send messages through Septapus Wormhole | | `!jw`
