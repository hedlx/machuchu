#!/usr/bin/env python
from __future__ import print_function

import re
import os

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s+$')
ONCE_RE = re.compile(r"^\s*#\s*pragma\s+once\s+$")


class Numerator(object):
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


def preprocess_one(text, files, once, fname):
    if fname in once:
        return
    with open(fname, "r") as f:
        if files[fname] != 0:
            text.append("#line %d %d\n" % (1, files[fname]))
        for n, line in enumerate(f, 1):
            match = ONCE_RE.match(line)
            if match:
                once.add(fname)
                continue
            match = INCLUDE_RE.match(line)
            if match:
                path = os.path.dirname(fname)
                if path != "":
                    path += "/"
                preprocess_one(text, files, once, path + match.groups()[0])
                text.append("#line %d %d\n" % (n, files[fname]))
                continue
            text.append(line)


def preprocess(fname):
    text = []
    once = set()
    files = Numerator()
    preprocess_one(text, files, once, fname)
    return ("".join(text), files.items())


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "FILE")
        exit(1)
    text, files = preprocess(sys.argv[1])
    print(text)
    print("/* Used files:")
    for i, f in enumerate(files):
        print(" *  %d: %s" % (i, f))
    print(" */")


if __name__ == "__main__":
    main()
