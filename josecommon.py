import discord
import asyncio
import urllib
import re

import jcoin.josecoin as jcoin

JOSE_VERSION = '0.5.9'
JOSE_SPAM_TRIGGER = 2
client = None

def set_client(cl):
	global client
	client = cl

JOSE_HELP_TEXT = '''Oi, eu sou o josé(v%s), sou um bot trabalhadô!

Eu tenho mais de 8000 comandos somente para você do grande serverzao!

jose - mostra essa ajuda
$guess - jogo de adivinhar o numero aleatorio
!xkcd [number|rand] - mostra ou o xkcd de número tal ou o mais recente se nenhum é dado
!yt pesquisa - pesquisar no youtube e mostrar o primeiro resultado
!setlmsg - altera a pequena mensagem
!lilmsg - mostra a pequena mensagem
!log - mostrar todos os logs do josé
!dbgmsg - mandar uma mensagem de debug ao jose
!xingar @mention - xinga a pessoa
!elogiar @mention - elogia a pessoa
!exit - desligar o jose(somente pessoas com o role "mestra" são autorizadas)
!reboot - reinicia o jose(somente role "mestra")
!version - mostra a versão do jose-bot
!pisca mensagem - PISCA A MENSAGEM(entre normal e negrito)
!animate mensagem - anima a mensagem(wip)
!money amount from to - conversão entre moedas
!fullwidth mensagem - você sabe
!playing jogo - muda o jogo que o josé tá jogando
!uptime - você também sabe
!escolha escolha1;escolha2;escolha3... - José escolhe por você!

!hypno <termos | :latest> - busca por termos no Hypnohub (custa 1 JC)
!josetxt - mostra quantas mensagens o José tem na memória dele (custa 1 JC)

!pesquisa tipo nome:op1,op2,op3... - cria uma pesquisa
!voto comando id voto - vota em uma pesquisa

$repl - inicia um repl de python
$josescript - inicia um repl de JoseScript

(não inclui comandos que o josé responde dependendo das mensagens)
(nem como funciona a JoseCoin)
''' % JOSE_VERSION

JOSESCRIPT_HELP_TEXT = '''Bem vindo ao JoséScript!
colocar variáveis: "nome=valor" (todas as variáveis são strings por padrão)

Variáveis são definidas por usuário: assim nenhum usuário mexe nas variáveis de outro usuário :DD
pegar valor de variável: "g nome"
printar todas as variáveis definidas: "pv" '''

@asyncio.coroutine
def show_version(message):
    yield from client.send_message(message.channel, "José v%s" % JOSE_VERSION)

@asyncio.coroutine
def show_help(message):
    yield from client.send_message(message.author, JOSE_HELP_TEXT)

@asyncio.coroutine
def show_shit(message):
    yield from client.send_message(message.channel, "tbm amo vc humano <3")

@asyncio.coroutine
def show_vtnc(message):
    yield from client.send_message(message.channel, "AH VAI SE FUDER")

@asyncio.coroutine
def show_top(message):
    yield from client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * 5),
        (":ok_hand:" * 6)))

@asyncio.coroutine
def show_tampa(message):
    yield from client.send_message(message.channel, "A DO TEU CU\nHÁ, TROLEI")

@asyncio.coroutine
def show_noabraco(message):
    yield from client.send_message(message.channel, "nao vou abraçar")

@asyncio.coroutine
def random_yt(message):
    d = message.content.split(' ')
    search_term = ' '.join(d[1:])

    print("!yt @ %s : %s" % (message.author.id, search_term))

    query_string = urllib.parse.urlencode({"search_query" : search_term})
    html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())

    yield from client.send_message(message.channel, "http://www.youtube.com/watch?v=" + search_results[0])

@asyncio.coroutine
def rodei_teu_cu(message):
    yield from client.send_message(message.channel, 'RODEI MEU PAU NO TEU CU')
