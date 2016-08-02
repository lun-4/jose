import discord
import asyncio
import time
import base64
from xml.etree import ElementTree

import randemoji as emoji

from random import SystemRandom
random = SystemRandom()

import joseerror as je

JOSE_VERSION = '0.8.0-beta6'
JOSE_BUILD = 290

#config
chattiness = .25
MASTER_ROLE = 'mestra'
LEARN_ROLE = 'cult'
JOSE_ANIMATION_LIMIT = 1 # 2 animações simultaneamente

#just for 0.6.6.6 and 6.6.6
DEMON_MODE = False
PARABENS_MODE = False

#mode changes
MAINTENANCE_MODE = False
GAMBLING_MODE = False

JOSE_SPAM_TRIGGER = 4
PIRU_ACTIVITY = .008
jc_probabiblity = .12
JC_REWARDS = [1, 1.2, 2, 2.5, 3.14, 5, 5.1, 6.28, 7.4]

PORN_LIMIT = 14
GAMBLING_FEE = 5 # 5 percent
TOTAL = 14.0
PORN_MEMBERS = 8.0
LEARN_MEMBERS = 1.0

# prices
'''
P = len_recompensas * (recompensa * prob) / TOTAL
'''
BASE_PRICE = 3 * ((len(JC_REWARDS) * (JC_REWARDS[len(JC_REWARDS)-1] * jc_probabiblity)) / TOTAL)

PORN_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / PORN_MEMBERS)
LEARN_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / LEARN_MEMBERS)
LEARN_PRICE -= 12

OP_TAX_PRICE = (BASE_PRICE) * ((TOTAL-1.0) / TOTAL)

PRICE_TABLE = {
    'porn': ("Comandos relacionados a pornografia", PORN_PRICE),
    'learn': ("Comandos relacionados ao josé aprender textos", LEARN_PRICE),
    'operational': ("Taxa operacional de alguns comandos(normalmente relacionados a muito processamento)", OP_TAX_PRICE)
}

ascii_to_wide = dict((i, chr(i + 0xfee0)) for i in range(0x21, 0x7f))
ascii_to_wide.update({0x20: u'\u3000', 0x2D: u'\u2212'})  # space and minus

JOSE_ID = '202587271679967232'

client = None

def set_client(cl):
    global client
    client = cl

JOSE_PORN_HTEXT = '''Pornô(Tudo tem preço de %.2fJC):
!hypno <termos | :latest> - busca por termos no Hypnohub
!e621 <termos | :latest> - busca por tags no e621
!yandere <termos | :latest> - busca no yande.re
''' % (PORN_PRICE)

JOSE_GENERAL_HTEXT = '''
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
'''

JOSE_TECH_HTEXT = '''Comandos relacionados a coisas *TECNOLÓGICAS*

!enc texto - encripta um texto usando OvoCrypt
!dec texto - desencripta um texto encriptado com OvoCrypt

Programação:
$repl - inicia um repl de python
$josescript - inicia um repl de JoseScript
$jasm - JoseAssembly

'''

JOSE_HELP_TEXT = '''Oi, eu sou o josé(v%s b%d), sou um bot trabalhadô!
Eu tenho mais de 8000 comandos somente para você do grande serverzao!

!htgeral - abre o texto de comandos gerais(o mais recomendado)
!htech - texto de ajuda para comandos *NERDS*

Jose faz coisas pra pessoas:
!xingar @mention - xinga a pessoa
!elogiar @mention - elogia a pessoa
!causar @mention @mention - faz um causo entre pessoas

Apostas:
!ahelp e !adummy irão te mostrar os textos de ajuda para apostadores

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

(não inclui comandos que o josé responde dependendo das mensagens)
(nem como funciona a JoseCoin, use !josecoin pra isso)
''' % (JOSE_VERSION, JOSE_BUILD, JOSE_PORN_HTEXT)

JOSESCRIPT_HELP_TEXT = '''Bem vindo ao JoséScript!
colocar variáveis: "nome=valor" (todas as variáveis são strings por padrão)

Variáveis são definidas por usuário: assim nenhum usuário mexe nas variáveis de outro usuário :DD
pegar valor de variável: "g nome"
printar todas as variáveis definidas: "pv"
'''

GAMBLING_HELP_TEXT = '''O que é: Função que permite dois (ou mais) usuários apostarem josecoins por esporte.

Como funciona:
-Primeiro, ativar o "modo aposta" do jose-bot com o comando: !aposta (qualquer um pode começar uma aposta)
-jose-bot printa a mensagem "Modo aposta ativado. Joguem suas granas!" ou algo do tipo
-Enquanto o "modo aposta" estiver ativado, qualquer um que !enviar josecoins para o jose-bot entra na aposta, o jose-bot grava o nome da pessoa
temporariamente como se fosse um "acesso a memória RAM"
-As apostas são cumulativas, ou seja, se uma mesma pessoa !enviar 20 e depois !enviar 40, é como se ela apostasse 60 josecoins de uma vez
-Quando todos tiverem feito suas apostas, inserir o comando !rolar (ou outro nome sla), o que fará com que o jose-bot sorteie aleatoriamente uma pessoa com base na fórmula: n = 1/x (x sendo o número de pessoas que entraram na aposta)
-A pessoa sorteada ganha a aposta, recebendo 76.54% do montante, e os outros apostadores ficam com o que sobrou, que será dividido igualmente.
-Após o pagamento, o modo aposta se desativa automaticamente(editado)

Exemplo:
Número de apostadores = 3 (pessoas A, B e C, respectivamente)
Inserindo o comando ---> !aposta
jose-bot printa: "Modo aposta ativado. Joguem suas granas!"
A pessoa A aposta 50 josecoins ---> !enviar @ZELAO 50
A pessoa B aposta 30 josecoins ---> !enviar @ZELAO 30
A pessoa C aposta 20 josecoins ---> !enviar @ZELAO 20
"Rolando o dado" ---> !rolar

Cálculo do prêmio:
M = montante acumulado de todas as apostas
P = total de josecoins que o vencedor da aposta ganha
p = total de josecoins que cada um dos perdedores da aposta ganha
x = número de pessoas que entraram na aposta

P = M * 0.7654
p = M * 0.2346 / x
Pegando os valores anteriores, o montante é 50+30+20=100
A pessoa B ganhou a aposta, sendo assim ela ganha 76.54 josecoins, sobrando 23.46 josecoins.
Desses 23.46 josecoins, as pessoas A e C vão receber, cada uma, 11.73 josecoins.
'''

GAMBLING_HELP_TEXT_SMALL = '''Aposta for Dummies:
!aposta - inicia modo de aposta do jose
!enviar <mention pro jose> <quantidade> - aposta propiamente dita
!rolar - quando você já está pronto pra ver quem é o ganhador
'''

debug_logs = []

debug_channel = discord.Object(id='208728345775439872')

@asyncio.coroutine
def debug_log(string):
    global debug_channel
    print(string)
    today_str = time.strftime("%d-%m-%Y")
    with open("logs/jose_debug-%s.log" % today_str, 'a') as f:
        f.write(string+'\n')
    yield from client.send_message(debug_channel, string)

@asyncio.coroutine
def jose_debug(message, dbg_msg, flag=True):
    message_banner = '%s[%s]: %r' % (message.author, message.channel, message.content)
    dbg_msg = '%s -> %s' % (message_banner, str(dbg_msg))
    debug_logs.append(dbg_msg)
    yield from debug_log('%s : %s' % (time.strftime("%d-%m-%Y %H:%M:%S"), dbg_msg))
    if flag:
        yield from client.send_message(message.channel, "jdebug: {}".format(dbg_msg))


cantadas = [
    'ô lá em casa',
    'vc é o feijão do meu acarajé',
    'gate, teu cu tem air bag?? pq meu pau tá sem freio',
    'se merda fosse beleza você estaria toda cagada',
    'me chama de bombeiro e deixa eu apagar seu fogo com a minha mangueira',
    'tô no hospital esperando uma doaçao de coração, pq vc roubou o meu',
    'me chama de piraque e vamos pra minha casa',
    'me chama de gorila e deixa eu te sarrar no ritmo do seu coração',
    'meu nome é arlindo, mas pode me chamar de lindo pq perdi o ar quando te vi',
    'me chama de lula e deixa eu roubar seu coração',
    'espero que o seu dia seja tão bom quanto sua bunda',
    'chama meu pau de Jean Willys e deixa ele cuspir na sua cara',
    'deixe eu ser a bala do seu Hamilton e acertar seu coração',
    'me chama de terrorista e deixa eu explodir dentro de você',
    'me chama de lava jato e me deixa te taxar de tão linde',
]

elogios = [
    "você é linde! <3",
    "sabia que você pode ser alguém na vida?",
    "eu acredito em você",
    'vc é FODA',
    'Parabéns',
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
    'CABALO IMUNDO',
    'HIJO DE PUTA',
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

aviaos = [
    'https://www.aboutcar.com/car-advice/wp-content/uploads/2011/02/Spoiler.jpg',
    'http://i.imgur.com/eL2hUyd.jpg',
    'http://i.imgur.com/8kS03gI.jpg',
    'http://i.imgur.com/Zfb05Qh.jpg',
    'http://i.imgur.com/w8Tp5z2.jpg',
    'http://i.imgur.com/ptpQdQx.jpg',
    'http://i.imgur.com/szx1S9n.jpg',
    'http://i.imgur.com/GG3zk49.jpg',
    'http://i.imgur.com/9Jq6oo6.jpg',
    'http://i.imgur.com/AIbjvX7.jpg',
]

@asyncio.coroutine
def show_help(message):
    yield from client.send_message(message.author, JOSE_HELP_TEXT)

@asyncio.coroutine
def show_gambling_full(message):
    yield from client.send_message(message.author, GAMBLING_HELP_TEXT)

@asyncio.coroutine
def show_gambling(message):
    yield from client.send_message(message.author, GAMBLING_HELP_TEXT_SMALL)

@asyncio.coroutine
def show_top(message):
    yield from client.send_message(message.channel, "BALADINHA TOPPER %s %s" % (
        (":joy:" * random.randint(1,5)),
        (":ok_hand:" * random.randint(1,6))))

@asyncio.coroutine
def check_roles(correct, rolelist):
    #for role in rolelist:
    #    if role.name == correct:
    #        return True
    #return False

    c = [role.name == correct for role in rolelist]
    return True in c

@asyncio.coroutine
def random_emoji(maxn):
    return ''.join((str(emoji.random_emoji()) for i in range(maxn)))

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

rodei_teu_cu = make_func("RODEI MEU PAU NO TEU CU")
show_noabraco = make_func("não vou abraçar")
show_tampa = make_func("A DO TEU CU\nHÁ, TROLEI")
show_vtnc = make_func("OQ VC DISSE?\nhttp://i.imgur.com/Otky963.jpg")
show_shit = make_func("tbm amo vc humano <3")
show_version = make_func("José v%s b%d" % (JOSE_VERSION, JOSE_BUILD))
show_emule = make_func("http://i.imgur.com/GO90sEv.png")
show_frozen_2 = make_func('http://i.imgur.com/HIcjyoW.jpg')
pong = make_func('pong')

show_tijolo = make_func("http://www.ceramicabelem.com.br/produtos/TIJOLO%20DE%2006%20FUROS.%209X14X19.gif")
show_mc = make_func("https://cdn.discordapp.com/attachments/202055538773721099/203989039504687104/unknown.png")
show_vinheta = make_func('http://prntscr.com/bvcbju')
show_agira = make_func("http://docs.unity3d.com/uploads/Main/SL-DebugNormals.png")
show_casa = make_func("https://thumbs.dreamstime.com/z/locais-de-trabalho-em-um-escrit%C3%B3rio-panor%C3%A2mico-moderno-opini%C3%A3o-de-new-york-city-das-janelas-tabelas-pretas-e-cadeiras-de-couro-59272285.jpg")

meme_ratelimit = make_func("http://i.imgur.com/P6bDtR9.gif")
meme_dank_memes = make_func("http://i.imgur.com/Fzk4jfl.png")

@asyncio.coroutine
def str_xor(s,t):
    return "".join(chr(ord(a)^ord(b)) for a,b in zip(s,t))

JCRYPT_KEY = 'vcefodaparabensfrozen2meuovomeuovinhoayylmaogordoquaseexploderindo'

class Context:
    def __init__(self, message):
        self.rtime = time.time()
        self.message = message

@asyncio.coroutine
def parse_id(data, message):
    '''
    <@196461455569059840>
    <@!162819866682851329>
    '''
    if data[0:2] == '<@':
        if data[2] == '!':
            return data[3:-1]
        else:
            return data[2:-1]
    else:
        yield from jose_debug(message, "error parsing id %s" % data)
        return

class Extension:
    def __init__(self, cl):
        self.client = cl
        self.current = None
        self.loop = cl.loop

    @asyncio.coroutine
    def say(self, msg):
        yield from self.client.send_message(self.current.channel, msg)

    @asyncio.coroutine
    def debug(self, msg, flag=True):
        yield from jose_debug(self.current, msg, flag)

    @asyncio.coroutine
    def recv(self, msg):
        self.current = msg

    @asyncio.coroutine
    def rolecheck(self, correct_role):
        c = [role.name == correct_role for role in self.current.author.roles]
        if not (True in c):
            raise je.PermissionError()
        else:
            return True

    def noasync(self, func, args):
        asyncio.async(func(*args), loop=self.loop)
