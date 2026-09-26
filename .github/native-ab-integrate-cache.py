"""Keep filesystem hashing out of the native hot call path."""
from pathlib import Path
p = Path("packing/src/sqpack/fractional/native_ab_runtime.py")
s = p.read_text()
s = s.replace("\ndef source_digest() -> str:\n", "\n@lru_cache(maxsize=1)\ndef source_digest() -> str:\n", 1)
s = s.replace('def build(*, core_only: bool = False) -> dict:\n',
              'def build(*, core_only: bool = False) -> dict:\n    source_digest.cache_clear()\n', 1)
p.write_text(s)
