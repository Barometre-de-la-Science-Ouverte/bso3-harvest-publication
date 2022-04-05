import os


class OvhPath:
    """OVH does not store objects in a directory but using a path-like filename allow a similar result.
    This class standardizes the path-like syntax (Windows path sep \ and Unix path sep /)
    OvhPath(a,b,c,file) -> a/b/c/file
    """
    def __init__(self, *args):
        self.components = [str(e) for e in args]
    def __repr__(self) -> str:
        return "'" + '/'.join(self.components) + "'"
    def __str__(self) -> str:
        return '/'.join(self.components)
    def __eq__(self, other):
        if isinstance(other, OvhPath):
            return repr(self) == repr(other)
        return False
    def to_local(self):
        return os.path.join(*self.components)