#!/usr/bin/env python3

import io

import discord
import aiohttp

from random import randint
from discord.ext import commands
from PIL import Image
from .common import Cog


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


class Datamosh(Cog):
    """Datamosh command(s)."""
    @commands.command()
    async def datamosh(self, ctx, url: str, iterations: int = 10):
        """Datamosh an image.

        Sometimes the result given by `j!datamosh` doesn't have any visualization,
        that means it broke the file and you need to try again.
        """

        if iterations > 129:
            await ctx.send('lul')
            return

        await self.jcoin.pricing(ctx, self.prices['OPR'])

        data = await get_data(url)

        source_image = io.BytesIO(data.getvalue())
        try:
            img = Image.open(data)
        except Exception as err:
            await ctx.send(f'Error opening image with Pillow({err!r})')
            return

        if img.format in ['JPEG', 'JPEG 2000']:
            # read the image, copy into a buffer for manipulation
            width, height = img.size

            if width > 4096 or height > 2048:
                await ctx.send("High resolution to work on(4096x2048 is the hard limit)")
                return

            future = self.bot.loop.run_in_executor(None, datamosh_jpg, \
                source_image, iterations)

            output_image = await future

            # send file
            output_file = discord.File(output_image, 'datamoshed.jpg')
            await ctx.send('datamoshed:', file=output_file)

            # done
            output_image.close()
        elif img.format in ['PNG']:
            await ctx.send("*no PNG support*")
        elif img.format in ['GIF']:
            await ctx.send("*no GIF support*")
        else:
            await ctx.send("Formato %s: desconhecido", (img.format,))

def setup(bot):
    bot.add_cog(Datamosh(bot))
