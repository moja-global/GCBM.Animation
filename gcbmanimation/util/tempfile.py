from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory

temp_dir = TemporaryDirectory()

def mktmp(**kwargs):
    return NamedTemporaryFile("w", dir=temp_dir.name, delete=False, **kwargs).name
