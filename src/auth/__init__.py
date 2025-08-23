"""Auth package exports and path adjustments."""

import os as _os, sys as _sys
_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _root not in _sys.path:
	_sys.path.append(_root)

__all__ = []