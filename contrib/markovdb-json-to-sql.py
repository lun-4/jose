import json
import sys

def main(args):
    jobj = None
    with open(args[1], 'r') as f:
        jobj = json.loads(f.read())

    res = []
    for serverid in jobj:
        serverobj = jobj[serverid]
        for message in serverobj:
            res.append("INSERT INTO markovdb (serverid, message) VALUES (%s, %r);" % (serverid, message))

    print('\n'.join(res))

if __name__ == '__main__':
    sys.exit(main(sys.argv))
