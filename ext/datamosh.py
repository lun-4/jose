import io
import time
from random import randint

import discord
import aiohttp
from discord.ext import commands
from PIL import Image

from .common import Cog


async def get_data(url):
    """Read data from an URL and return
    a `io.BytesIO` instance of the data gathered
    in that URL.
    """
    data = io.BytesIO()
    with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data_read = await resp.read()
            data.write(data_read)

    return data


def read_chunks(fh):
    """Split a file handler into 4 kilobyte chunks."""
    while True:
        chunk = fh.read(4096)
        if not chunk:
            break
        yield chunk


def datamosh_jpg(source_image: 'io.BytesIO', iterations: int) -> 'io.BytesIO':
    """Datamosh a JPG file.

    This changes random blocks in the file
    to generate a datamoshed image.
    """
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
    """Datamosh."""
    @commands.command()
    async def datamosh(self, ctx, url: str, iterations: int = 1):
        """Datamosh an image.

        Sometimes the result given by `j!datamosh` doesn't have any thumbnail,
        that means it actually broke the file and you need to try again(and
        hope it doesn't break the file again).
        """

        if iterations > 10:
            return await ctx.send('too much lul')

        await self.jcoin.pricing(ctx, self.prices['OPR'])

        dt1 = time.monotonic()
        data = await get_data(url)
        dt2 = time.monotonic()
        ddelta = round((dt2 - dt1) * 1000, 6)

        source_image = io.BytesIO(data.getvalue())
        try:
            img = Image.open(data)
        except Exception as err:
            raise self.SayException('Error opening image with'
                                    f' Pillow(`{err!r}`)')

        if img.format in ['JPEG', 'JPEG 2000']:
            # read the image, copy into a buffer for manipulation
            width, height = img.size

            if width > 4096 or height > 2048:
                await ctx.send("High resolution to work on"
                               "(4096x2048 is the hard limit)")
                return

            future = self.bot.loop.run_in_executor(None, datamosh_jpg,
                                                   source_image, iterations)

            t1 = time.monotonic()
            output_image = await future
            t2 = time.monotonic()
            pdelta = round((t2 - t1) * 1000, 5)

            # send file
            output_file = discord.File(output_image, 'datamoshed.jpg')
            await ctx.send(f'took {ddelta}ms on download.\n'
                           f'{pdelta}ms on processing.', file=output_file)

            # done
            output_image.close()
        elif img.format in ['PNG']:
            await ctx.send('no support for png')
        elif img.format in ['GIF']:
            await ctx.send('no support for gif')
        else:
            await ctx.send(f'Unknown format: `{img.format}`')


def setup(bot):
    bot.add_cog(Datamosh(bot))
