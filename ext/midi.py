# -*- coding: utf-8 -*-
import io
import logging
import time

import discord
from discord.ext import commands
from midiutil import MIDIFile

from .common import Cog


LETTER_PITCH_MAP = {    
    " ": 0,
    "-": 0,

    "a": 34,
    "A": 35,
    "b": 36,
    "B": 37,
    "c": 38,
    "C": 39,
    "d": 40,
    "D": 41,
    "e": 42,
    "E": 43,
    "f": 44,
    "F": 45,
    "g": 46,
    "G": 47,
    "h": 48,
    "H": 49,
    "i": 50,
    "I": 51,
    "j": 52,
    "J": 53,
    "k": 54,
    "K": 55,
    "l": 56,
    "L": 57,
    "m": 58,
    "M": 59,
    "n": 60,
    "N": 61,
    "o": 62,
    "O": 63,
    "p": 64,
    "P": 65,
    "q": 66,
    "Q": 67,
    "r": 68,
    "R": 69,
    "s": 70,
    "S": 71,
    "t": 72,
    "T": 73,
    "u": 74,
    "U": 75,
    "v": 76,
    "V": 77,
    "w": 78,
    "W": 79,
    "x": 80,
    "X": 81,
    "y": 82,
    "Y": 83,
    "z": 84,
    "Z": 85,

    "0": 86,
    "1": 87,
    "2": 88,
    "3": 89,
    "4": 90,
    "5": 91,
    "6": 92,
    "7": 93,
    "8": 94,
    "9": 95,
}


log = logging.getLogger(__name__)


def get_duration(letter):
    return {
        ' ': 2,
        ',': 3,
        '.': 4,
        '^': 6,
        '\'': 8,
        '$': 12,
        '"': 16
    }.get(letter, 1)


class MIDI(Cog):
    async def add_channel(self, midi_file, channel_index, channel_data):
        for index, letter in enumerate(channel_data):
            note = LETTER_PITCH_MAP.get(letter)
            if note is None:
                continue

            # modifiers are characters before the actual
            # letter note that modify the note's duration
            try:
                duration = get_duration(channel_data[index - 1])
            except IndexError:
                duration = 1

            await self.loop.run_in_executor(None, midi_file.addNote,
                                            0, channel_index, note,
                                            index, duration, 100)

    async def make_midi(self, tempo: int, data: str) -> MIDIFile:
        midi_file = MIDIFile(1)

        midi_file.addTrackName(0, 0, 'beep boop')
        midi_file.addTempo(0, 0, tempo)

        channel_datas = data.split('|')

        log.info(f'creating MIDI out of "{data}"')

        for channel_index, channel_data in enumerate(channel_datas):
            await self.add_channel(midi_file, channel_index, channel_data)

        log.info('successfully created MIDI')
        return midi_file

    async def download_data(self, message: discord.Message) -> str:
        """Checks if an attachment is viable to be used as
        MIDI input and downloads it."""
        if not message.attachments:
            raise self.SayException('You did not attach a file to '
                                    'use as MIDI input!, `j!help midi`')

        attachment = message.attachments[0]

        if not attachment.filename.endswith('.txt'):
            raise self.SayException('File must be a .txt!')

        # see if the file is bigger than 20 KiB as we don't want
        # to download huge files
        if attachment.size >= 20 * 1024:
            raise self.SayException('File is too large. '
                                    'Your file may only be 20KiB big.')

        log.info('downloading file to use as MIDI input. '
                 f'{attachment.size} bytes large.')
        buffer = io.BytesIO()
        await attachment.save(buffer)

        return buffer.getvalue().decode('utf-8')

    @commands.command()
    async def midi(self, ctx: commands.Context,
                   tempo: int=120, *, data: str=None):
        """
        Convert text to MIDI. Multiple channels can be used by splitting text with |.
        Letters are converted to their pitch values using a mapping.

        Full documentation about it is not provided, read the code at
        https://github.com/lnmds/jose/blob/master/ext/midi.py

        To give longer input than a discord message allows you may upload a .txt file of up to 20 KiB.
        """
        if data is None:
            try:
                data = await self.download_data(ctx.message)
            except Exception as err:
                log.exception('error downloading file at midi')
                raise self.SayException('We had an error while downloading '
                                        'the file, are you sure it is text?')

        before = time.monotonic()
        midi_file = await self.make_midi(tempo, data)
        duration = (time.monotonic() - before) * 1000

        if midi_file is None:
            return await ctx.send('Failed to generate a MIDI file!')

        file = io.BytesIO()
        await self.loop.run_in_executor(None, midi_file.writeFile, file)
        file.seek(0)

        wrapped = discord.File(file, filename='boop.midi')
        await ctx.send(f'Took {duration:.3f}ms!', file=wrapped)


def setup(bot: commands.Bot):
    bot.add_cog(MIDI(bot))
