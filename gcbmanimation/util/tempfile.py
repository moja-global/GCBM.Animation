import os
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from glob import glob

__temp_dir = TemporaryDirectory()

def cleanup(pattern=None):
    if pattern:
        for fn in glob(os.path.join(__temp_dir.name, pattern)):
            os.remove(fn)
    else:
        __temp_dir = TemporaryDirectory()

def mktmp(**kwargs):
    '''
    Gets a unique temporary file name located in the gcbmanimation temp directory.
    Accepts any arguments supported by NamedTemporaryFile. Temporary files will be
    deleted when the interpreter exits.
    '''
    return NamedTemporaryFile("w", dir=__temp_dir.name, delete=False, **kwargs).name
