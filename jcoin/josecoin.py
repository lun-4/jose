"""
jcoin/josecoin.py - josecoin meme module

a webserver that makes transactions between users and stuff
"""
import logging
import asyncio

from sanic import Sanic
from sanic import response

app = Sanic()
log = logging.getLogger(__name__)


class AccountType:
    USER = 0
    TAXBANK = 1


@app.route('/', methods=['GET'])
async def index(request):
    return response.text('henlo yes')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = app.create_server(host='0.0.0.0', port=8080)

    try:
        loop.create_task(server)
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
    except:
        log.exception('Closing loop.')
        loop.close()
