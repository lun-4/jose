#!/usr/bin/python3

import sys
sys.path.append("/home/luna/jose-bot")

print(sys.path)
import josecommon as jc

def main():
    zelao_txt = open("zelao.txt", 'r')
    new_zelao_txt = ""
    for line in zelao_txt.readlines():
        new_zelao_txt += jc.speak_filter(line)
    zelao_txt.close()

    new_zelao_file = open("zelao.txt", 'w')
    new_zelao_file.write(new_zelao_txt)
    new_zelao_file.close()

if __name__ == '__main__':
    main()
