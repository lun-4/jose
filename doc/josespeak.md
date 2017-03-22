JoséSpeak
====

:ok_hand: **THIS IS HIGHLY RECOMMENDED TOP NOTCH READING FOR PEOPLE ADDING JOSÉ TO NEW SERVERS** :ok_hand:

In José, `josespeak` is the module responsible for Text Generation, or, more generally, speaking.

José needs source text so he can make its sentences, currently José gets 3000 messages from the server's default channel(usually #general).

In technical terms, `josespeak` has its `on_message` event, that only calculates the probability of receiving an answer from José(default is 1%), when needed, a text generator is born, `Texter`. The `Texter` is *usually* filled with 3000 messages from the server's default channel, the messages go through a filter and messages from José are ignored. Botblock rules still apply.

(removed actions: Message storage to SQL, wordlength calculation)

There are 2 extra `Texter`s after the server ones, one is the "cult" generator, which uses the file `jose-data.txt` to generate formal texts, and the "global" generator, which uses the file `zelao.txt`, this file has **ALL MESSAGES FROM EVERY SERVER** but without separation for "who said what", the messages are just dumped there. Those `Texters` are only generated in José's startup.


### List of commands

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!speaktrigger ["fw"]` | Triggers your server's `Texter` to generate text, if fw is listed as in argument, then the `Texter` will generate in Ｆｕｌｌ　Ｗｉｄｔｈ | `j!spt fw` | `j!spt`
`j!falar` | Triggers the "cult" generator to generate text | |
`j!gfalar` | Triggers the global `Texter` to generate text | |
`j!jwormhole` | Uses your server's `Texter` to send messages through Septapus Wormhole | | `j!jw`
`j!tatsu` | Prefixes output from `j!speaktrigger` with `"^"`, for Tatsumaki's call function | |

### Coming Soon™

 * Removal of `j!gfalar`
