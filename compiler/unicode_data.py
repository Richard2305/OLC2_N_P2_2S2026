"""Build Unicode scalar case tables from Python's bundled Unicode database.

Only language-independent data is generated here; source-program strings are
transformed by the AArch64 runtime. Expanding mappings such as ß -> SS are kept.
"""
from functools import lru_cache

@lru_cache(maxsize=2)
def case_mapping(which):
    convert = str.upper if which == "upper" else str.lower
    return tuple((codepoint, convert(chr(codepoint)))
                 for codepoint in range(0x110000)
                 if not 0xD800 <= codepoint <= 0xDFFF and convert(chr(codepoint)) != chr(codepoint))
