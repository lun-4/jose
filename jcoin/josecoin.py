import time
import pickle
import logging

import sys
sys.path.append("..")
import josecommon as jcommon

JOSECOIN_VERSION = '0.6'

import decimal
decimal.getcontext().prec = 3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.addHandler(jcommon.handler)
logger.addHandler(jcommon.log_channel_handler)

data = {}
lock = False
jose_id = jcommon.JOSE_ID

LEDGER_PATH = 'jcoin/josecoin-5.journal'

def lockdb():
    '''Locks JoséCoin database, no transactions can be done'''
    global lock
    lock = True
    return lock

def unlockdb():
    global lock
    lock = False
    return lock

def ledger_data(fpath, data):
    with open(fpath, 'a') as f:
        f.write(data)
    return

def empty_acc(name, amnt, acctype=0):
    if acctype == 0:
        # user account
        return {
            'type': 0,
            'amount': amnt,
            'name': name,

            # personal bank thing
            'fakemoney': decimal.Decimal(0),
            'actualmoney': decimal.Decimal(0),

            # statistics for taxes
            'taxpaid': decimal.Decimal(0),

            # j!steal stuff
            'times_stolen': 0,
            'success_steal': 0,

            # from what taxbank are you loaning from
            'loaning_from': None,

            # last tbank to get interest from
            'interest_tbank': '',
        }
    elif acctype == 1:
        # tax bank
        return {
            'type': 1,
            'name': name,
            'amount': decimal.Decimal(-1),
            'taxes': decimal.Decimal(0),
            'loans': {},
        }

def new_acc(id_acc, name, init_amnt=None, acctype=0):
    if lock:
        return False, 'database is locked'

    if init_amnt is None and acctype == 0:
        init_amnt = decimal.Decimal('3')

    if id_acc in data:
        return False, 'account already exists'

    data[id_acc] = empty_acc(name, init_amnt, acctype)
    return True, 'account made with success'

def get(id_acc):
    if lock:
        return False, 'database is locked'

    if id_acc not in data:
        return False, 'account doesn\'t exist, read `j!docs jcoin`'
    return True, data[id_acc]

def gen():
    for acc_id in data:
        acc = data[acc_id]
        yield (acc_id, acc['name'], acc['amount'])

def transfer(id_from, id_to, amnt, file_name=None):
    if amnt < 0.001:
        return False, 'very small transfer.'

    if file_name is None:
        file_name = LEDGER_PATH

    if lock:
        return False, 'database is locked'

    amnt = decimal.Decimal(str(amnt))

    if amnt <= 0:
        return False, "transfering zero or less than is prohibited"

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

    if acc_to['type'] == 1 or acc_from['type'] == 1:
        # tax transfer

        if acc_to['type'] == 1:
            if not (acc_from['amount'] >= amnt):
                return False, "account doesn't have enough funds to make this transaction"

            acc_to['taxes'] += amnt
            acc_from['taxpaid'] += amnt
            acc_from['amount'] -= amnt

        elif acc_from['type'] == 1:
            if not (acc_from['taxes'] >= amnt):
                return False, "account doesn't have enough funds to make this transaction"

            acc_from['taxes'] -= amnt
            acc_to['amount'] += amnt

        ledger_data(file_name, "%f;TAXTR;%s;%s;%s\n" % \
            (time.time(), id_from, id_to, amnt))

    else:
        if not (acc_from['amount'] >= amnt):
            return False, "account doesn't have enough funds to make this transaction"

        acc_to['amount'] += amnt
        acc_from['amount'] -= amnt

        ledger_data(file_name, "%f;TR;%s;%s;%s\n" % \
            (time.time(), id_from, id_to, amnt))

    return True, "%s was sent from %s to %s" % (amnt, acc_from['name'], acc_to['name'])

def ensure_exist(acc_id, attribute, val):
    if attribute not in data[acc_id]:
        data[acc_id][attribute] = val

def load(fname):
    global data
    try:
        with open(fname, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        return False, repr(e)

    remove_itbank = False

    for acc_id in data:
        acc = data[acc_id]
        if not isinstance(acc, dict):
            if isinstance(acc, str):
                if acc_id == 'interest_tbank':
                    jcommon.logger.info("!!")
                    remove_itbank = True
                    continue
                elif acc_id[0] == '_':
                    continue

            return False, ('%s is not an account, it is %r = %r' % (acc_id, type(acc), acc))

        if acc_id.startswith('tbank'):
            data[acc_id]['type'] = 1
        else:
            data[acc_id]['type'] = 0

        if data[acc_id]['type'] == 0:
            ensure_exist(acc_id, 'fakemoney', decimal.Decimal(0))
            ensure_exist(acc_id, 'actualmoney', decimal.Decimal(0))
            ensure_exist(acc_id, 'taxpaid', decimal.Decimal(0))
            ensure_exist(acc_id, 'times_stolen', 0)
            ensure_exist(acc_id, 'success_steal', 0)

            ensure_exist(acc_id, 'loaning_from', None)
            ensure_exist(acc_id, 'interest_tbank', '')

        if data[acc_id]['type'] == 1:
            ensure_exist(acc_id, 'name', acc_id)
            ensure_exist(acc_id, 'amount', decimal.Decimal(-1))
            ensure_exist(acc_id, 'loans', {})
            ensure_exist(acc_id, 'taxes', decimal.Decimal(0))

            if 'taxpayers' in data[acc_id]:
                del data[acc_id]['taxpayers']

    if remove_itbank:
        del data['interest_tbank']

    data[jose_id] = empty_acc('jose-bot', decimal.Decimal('Inf'), 0)
    return True, "load %s" % fname

def save(fname):
    global data
    try:
        with open(fname, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        return False, repr(e)

    #ledger_data(fname.replace('db', 'journal'), '%f;SAVE;%r\n' % (time.time(), data))
    return True, "save %s" % fname

async def jcoin_control(userid, amount):
    return transfer(userid, jose_id, amount, LEDGER_PATH)

async def raw_save():
    res = save('jcoin/josecoin.db')
    return res
