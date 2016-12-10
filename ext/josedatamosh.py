#!/usr/bin/env python3

import discord
import asyncio
import aiohttp
import sys
import io
sys.path.append("..")

from PIL import Image
import os
from random import SystemRandom
randint = SystemRandom().randint

import jauxiliar as jaux
import joseerror as je

class JoseDatamosh(jaux.Auxiliar):
    def __init__(self, cl):
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return True, ''

    async def ext_unload(self):
        return True, ''

    async def c_datamosh(self, message, args):
        '''
        `!datamosh <url> [iterations]` - *Datamoshing.* (3JC/datamosh)
        ```
Formatos recomendados(*testados*): JPG, PNG
Formatos NÃO recomendados: BMP, GIF

Resultados de fotos jogadas ao !datamosh:
 * ou o resultado é imcompreensível
 * ou o resultado é legalzinho
 * ou não tem visualização(o datamosh quebrou o arquivo)
        ```
        '''

        auth = await self.jc_control(message.author.id, 3)
        if not auth:
            await self.say("jc.auth: não autorizado")
            return

        iterations = 10
        if len(args) > 2:
            try:
                iterations = int(args[2])
            except Exception as e:
                await self.say("Erro parseando argumentos(%r)." % e)
                return

        if iterations > 129:
            await self.say("*engracadinho*")
            return

        data = io.BytesIO()
        with aiohttp.ClientSession() as session:
            async with session.get(args[1]) as resp:
                data_read = await resp.read()
                data.write(data_read)

        def read_chunks(fh):
            while True:
                chunk = fh.read(4096)
                if not chunk:
                    break
                yield chunk

        source_image = io.BytesIO(data.getvalue())
        try:
            img = Image.open(data)
        except Exception as e:
            await self.say("Erro abrindo imagem com o Pillow(%r)" % e)
            return

        if img.format in ['JPEG', 'JPEG 2000']:
            # read the image, copy into a buffer for manipulation
            width, height = img.size

            if width > 1280 or height > 720:
                await self.say("Resolução muito grande(>720p)")
                return

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

            await self.client.send_file(message.channel, output_image, filename='datamosh.jpg', content='*Datamoshed*')

            output_image.close()
        elif img.format in ['PNG']:
            await self.say("*não tenho algoritmo pra PNG*\n*espera porra*\n é sério porra")
        elif img.format in ['GIF']:
            await self.say("*o sr esta de brincando comigo NAO VAI TE GIF NO DATAMOSH* é muito caro em relação a processamento NAO")
        else:
            await self.say("Formato desconhecido(%s)" % img.format)
