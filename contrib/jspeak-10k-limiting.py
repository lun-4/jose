import sqlite3
import json

conn = sqlite3.connect('jose.db')
result = sqlite3.connect('jose2.db')

def do_stmt(stmt, params=None):
    global conn
    cur = conn.cursor()
    cur.execute(stmt, params)
    conn.commit()
    return cur

def server_messages(serverid, limit=None):
    cur = do_stmt('SELECT message FROM markovdb WHERE serverid=?', (serverid,))
    rows = [row[0] for row in cur.fetchall()]

    if limit is not None:
        pos = len(rows) - limit
        rows = rows[pos:]

    return rows

def get_all_serverids():
    server_ids = do_stmt('SELECT serverid FROM markovdb')
    return set(server_ids)

def main():
    serverids = get_all_serverids()
    amnt = do_stmt("SELECT COUNT(*) FROM markovdb")

    print("%d servers")

    msgs = 0
    with open('limit.sql', 'w') as sqlfile:
        for serverid in serverids:
            messages = server_messages(serverid, 10000)

            for message in messages:
                sqlfile.write("INSERT INTO markovdb (serverid, message) VALUES (%s, %s);\n" % \
                    (serverid, json.dumps(message)))
                msgs += 1

    print("Done! from %d to %d messages." % (amnt, msgs))

if __name__ == '__main__':
    sys.exit(main())
