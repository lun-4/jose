import discord
import asyncio
import urllib
import re
import randemoji as emoji

from random import SystemRandom
random = SystemRandom()

import jcoin.josecoin as jcoin

JOSE_VERSION = '0.7.2'
JOSE_BUILD = 136

JOSE_SPAM_TRIGGER = 4
PIRU_ACTIVITY = .05

TOTAL = 13.0
PORN_MEMBERS = 8.0
LEARN_MEMBERS = 1.0

# prices
'''
P = maior recompensa(7.4) * probabilidade(0.12)/ quantidade de membros(12 porquê a hachi não possui conta)
P = (7.4*0.12) / 12
P  = 0.888/12
P = 0.74
'''
BASE_PRICE = 0.74

PORN_PRICE = (BASE_PRICE) * ((TOTAL-1) / PORN_MEMBERS)
LEARN_PRICE = (BASE_PRICE) * ((TOTAL-1) / LEARN_MEMBERS)

client = None

def set_client(cl):
    global client
    client = cl

JOSE_PORN_HTEXT = '''Pornô(Tudo tem preço de %.2fJC):
!hypno <termos | :latest> - busca por termos no Hypnohub
!e621 <termos | :latest> - busca por tags no e621
!yandere <termos | :latest> - busca no yande.re
''' % (PORN_PRICE)

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

%s

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
''' % (JOSE_VERSION, JOSE_BUILD, JOSE_PORN_HTEXT)

JOSESCRIPT_HELP_TEXT = '''Bem vindo ao JoséScript!
colocar variáveis: "nome=valor" (todas as variáveis são strings por padrão)

Variáveis são definidas por usuário: assim nenhum usuário mexe nas variáveis de outro usuário :DD
pegar valor de variável: "g nome"
printar todas as variáveis definidas: "pv"
'''


cantadas = [
    'ô lá em casa',
    'vc é o feijao do meu acaraje',
    'gate, teu cu tem air bag?? pq meu pau tá sem freio',
    'se merda fosse beleza você estaria toda cagada',
    'me chama de bombeiro e deixa eu apagar seu fogo com a minha mangueira',
    'to no hospital esperando uma doaçao de coraçao, pq vc roubou o meu',
    'me chama de piraque e vamos pra minha casa',
    'me chama de gorila e deixa eu te sarrar no ritmo do seu coração',
    'meu nome é arlindo, mas pode me chamar de lindo pq perdi o ar quando te vi',
    'me chama de lula e deixa eu roubar seu coração',
    'espero que o seu dia seja tão bom quanto sua bunda',
    'chama meu pau de Jean Willys e deixa ele cuspir na sua cara',
    'deixe eu ser a bala do seu Hamilton e acertar seu coração',
    'me chama de terrorista e deixa eu explodir dentro de você',
]

elogios = [
    "você é linde! <3",
    "sabia que você pode ser alguém na vida?",
    "eu acredito em você",
]

xingamentos = [
    "Tu fica na merda",
    "Vai se fuder!",
    "pq colocou man",
    "MANO PQ",
    "vsf",
    "seu FILHO DA PUTA",
    "se fosse eu não deixava",
    "vai tomar no cu",
]

demon_videos = [
    'https://www.youtube.com/watch?v=-y73eXfQU6c',
    'https://www.youtube.com/watch?v=1GhFj54x1iM',
    'https://www.youtube.com/watch?v=cXzT3IDNwEw',
    'https://www.youtube.com/watch?v=WDKcod-mOIE',
    'https://www.youtube.com/watch?v=br3KwhALEvw',
    'https://www.youtube.com/watch?v=MzRDZpyOMFM',
    'https://www.youtube.com/watch?v=LHJC41YP5ec',
    'https://www.youtube.com/watch?v=ae9GEf7K8DM',
    'https://www.youtube.com/watch?v=03KHCQZ6Faw',
    'https://www.youtube.com/watch?v=9NCWKd8lL3o',
]

@asyncio.coroutine
def show_help(message):
    yield from client.send_message(message.author, JOSE_HELP_TEXT)

@asyncio.coroutine
def show_top(message):
    yield from client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * random.randint(1,5)),
        (":ok_hand:" * random.randint(1,6))))

@asyncio.coroutine
def search_youtube(message):
    d = message.content.split(' ')
    search_term = ' '.join(d[1:])

    print("!yt @ %s : %s" % (message.author.id, search_term))

    query_string = urllib.parse.urlencode({"search_query" : search_term})
    html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
    search_results = re.findall(r'href=\"\/watch\?v=(.{11})', html_content.read().decode())

    if len(search_results) < 2:
        yield from client.send_message(message.channel, "!yt: Nenhum resultado encontrado.")
        return

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
        yield from client.send_message(ch, random.choice(atividade))

def make_func(res):
    @asyncio.coroutine
    def response(message):
        yield from client.send_message(message.channel, res)

    return response

def make_xmlporn(baseurl):
    @asyncio.coroutine
    def func(message):
        res = yield from jcoin_control(message.author.id, PORN_PRICE)
        if not res[0]:
            yield from client.send_message(message.channel,
                "PermError: %s" % res[1])
            return

        args = message.content.split(' ')
        search_term = ' '.join(args[1:])

        if search_term == ':latest':
            yield from client.send_message(message.channel, 'procurando post mais recente')
            r = requests.get('%s?limit=%s' % (baseurl, PORN_LIMIT))
            tree = ElementTree.fromstring(r.content)
            root = tree
            try:
                post = random.choice(root)
                yield from client.send_message(message.channel, '%s' % post.attrib['file_url'])
                return
            except Exception as e:
                yield from jose_debug(message, "erro: %s" % str(e))
                return

        else:
            yield from client.send_message(message.channel, 'procurando por %r' % search_term)
            r = requests.get('%s?limit=%s&tags=%s' % (baseurl, PORN_LIMIT, search_term))
            tree = ElementTree.fromstring(r.content)
            root = tree
            try:
                post = random.choice(root)
                yield from client.send_message(message.channel, '%s' % post.attrib['file_url'])
                return
            except Exception as e:
                yield from jose_debug(message, "erro: provavelmente nada foi encontrado, seu merda. (%s)" % str(e))
                return

    return func

rodei_teu_cu = make_func("RODEI MEU PAU NO TEU CU")
show_noabraco = make_func("não vou abraçar")
show_tampa = make_func("A DO TEU CU\nHÁ, TROLEI")
show_vtnc = make_func("OQ VC DISSE?\nhttp://i.imgur.com/Otky963.jpg")
show_shit = make_func("tbm amo vc humano <3")
show_version = make_func("José v%s b%d" % (JOSE_VERSION, JOSE_BUILD))
show_emule = make_func("http://i.imgur.com/GO90sEv.png")
show_frozen_2 = make_func('http://i.imgur.com/HIcjyoW.jpg')
pong = make_func('pong')

help_josecoin = make_func(jcoin.JOSECOIN_HELP_TEXT)
show_tijolo = make_func("http://www.ceramicabelem.com.br/produtos/TIJOLO%20DE%2006%20FUROS.%209X14X19.gif")
show_mc = make_func("https://cdn.discordapp.com/attachments/202055538773721099/203989039504687104/unknown.png")
show_vinheta = make_func('http://prntscr.com/bvcbju')
show_agira = make_func("http://docs.unity3d.com/uploads/Main/SL-DebugNormals.png")
