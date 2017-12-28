"""
Stolen code from Mousey,
Thanks FrostLuma
"""
import asyncio
import functools
import time

from typing import List

class Table:
    def __init__(self, *column_titles: str):
        self._rows = [column_titles]
        self._widths = []

        for index, entry in enumerate(column_titles):
            self._widths.append(len(entry))

    def _update_widths(self, row: tuple):
        for index, entry in enumerate(row):
            width = len(entry)
            if width > self._widths[index]:
                self._widths[index] = width

    def add_row(self, *row: str):
        """
        Add a row to the table.
        .. note :: There's no check for the number of items entered, this may cause issues rendering if not correct.
        """
        self._rows.append(row)
        self._update_widths(row)

    def add_rows(self, *rows: List[str]):
        for row in rows:
            self.add_row(*row)

    def _render(self):
        def draw_row(row_):
            columns = []

            for index, field in enumerate(row_):
                # digits get aligned to the right
                if field.isdigit():
                    columns.append(f" {field:>{self._widths[index]}} ")
                    continue

                # make sure the codeblock this will end up in won't get escaped
                field = field.replace('`', '\u200b`')

                # regular text gets aligned to the left
                columns.append(f" {field:<{self._widths[index]}} ")

            return "|".join(columns)

        # column title is centered in the middle of each field
        title_row = "|".join(f" {field:^{self._widths[index]}} " for index, field in enumerate(self._rows[0]))
        separator_row = "+".join("-" * (width + 2) for width in self._widths)

        drawn = [title_row, separator_row]
        # remove the title row from the rows
        self._rows = self._rows[1:]

        for row in self._rows:
            row = draw_row(row)
            drawn.append(row)

        return "\n".join(drawn)

    async def render(self, loop: asyncio.AbstractEventLoop=None):
        """Returns a rendered version of the table."""
        loop = loop or asyncio.get_event_loop()

        func = functools.partial(self._render)
        return await loop.run_in_executor(None, func)

class Timer:
    """Context manager to measure how long the indented block takes to run."""

    def __init__(self):
        self.start = None
        self.end = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    async def __aenter__(self):
        return self.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

    def __str__(self):
        return f'{self.duration:.3f}ms'

    @property
    def duration(self):
        """Duration in ms."""
        return (self.end - self.start) * 1000
