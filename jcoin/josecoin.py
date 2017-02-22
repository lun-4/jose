import time
import pickle

import sys
sys.path.append("..")
import josecommon as jcommon

JOSECOIN_VERSION = '0.6'

import decimal
decimal.getcontext().prec = 3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('José.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

JOSECOIN_HELP_TEXT = '''JoseCoin(%s) é a melhor moeda que o josé pode te oferecer!

Toda mensagem enviada tem 1%% de chance de conseguir 1, 1.2, 2, 2.5, 5, 5.1 ou 7.4JC$ para o autor da mensagem
Alguns comandos pedem JC$ em troca da sua funcionalidade(*comandos nsfw incluídos*)

!conta - cria uma nova conta
!enviar mention quantidade - envia josecoins para alguém
!saldo [mention] - mostra o quanto que tal conta tem em josecoins

''' % JOSECOIN_VERSION

data = {}
jose_id = jcommon.JOSE_ID

LEDGER_PATH = 'jcoin/josecoin-5.journal'

def ledger_data(fpath, data):
    with open(fpath, 'a') as f:
        f.write(data)
    return

def empty_acc(name, amnt):
    return {
        'amount': amnt,
        'name': name
    }

def new_acc(id_acc, name, init_amnt=None):
    if init_amnt is None:
        # the readjust gave so little prices I need to lower this
        init_amnt = decimal.Decimal('3')

    if id_acc in data:
        return False, 'account already exists'

    data[id_acc] = empty_acc(name, init_amnt)
    return True, 'account made with success'

def get(id_acc):
    if id_acc not in data:
        return False, 'account doesn\'t exist'
    return True, data[id_acc]

def gen():
    for acc_id in data:
        acc = data[acc_id]
        yield (acc_id, acc['name'], acc['amount'])

def transfer(id_from, id_to, amnt, file_name):
    amnt = decimal.Decimal(str(amnt))

    if amnt < 0:
        return False, "values less than zero aren't permitted"

    if amnt == 0:
        return False, "sending zero is prohibited"

    if not (id_from in data):
        return False, "account to get funds doesn't exist"

    if not (id_to in data):
        return False, "account to send funds doesn't exist"

    try:
        acc_from = data[id_from]
        acc_to = data[id_to]
    except Exception as e:
        return False, str(e)

    logger.info("%s > %.6fJC > %s", \
        acc_from['name'], amnt, acc_to['name'])

    if not (acc_from['amount'] >= amnt):
        return False, "account doesn't have enough funds to make this transaction"

    acc_to['amount'] += amnt
    acc_from['amount'] -= amnt

    ledger_data(file_name, "%f;TR;%s;%s;%s\n" % (time.time(), id_from, id_to, amnt))

    return True, "%s was sent from %s to %s" % (amnt, acc_from['name'], acc_to['name'])

def load(fname):
    global data
    try:
        with open(fname, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        return False, str(e)

    data[jose_id] = empty_acc('jose-bot', decimal.Decimal('1000000'))
    #ledger_data(fname.replace('db', 'journal'), '%f;LOAD;%r\n' % (time.time(), data))
    return True, "load %s" % fname

def save(fname):
    global data
    try:
        with open(fname, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        return False, str(e)

    #ledger_data(fname.replace('db', 'journal'), '%f;SAVE;%r\n' % (time.time(), data))
    return True, "save %s" % fname

async def jcoin_control(userid, amount):
    return transfer(userid, jose_id, amount, LEDGER_PATH)

async def raw_save():
    res = save('jcoin/josecoin.db')
    return res
