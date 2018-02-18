#!/usr/bin/env python3

import sys

def parse(fn):
	data = {}
	with open(fn, 'r') as f:
		for line in f.readlines():
			d = line.split(';')
			#1469317695.540287;TR;202587271679967232;162819866682851329;7.400000
			if d[1] == 'TR':
				id_from = d[2]
				id_to = d[3]
				amnt = float(d[4])

				if not id_from in data:
					data[id_from] = 25
				if not id_to in data:
					data[id_to] = 25

				data[id_from] -= amnt
				data[id_to] += amnt

	return data

def main():
	args = sys.argv
	fname = args[1]
	data = parse(fname)
	for accid in data:
		print("<@%s> %.2fJC" % (accid, data[accid]))
	print(parse(fname))

main()
