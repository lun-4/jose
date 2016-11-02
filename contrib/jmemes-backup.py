#!/usr/bin/env python3

import urllib.request
import sys
import pickle
import re
import os.path

urllib.request.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
args = sys.argv

url_regex = '((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)'

blacklist = [
    'discord', 'youtube', 'youtu.be', 'puu.sh'
]

def is_blacklist(url):
    for el in blacklist:
        if el in url: return True
    return False

def download_meme(key, meme, folder):
    print('get %s' % key)

    if re.match(url_regex, meme['data']) and not is_blacklist(meme['data']):
        _filename = meme['data'].split('/')[-1]
        filename = "%s-%s" % (key, _filename)
        path = "%s/%s" % (folder, filename)
        print("download %s" % meme['data'])
        try:
            if not os.path.isfile(path):
                urllib.request.urlretrieve(meme['data'], path)
        except Exception as e:
            print("ERROR %r" % e)
    else:
        path = '%s/%s.txt' % (folder, key.replace('/', '\\'))
        with open(path, 'w') as f:
            f.write(meme['data'])

def main():
    memes = pickle.load(open('ext/josememes.db', 'rb'))
    for key in memes:
        download_meme(key, memes[key], args[1])

if __name__ == '__main__':
    main()
