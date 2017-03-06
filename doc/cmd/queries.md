Query types for the `j!query` command
=====================================

*Para a documentação em português, veja [queries-pt.md](https://github.com/lkmnds/jose/blob/master/doc/queries-pt.md)*

*global/globally*: Applied to every server José is in

*local/locally*: Applied only in a specific server, usually the server where the message/command originated from.

 * `j!query summary`
  * Summary of global data: total messages, total commands received, and the most used command

 * `j!query dbsize`
  * Shows the size of the 4 main databases jose uses
   * `markovdb`: the markov database, and normally the biggest, it has all messages from the servers
   * `messages`: the message count database
   * `itself`: the statistics database
   * `wlength`: the word length database

 * `j!query this`
  * Queries the server where the command originated and shows (almost) the same things as `!query summary`, but using a local database

 * `j!query topcmd`
  * Shows top 10 most used commands in josé

 * `j!query ltopcmd`
  * Shows top 10 most used commands in your server
