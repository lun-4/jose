"""
jcoin/josecoin.py - josecoin meme module

a webserver that makes transactions between users and stuff
"""
import logging
import hashlib

from sanic import Sanic
from sanic import response

from .db import Database

app = Sanic()
log = logging.getLogger(__name__)


class AccountType:
    USER = 0
    TAXBANK = 1

def empty_account(user_id, acc_type, password):
    salt = os.urandom(128)
    salt = base64.b64encode(salt)
    h = hashlib.sha512(salt + password).hexdigest()
    base = {
        'id': user_id,
        'type': acc_type,
        'password': h,
    }
    if acc_type == AccountType.USER:
        return {**base, **{

        }}
    else:
        return {**base, **{

        }}

@app.route('/', methods=['GET'])
async def index(request):
    return response.text('henlo yes')


@app.route('/create', methods=['POST'])
async def create_account(request):
    uid = request.json['user_id']
    acc_type = request.json['type']
    password = request.json['password']

    acc = await get_acc(uid)
    if not acc:
        return response.json({
            'success': False,
            'status': 'you already have an account'
            })

    await coll.insert_one(empty_account(uid, acc_type, password))

    return response.json({
        'success': True
    })


@app.route('/tx', methods=['POST'])
async def transaction(request):
    pass


@app.route('/history', methods=['GET'])
async def fetch_history(request):
    pass


@app.route('/recent', methods=['GET'])
async def recent_txs(request):
    """Returns recent transactions."""
    # TODO: actually return some transactions, but that's for way later
    # SOLUTION: lol
    # TODO: how many transactions to return?
    # SOLUTION: PAGINATION!!!!
    limit = response.json['limit']
    tx =
    return request.json({'success': True,
                        'transactions': {'1': amount: '69.69',
                                                to: None }})


@app.route('/gdp', methods=['GET'])
async def get_gdp(request):
    """yeah this returns gdp haha"""
    return request.json({'success': True,
                         'gdp': 0.00})

@app.route('/meme')
async def meme(request):
    return request.text('meme')

if __name__ == '__main__':
    # hehe 6969
    # h aha ye syyes.
    app.run(host='0.0.0.0', port=8696)
