import sqlite3
import json
import sys

conn = sqlite3.connect('jose.db')

def do_stmt(stmt, params=None):
    global conn
    cur = conn.cursor()
    if params is None:
        cur.execute(stmt)
    else:
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
    cur = do_stmt('SELECT serverid FROM markovdb')
    server_ids = [row[0] for row in cur.fetchall()]
    return set(server_ids)

def main(args):
    resfile = args[1]
    amnt = do_stmt("SELECT COUNT(*) FROM markovdb").fetchall()[0]
    serverids = get_all_serverids()

    print("%d messages" % amnt[0])

    msgs = 0
    with open(resfile, 'w') as sqlfile:
        for serverid in serverids:
            messages = server_messages(serverid, 10000)

            for message in messages:
                sqlfile.write("INSERT INTO markovdb (serverid, message) VALUES (%s, %s);\n" % \
                    (serverid, json.dumps(message)))
                msgs += 1

    print("Done! from %d to %d messages." % (amnt[0], msgs))

if __name__ == '__main__':
    sys.exit(main(sys.argv))
