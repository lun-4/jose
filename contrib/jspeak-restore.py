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

def main(args):
    sql_file = args[1]

    print("Restoring jose.db markovdb table...")

    stmts = 0
    with open(sql_file, 'r') as sqlfile:
        for line in sqlfile.readlines():
            if not stmts % 1000:
                print("%d statements..." % stmts)
            do_stmt(line)
            stmts += 1

    print("%d statements executed" % stmts)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
