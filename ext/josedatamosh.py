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

import josecommon as jcommon
import jauxiliar as jaux
import joseerror as je

class JoseDatamosh(jcommon.Extension, jaux.Auxiliar):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        jaux.Auxiliar.__init__(self, cl)

    async def ext_load(self):
        return

    async def ext_unload(self):
        return

    async def c_datamosh(self, message, args):
        '''
        `!datamosh <url>` - *Datamoshing.*
        ```
        Resultados do !datamosh:
         * ou o resultado é imcompreensível
         * ou o resultado é legalzinho
         * ou não tem visualização(o datamosh quebrou o arquivo)
        ```
        Formatos recomendados(*testados*): JPG, PNG
        Formatos NÃO recomendados: BMP, GIF
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
            Image.open(data)
        except:
            await self.say("Erro abrindo imagem com o Pillow")
            return

        # read the image, copy into a buffer for manipulation
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
