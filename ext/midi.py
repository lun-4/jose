# -*- coding: utf-8 -*-
import io
import logging
import time

import discord
from discord.ext import commands
from midiutil import MIDIFile

from .common import Cog


LETTER_PITCH_MAP = {
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
    async def make_midi(self, tempo: int, data: str) -> MIDIFile:
        midi_file = MIDIFile(1)
        
        channels = data.split('|')
        
        midi_file.addTrackName(0, 0, 'beep boop')
        midi_file.addTempo(0, 0, tempo)
        
        for c in range(len(channels)):
            log.info(f'creating MIDI channel out of "{data}"')

            for index, letter in enumerate(channels[c]):
                note = LETTER_PITCH_MAP.get(letter)
                if note is None:
                    continue

                # modifiers are characters before the actual
                # letter note that modify the note's duration
                try:
                    duration = get_duration(channels[c][index - 1])
                except IndexError:
                    duration = 1

                await self.loop.run_in_executor(
                    None, midi_file.addNote, 0, c, note, index, duration, 100
                )

            log.info('successfully created MIDI channel')
        return midi_file

    @commands.command()
    async def midi(self, ctx: commands.Context, tempo: int=120, *, data: str):
        """
        Convert text to MIDI.

        The actual letter-to-note map? idk :shrug:
        """
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
