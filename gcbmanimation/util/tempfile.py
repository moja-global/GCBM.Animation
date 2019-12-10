import os
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from glob import glob

class TempFileManager:
    
    _temp_dir = TemporaryDirectory()

    def __init__(self):
        raise RuntimeError("Not instantiable")

    @staticmethod
    def cleanup(pattern=None):
        if pattern:
            for fn in glob(os.path.join(TempFileManager._temp_dir.name, pattern)):
                os.remove(fn)
        else:
            TempFileManager._temp_dir = TemporaryDirectory()

    @staticmethod
    def mktmp(**kwargs):
        '''
        Gets a unique temporary file name located in the gcbmanimation temp directory.
        Accepts any arguments supported by NamedTemporaryFile. Temporary files will be
        deleted when the interpreter exits.
        '''
        return NamedTemporaryFile("w", dir=TempFileManager._temp_dir.name, delete=False, **kwargs).name
