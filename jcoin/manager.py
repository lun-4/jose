"""
manager.py - manage transaction commiting from the queue
to Postgres.
"""
import asyncio
import logging

log = logging.getLogger(__name__)


class TransferManager:
    def __init__(self, app):
        self.app = app
        self._queue = []

        self.txlock = asyncio.Lock()
        self.app.loop.create_task(self.commit_task())

    @property
    def db(self):
        return self.app.db

    async def commit_all(self):
        await self.txlock
        # First, process batch of transactions
        for tx in self._queues:
            pass

        # Then, insert them into the log
        await self.db.executemany("""
        INSERT INTO transactions (sender, receiver, amount)
        VALUES ($1, $2, $3)
        """, ((a, b, str(c)) for (a, b, c) in self._queue))

        self._queue = []
        self.txlock.release()

    async def commit_task(self):
        try:
            while True:
                await self.commit()
                await asyncio.sleep(20)
        except:
            log.exception('error in commit task')

    async def queue(self, txdata):
        await self.txlock
        self._queue.append(txdata)
        self.txlock.release()
