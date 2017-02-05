Magic Words/Palavras Mágicas
==================

*English documentation:* (magicwords.md)[https://github.com/lkmnds/jose/blob/master/doc/cmd/magicwords.md]

Magic Words são palavras, configuradas por servidor, que, quando faladas, ou estiverem dentro de uma mensagem, fazem com que o josé fale algo pre-determinado, por exemplo, quando alguém falar "boa noite", josé fala "bons sonhos"

## Limites
 * 10 Palavras Mágicas por conjunto
 * 10 Conjuntos por servidor
 * Palavras Mágicas não são sensíveis a letras maiúsulas ou minúsculas

## Setar um conjunto de palavras mágicas

 * Use `!setmw`:
  ```
  !setmw palavra1,palavra2,palavra3,palavra 4;você disse uma palavra
  ```
  * Quando alguém falar algum texto que contenha `"palavra1", "palavra2", "palavra3"` or `"palavra 4"`,
   José irá responder `"você disse uma palavra"`
 * Exemplo:
```
   alguém: eu tenho palavra1
   José: você disse uma palavra

   alguém: pa lavra 4
   # nada acontece

   alguém: palavra 4
   José: você disse uma palavra
   alguém: PALavrA 4
   José: você disse uma palavra

   alguém: PÁlavra 4
   # nada acontece, pois "á" é diferente de "a"
```
  * Cada conjunto tem seu número identificador

## Formatando respostas
 * As respostas que o José dá podem ser um pouco diferentes/customizáveis baseados na formato que é a resposta
  * Por exemplo uma palavra mágica `!setmw olá,oi;olá %a`
  * Toda vez que alguém falar ou a mensagem conter `"olá"` ou `"oi"`, josé vai responder `"olá @mention"`, com `"@mention"` sendo uma menção ao autor da mensagem
  * Para um simples `%`, use `%%` na sua resposta

## Remover um conjunto
 * `!delmw setid`, com `setid` sendo o número identificador do seu conjunto

## Mostrar todos os conjuntos de um servidor
 * `!listmw [setid]`, se você colocar `setid`, ele mostra somente aquele conjunto
