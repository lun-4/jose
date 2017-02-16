Magic Words
==================

*Documentação em Português:* [magicwords-pt.md](https://github.com/lkmnds/jose/blob/master/doc/cmd/magicwords-pt.md)

Magic Words are words, configurable per server, that, when said, makes José
say something, for example when someone says "good night", José responds "Good dreams!"

## Limits for Magic Words
 * 10 Magic Words per set
 * 10 Sets per server
 * Magic Words are case-insensitive

## Setup a magicword

 * Use the `j!setmw` command, like this:
  ```
  j!setmw myword1,myword2,myword3,my word 4;you said a word
  ```
  * When anyone says a text that contains `"myword1", "myword2", "myword3"` or `"my word 4"`,
   José will respond "you said a word"
 * Example:
```
   someone: i have myword1
   José: you said a word

   someone: Myword 4
   # nothing happens

   someone: my word 4
   José: you said a word
   someone: mY wOrD 4
   José: you said a word

   someone: mY  word 4
   # nothing happens because "mY  wOrD" is different from "mY wOrD"
```
  * Each magicword set has its own ID number

## Formatting responses with Magic Words
 * The responses José gives can be a little different based on the formatting of the response
  * Taking for example a magicword set up like `j!setmw hello,hi;hello %a`
  * Every time someone says or their message contains `"hello"` or `"hi"`, josé will respond `"hello @mention"`, with `"@mention"` being a mention to the author of the message
  * If you want a plain `%`, use `%%` in your response, it will become `%`

## Delete a magicword set
 * `j!delmw setid`, with `setid` being the ID number of the set

## List sets in a server
 * `j!listmw [setid]`, if you use `setid`, it will only show that set
