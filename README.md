José
=========

*en*: José is in Brazilian Portuguese(including documentation which follows this README file)

José é o melhor bot para a galerinha do mal dentro do Discord!

Atualmente o bot está somente em português brasileiro e não é recomendado usar em outros servidores,
você terá que configurar manualmente(`git clone`) e rodar ele separadamente

Instruções(Linux):
```bash
$ git clone https://github.com/lkmnds/jose.git
$ cd jose
$ nano joseconfig.py
```

`joseconfig.py` de exemplo:
```python
discord_token = 'DISCORD OAUTH2 BOT TOKEN'
soundcloud_id = 'SOUNDCLOUD API ID'
jcoin_path = 'jcoin/josecoin.db'
```

Recomendável ter um `jose-data.txt` com sentenças do jeito que você quiser, o josé irá falar elas com o comando `!falar`

Rodando:
```
python3 jose-bot.py
```
