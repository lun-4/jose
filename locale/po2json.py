import sys
import polib

def main(args):
    infile = args[1]
    try:
        outfile = args[2]
    except:
        outfile = '%s.json' % infile

    po = polib.pofile(infile)
    print('{')
    for entry in po:
        # best
        print("\t%r: \"%s\"," % (entry.msgid, entry.msgstr))
    print('}')

if __name__ == '__main__':
    sys.exit(main(sys.argv))
