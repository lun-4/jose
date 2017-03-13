import sqlite3
import sys

conn = sqlite3.connect('jose.db')

def do_stmt(stmt, params=None, stmt_num=-1):
    global conn
    cur = conn.cursor()
    try:
        if params is None:
            cur.execute(stmt)
        else:
            cur.execute(stmt, params)
    except Exception as err:
        print("%r at statment %d: %r" % (err, stmt_num, stmt))
    return cur

def main(args):
    sql_file = args[1]

    print("Restoring jose.db markovdb table...")

    stmts = 0
    with open(sql_file, 'r') as sqlfile:
        for line in sqlfile.readlines():
            if not stmts % 1000:
                print("%d statements..." % stmts)
            do_stmt(line, None, stmts)
            stmts += 1

    print("Commiting to file...")
    conn.commit()

    print("%d statements executed and commited with success!" % stmts)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
