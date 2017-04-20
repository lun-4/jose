#!/usr/bin/env python3

import aiohttp
import sys
import io
sys.path.append("..")
import josecommon as jcommon

from PIL import Image
from random import SystemRandom
randint = SystemRandom().randint

import jauxiliar as jaux

async def get_data(url):
    data = io.BytesIO()
    with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data_read = await resp.read()
            data.write(data_read)

    return data

def read_chunks(fh):
    while True:
        chunk = fh.read(4096)
        if not chunk:
            break
        yield chunk

def datamosh_jpg(source_image, iterations):
    output_image = io.BytesIO()
    for chunk in read_chunks(source_image):
        output_image.write(chunk)

    # herald the destroyer
    iters = 0
    steps = 0
    block_start = 100
    block_end = len(source_image.getvalue()) - 400
    replacements = randint(1, 30)

    source_image.close()

    while iters <= iterations:
        while steps <= replacements:
            pos_a = randint(block_start, block_end)
            pos_b = randint(block_start, block_end)

            output_image.seek(pos_a)
            content_from_pos_a = output_image.read(1)
            output_image.seek(0)

            output_image.seek(pos_b)
            content_from_pos_b = output_image.read(1)
            output_image.seek(0)

            # overwrite A with B
            output_image.seek(pos_a)
            output_image.write(content_from_pos_b)
            output_image.seek(0)

            # overwrite B with A
            output_image.seek(pos_b)
            output_image.write(content_from_pos_a)
            output_image.seek(0)

            steps += 1
        iters += 1

    return output_image

class JoseDatamosh(jaux.Auxiliar):
    def __init__(self, _client):
        jaux.Auxiliar.__init__(self, _client)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_datamosh(self, message, args, cxt):
        '''
        `j!datamosh <url> [iterations]` - *Datamoshing.*
        Sometimes the result given by `j!datamosh` doesn't have any visualization,
        that means `j!datamosh` broke the file and you need to try again.
        '''

        iterations = 10
        if len(args) > 2:
            try:
                iterations = int(args[2])
            except Exception as err:
                await cxt.say("Erro parseando argumentos(%r).", (err,))
                return

        if iterations > 129:
            await cxt.say("*engracadinho*")
            return

        await self.jcoin_pricing(cxt, jcommon.OP_TAX_PRICE)

        data = await get_data(args[1])

        source_image = io.BytesIO(data.getvalue())
        try:
            img = Image.open(data)
        except Exception as err:
            await cxt.say("Erro abrindo imagem com o Pillow(%r)", (err,))
            return

        if img.format in ['JPEG', 'JPEG 2000']:
            # read the image, copy into a buffer for manipulation
            width, height = img.size

            if width > 4096 or height > 2048:
                await cxt.say("High resolution to work on(4096x2048 is the hard limit)")
                return

            future = self.client.loop.run_in_executor(None, datamosh_jpg, \
                source_image, iterations)

            output_image = await future

            # send file
            await self.client.send_file(message.channel, \
                output_image, filename='datamosh.jpg', content='*Datamoshed*')

            # done
            output_image.close()
        elif img.format in ['PNG']:
            await cxt.say("*no PNG support*")
        elif img.format in ['GIF']:
            await cxt.say("*no GIF support*")
        else:
            await cxt.say("Formato %s: desconhecido", (img.format,))

def setup(bot):
    return JoseDatamosh(bot)
