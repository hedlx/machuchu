#!/usr/bin/env python
from __future__ import print_function

import re

class Numerator:
    def __init__(self):
        self._hash = {}
        self._list = []
        self._cnt = 0
    def __getitem__(self, item):
        if item not in self._hash:
            self._hash[item] = self._cnt
            self._list.append(item)
            self._cnt += 1
        return self._hash[item]
    def items(self):
        return self._list

include_re = re.compile('^\s*#\s*include\s+"([^"]+)"\s+$')

def preprocess_one(text, files, fname):
    with open(fname,"r") as f:
        if files[fname] != 0:
            text.append("#line %d %d\n" % (1, files[fname]))
        for n,line in enumerate(f,1):
            match = include_re.match(line)
            if match:
                preprocess_one(text, files, match.groups()[0])
                text.append("#line %d %d\n" % (n, files[fname]))
            else:
                text.append(line)

def preprocess(fname):
    text = []
    files = Numerator()
    preprocess_one(text, files, fname)
    return ("".join(text), files.items())

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "FILE")
        exit(1)
    text, files = preprocess(sys.argv[1])
    print(text)
    print('/* Used files:')
    for i, f in enumerate(files):
        print(" *  %d: %s" % (i, f))
    print(" */")
