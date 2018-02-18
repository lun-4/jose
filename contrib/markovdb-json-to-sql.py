import json
import sys
import sqlite3

def main(args):
    if args[1] != 'auto':
        jobj = None
        with open(args[1], 'r') as f:
            jobj = json.loads(f.read())

        res = []
        for serverid in jobj:
            serverobj = jobj[serverid]
            for message in serverobj:
                res.append("INSERT INTO markovdb (serverid, message) VALUES (%s, %s);" % (serverid, json.dumps(message)))

        print('\n'.join(res))
    else:
        conn = sqlite3.connect('jose.db')
        jobj = None
        with open('markov-database.json', 'r') as f:
            jobj = json.loads(f.read())

        cur = conn.cursor()
        for serverid in jobj:
            serverobj = jobj[serverid]
            for message in serverobj:
                cur.execute("INSERT INTO markovdb (serverid, message) VALUES (?, ?);", \
                    (serverid, message))
            conn.commit()

        conn.close()
        print("done")

if __name__ == '__main__':
    sys.exit(main(sys.argv))
