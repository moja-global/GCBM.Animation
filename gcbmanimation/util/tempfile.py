from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory

temp_dir = TemporaryDirectory()

def mktmp(**kwargs):
    '''
    Gets a unique temporary file name located in the gcbmanimation temp directory.
    Accepts any arguments supported by NamedTemporaryFile. Temporary files will be
    deleted when the interpreter exits.
    '''
    return NamedTemporaryFile("w", dir=temp_dir.name, delete=False, **kwargs).name
