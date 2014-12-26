import posix
import errno


class Updater(object):
    def __init__(self, files):
        self.files = {f: posix.stat(f).st_ctime for f in files}

    def check(self):
        res = False
        for f, old in self.files.items():
            try:
                new = posix.stat(f).st_ctime
                if old != new:
                    self.files[f] = new
                    res = True
            except OSError as e:
                if e.errno == errno.ENOENT:
                    return False
                raise e
        return res
