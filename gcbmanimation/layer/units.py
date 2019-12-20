from enum import Enum

class Units(Enum):
    
    Blank    = 1,   ""
    Tc       = 1,   "tC/yr"
    Ktc      = 1e3, "KtC/yr"
    Mtc      = 1e6, "MtC/yr"
    TcPerHa  = 1,   "tC/ha/yr"
    KtcPerHa = 1e3, "KtC/ha/yr"
    MtcPerHa = 1e6, "MtC/ha/yr"
