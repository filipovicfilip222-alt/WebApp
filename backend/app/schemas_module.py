"""Compatibility module that exposes the Pydantic schemas defined in schemas.py."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_schemas_path = Path(__file__).resolve().with_name("schemas.py")
_schemas_spec = spec_from_file_location("app._schemas_impl", _schemas_path)

if _schemas_spec is None or _schemas_spec.loader is None:
    raise ImportError(f"Unable to load schemas module from {_schemas_path}")

_schemas_module = module_from_spec(_schemas_spec)
_schemas_spec.loader.exec_module(_schemas_module)

for _name in dir(_schemas_module):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_schemas_module, _name)

__all__ = [_name for _name in globals() if not _name.startswith("_")]