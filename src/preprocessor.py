#!/usr/bin/env python3

import re
import os

INCLUDE_RE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s*$')
ONCE_RE = re.compile(r"^\s*#\s*pragma\s+once\s*$")
VERSION_RE = re.compile(r"^\s*#\s*version\s+(.*)$")


class Preprocessor:
    def __init__(self, fname: str) -> None:
        self.version: None | list[str] = None
        self._shift = 0
        self.text_lines: list[str] = []
        self.fnames: list[str] = []
        self.fcontents: list[list[str]] = []
        self._once: set[str] = set()

        self._one(fname)
        self.text = "\n".join(self.text_lines)

    def _one(self, fname: str) -> None:
        if fname in self._once:
            return
        contents = open(fname, "r").read().split("\n")

        if fname not in self.fnames:
            self.fnames.append(fname)
            self.fcontents.append(contents)
        findex = self.fnames.index(fname)

        if findex != 0:
            self.text_lines.append(
                f"#line {self._shift} {findex} /* {fname} */"
            )

        for n, line in enumerate(contents):
            match = ONCE_RE.match(line)
            if match:
                self.text_lines.append(f"/* {line} */")
                self._once.add(fname)
                continue
            match = INCLUDE_RE.match(line)
            if match:
                path = os.path.dirname(fname)
                if path != "":
                    path += "/"
                self._one(path + match.groups()[0])
                self.text_lines.append(
                    f"#line {self._shift + n + 1} {findex} "
                    f"/* {fname}:{n + 1} */"
                )
                continue
            match = VERSION_RE.match(line)
            if match:
                self.version = re.split(r" +", match.groups()[0])
                self._shift = int(self.version[1:2] == ["es"])
                self.text_lines.append(f"/* {line} */")
                self.text_lines.insert(0, line)
                self.text_lines.insert(1, f"#line {self._shift} 0")
                continue
            self.text_lines.append(line)


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "FILE")
        exit(1)
    p = Preprocessor(sys.argv[1])
    print(p.text)
    print("/* Used files:")
    for i, f in enumerate(p.fnames):
        print(f" *  {i}: {f}")
    print(" */")


if __name__ == "__main__":
    main()
