Tipos de pedidos para o comando `j!query`
=========================================

*English documentation: [queries.md](https://github.com/lkmnds/jose/blob/master/doc/queries.md)*

*global/globalmente*: é aplicado em todos os servidores em que o josé está

*local/localmente*: aplicado somente em um servidor específico, normalmente no servidor em que uma mensagem/comando se originou

 * `j!query summary`
  * Sumário: todas as mensagens e comandos recebidos, e também o comando mais usado globalmente

 * `j!query dbsize`
  * Mostra o tamanho dos 4 bancos de dados que o josé usa
   * `markovdb`: o banco de dados para o gerador de textos de Markov, normalmente é o maior banco de dados pois possui todas as mensagens recebidas
   * `messages`: contador de mensagens por servidor
   * `itself`: o banco de dados de estatísticas
   * `wlength`: o banco de dados do tamanho de palavras(usado pelo `josespeak`)

 * `j!query this`
  * Mostra as mesmas informações que o `!query summary`, mas informações locais

 * `j!query topcmd`
  * Mostra os comandos mais usados
