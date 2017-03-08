import sqlite3
import json
import sys

conn = sqlite3.connect('jose.db')

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

def main(args):
    serverid = args[1]
    resfile = args[2]

    msgs = 0
    with open(resfile, 'w') as sqlfile:
        messages = server_messages(serverid, 10000)

        for message in messages:
            sqlfile.write("INSERT INTO markovdb (serverid, message) VALUES (%s, %s);\n" % \
                (serverid, json.dumps(message)))
            msgs += 1

    print("Done! made a dump of %d messages." % (msgs,))

if __name__ == '__main__':
    sys.exit(main(sys.argv))
