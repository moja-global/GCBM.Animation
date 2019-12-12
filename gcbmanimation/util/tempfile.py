import os
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from glob import glob

class TempFileManager:
    
    _temp_dir = TemporaryDirectory()
    _no_cleanup = []

    def __init__(self):
        raise RuntimeError("Not instantiable")

    @staticmethod
    def cleanup(pattern="*"):
        '''
        Manually cleans up files in the gcbmanimation temp directory matching the
        specified glob pattern, or all files by default. Remaining files will still
        be deleted when the interpreter exits.

        Arguments:
        'pattern' -- the file pattern to delete, or all files by default.
        '''
        for fn in glob(os.path.join(TempFileManager._temp_dir.name, pattern)):
            if fn not in TempFileManager._no_cleanup:
                os.remove(fn)

    @staticmethod
    def mktmp(no_manual_cleanup=False, **kwargs):
        '''
        Gets a unique temporary file name located in the gcbmanimation temp directory.
        Accepts any arguments supported by NamedTemporaryFile. Temporary files will be
        deleted when the interpreter exits.

        Arguments:
        'no_manual_cleanup' -- prevents this file from being deleted by calls to
            TempFileManager.cleanup()
        '''
        temp_file_name = NamedTemporaryFile("w", dir=TempFileManager._temp_dir.name, delete=False, **kwargs).name
        if no_manual_cleanup:
            TempFileManager._no_cleanup.append(temp_file_name)

        return temp_file_name
