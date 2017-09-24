import time
import logging

from discord.ext import commands

from .common import Cog

log = logging.getLogger()

async def get_duration(letter):
    return {
        ' ': 2,
        ',': 3,
        '.': 4,
    }.get(letter, 1)

async def get_note(letter):
    # TODO: letter_pitch_mapping
    return letter_pitch_mapping.get(letter)

class MIDI(Cog):
    async def make_midi(self, tempo, data):
        midifile = MIDIFile(1)

        midifile.addTrackName(0, 0, 'ur gay')
        midifile.addTempo(0, 0, tempo)

        log.info('Making MIDI out of %r', data)

        for index, letter in enumerate(data):
            note = await get_note(letter)
            if note is None:
                continue

            # modifiers are characters before the actual
            # letter note that modify the note's duration

            try:
                duration = await get_duration(data[index - 1])
            except IndexError: duration = 1

            await self.loop.run_in_executor(None, midifile.add_one,\
                0, 0, note, index, duration, 100)


        return midifile

    @commands.command()
    @commands.is_owner()
    async def midi(self, ctx, tempo: int=120, *, data: str):
        """Convert text to MIDI.
        
        The actual letter-to-note map? idk :shrug:
        """
        t1 = time.monotonic()
        midifile = await self.make_midi(tempo, data)
        t2 = time.monotonic()

        if midifile is None:
            return await ctx.send('Failed to generate MIDI file')

        delta = round((t2 - t1) * 1000, 2)

        fp = io.BytesIO()
        await self.loop.run_in_executor(None, midifile.writeFile, fp)

        wrapped = discord.File(fp, filename='gay.midi')
        await ctx.send(f'took {delta}ms', file=wrapped)

def setup(bot):
    bot.add_cog(MIDI(bot))

