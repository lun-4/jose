import discord
import asyncio
import urllib
import re
import randemoji as emoji

from random import SystemRandom
random = SystemRandom()

import jcoin.josecoin as jcoin

JOSE_VERSION = '0.6.7'
JOSE_BUILD = 112

JOSE_SPAM_TRIGGER = 4
PIRU_ACTIVITY = .05
client = None

def set_client(cl):
    global client
    client = cl

JOSE_HELP_TEXT = '''Oi, eu sou o josé(v%s b%d), sou um bot trabalhadô!

Eu tenho mais de 8000 comandos somente para você do grande serverzao!

GERAL:
jose - mostra essa ajuda
$guess - jogo de adivinhar o numero aleatório
!xkcd [number|rand] - mostra ou o xkcd de número tal ou o mais recente se nenhum é dado
!yt pesquisa - pesquisar no youtube e mostrar o primeiro resultado
!pisca mensagem - PISCA A MENSAGEM(entre normal e negrito)
!animate mensagem - anima a mensagem(wip)
!money amount from to - conversão entre moedas
!version - mostra a versão do jose-bot
!playing jogo - muda o jogo que o josé está jogando
!fullwidth mensagem - converte texto para fullwidth
!escolha escolha1;escolha2;escolha3... - José escolhe por você!
!learn <texto> - josé aprende textos!
!ping - pong
!sndc termos - pesquisa no SoundCloud

Jose faz coisas pra pessoas:
!xingar @mention - xinga a pessoa
!elogiar @mention - elogia a pessoa
!causar @mention @mention - faz um causo entre pessoas

Administradores(role "mestra"):
!exit - desligar o jose(somente pessoas com o role "mestra" são autorizadas)
!reboot - reinicia o jose(somente role "mestra")
!setlmsg - altera a pequena mensagem
!lilmsg - mostra a pequena mensagem

PORN:
!hypno <termos | :latest> - busca por termos no Hypnohub (custa 1 JC)
!e621 <termos | :latest> - busca por tags no e621 (custa 1 JC)

Developers:
!log - mostrar todos os logs do josé
!dbgmsg - mandar uma mensagem de debug ao jose
!uptime - mostra o uptime do jose
!josetxt - mostra quantas mensagens o José tem na memória dele(data.txt)

Pesquisa:
!pesquisa tipo nome:op1,op2,op3... - cria uma pesquisa
!voto comando id voto - vota em uma pesquisa

Programação:
$repl - inicia um repl de python
$josescript - inicia um repl de JoseScript
$jasm - JoseAssembly

(não inclui comandos que o josé responde dependendo das mensagens)
(nem como funciona a JoseCoin, use !josecoin pra isso)
''' % (JOSE_VERSION, JOSE_BUILD)

JOSESCRIPT_HELP_TEXT = '''Bem vindo ao JoséScript!
colocar variáveis: "nome=valor" (todas as variáveis são strings por padrão)

Variáveis são definidas por usuário: assim nenhum usuário mexe nas variáveis de outro usuário :DD
pegar valor de variável: "g nome"
printar todas as variáveis definidas: "pv"
'''

@asyncio.coroutine
def show_help(message):
    yield from client.send_message(message.author, JOSE_HELP_TEXT)

@asyncio.coroutine
def show_top(message):
    yield from client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * random.randint(1,5)),
        (":ok_hand:" * random.randint(1,6))))

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
def check_roles(correct, rolelist):
    for role in rolelist:
        if role.name == correct:
            return True
    return False

@asyncio.coroutine
def random_emoji(maxn):
    res = ''
    for i in range(maxn):
        res += str(emoji.random_emoji())
    return res

atividade = [
    'http://i.imgur.com/lkZVh3K.jpg',
]

@asyncio.coroutine
def gorila_routine(ch):
    if random.random() < PIRU_ACTIVITY:
        print("THE ACTIVITY HAS BORN")
        yield from client.send_message(ch, random.choice(atividade))

def make_func(res):
    @asyncio.coroutine
    def response(message):
        yield from client.send_message(message.channel, res)

    return response

rodei_teu_cu = make_func("RODEI MEU PAU NO TEU CU")
show_noabraco = make_func("não vou abraçar")
show_tampa = make_func("A DO TEU CU\nHÁ, TROLEI")
show_vtnc = make_func("OQ VC DISSE?\nhttp://i.imgur.com/Otky963.jpg")
show_shit = make_func("tbm amo vc humano <3")
show_version = make_func("José v%s b%d" % (JOSE_VERSION, JOSE_BUILD))
