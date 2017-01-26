José
===========

*English documentation: [README.md](https://github.com/lkmnds/jose/blob/master/README.md)*


José é o melhor bot para a galerinha do mal dentro do Discord!

Atualmente o bot está somente em português brasileiro e não é recomendado usar em outros servidores,
você terá que configurar manualmente(`git clone`) e rodar ele separadamente

**Python 3.5+ é necessário**

Instruções(Linux):
```bash
$ git clone https://github.com/lkmnds/jose.git
$ cd jose
$ nano joseconfig.py
$ pip install discord.py Pillow wolframalpha pyowm
```

`joseconfig.py` de exemplo:
```python
discord_token = 'DISCORD OAUTH2 BOT TOKEN'
soundcloud_id = 'SOUNDCLOUD API ID'
jcoin_path = 'jcoin/josecoin.db'
WOLFRAMALPHA_APP_ID = 'WOLFRAM|ALPHA APP ID'
OWM_APIKEY = 'OpenWeatherMap API Key'
MAGICWORD_PATH = 'db/magicwords.json'
```

Recomendável ter um `jose-data.txt` com sentenças do jeito que você quiser, o josé irá falar elas com o comando `!falar`

Rodando:
```
python3 jose-bot.py
```
