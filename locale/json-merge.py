import sys
import json

def main(args):
    basefile = args[1]
    langfile = args[2]

    basejson, langjson = None, None
    with open(basefile, 'r') as f:
        print("load basejson", basefile)
        basejson = json.load(f)

    with open(langfile, 'r') as f:
        print("load langfile", langfile)
        langjson = json.load(f)

    # best merge ever!!!
    for entry in basejson:
        if entry not in langjson:
            langjson[entry] = basejson[entry]

    i = 0
    print('{')
    for key in langjson:
        val = langjson[key]
        dk = json.dumps(key).replace('\n', '\\n')
        dv = json.dumps(val).replace('\n', '\\n')
        if i == len(langjson)-1:
            print("\t%s: %s" % (dk, dv))
        else:
            print("\t%s: %s," % (dk, dv))
        i += 1
    print('}')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
