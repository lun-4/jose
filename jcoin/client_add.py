#!/usr/bin/env python3.6

import sys
import os
import hashlib
import time
import base64

import asyncio
import asyncpg

import config


def generate_id():
    return base64.b64encode(str(time.time()).encode()).decode()


def generate_token(client_id):
    data = f'{client_id}{os.urandom(1000)}'
    return hashlib.sha256(data.encode()).hexdigest()


async def main():
    conn = await asyncpg.create_pool(**config.db)
    name = sys.argv[1]
    description = sys.argv[2]
    level = int(sys.argv[3])

    client_id = generate_id()
    token = generate_token(client_id)

    await conn.execute("""
    INSERT INTO clients (client_id, token, client_name,
    description, auth_level) VALUES ($1, $2, $3, $4, $5)
    """, client_id, token, name, description, level)

    print(f'Add client {name!r}')
    print(f'Client ID: {client_id}')
    print(f'Client Token: {token}')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
