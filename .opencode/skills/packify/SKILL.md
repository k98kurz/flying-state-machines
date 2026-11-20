---
name: packify
description: Serialize and deserialize Python data structures to and from bytes for storage, transmission, or API integration. Handles arbitrarily nested built-ins and custom objects implemented via the `Packable` protocol, with deterministic, version-independent output and exact type preservation. Use this skill when the user needs to save, send, encode, decode, pack, unpack, or convert complex Python structures to bytes or back, even if they don't mention serialization by name.
license: ISC
compatibility: Requires Python 3.10+
metadata:
  version: "0.4.0"
  last-updated: "2026-10-17"
  author: "Jonathan Voss"
  repository: "https://github.com/k98kurz/packify"
---

# Packify

Universal serialization for Python data structures to/from bytes.

## Quick Start

```python
import packify

# Serialize to bytes
packed: bytes = packify.pack(data)

# Deserialize from bytes
data = packify.unpack(packed, inject={})  # inject provides custom types
```

## Supported Types

Built-in: `int`, `bool`, `float`, `Decimal`, `str`, `bytes`, `bytearray`, `NoneType`, `list`, `tuple`, `set`, `dict`

All types can be nested arbitrarily. Ints of effectively any size are supported
(0.4.0+). Values with magnitude below `2**32` pack into a compact 1-, 2-, or
4-byte field with no separate size prefix. Larger values carry a length prefix:
one byte for those needing up to 255 bytes, or an extended 4-byte prefix for
those needing 256 or more (absolute value >= `2**2040`). The 4-byte prefix caps
a serialized integer at `2**32 - 1` bytes.

## Named Tuples

Convert named tuples to/from regular tuples:

```python
from collections import namedtuple
import packify

Point = namedtuple('Point', ['x', 'y'])

original = Point(1, 2)
packed = packify.pack(tuple(original))
unpacked = Point(*packify.unpack(packed))
```

**Note**: Recursive serialization doesn't support named tuples nested within
other data structures. For custom types in nested structures, use the `Packable`
protocol instead.

## Custom Types

Implement the `Packable` protocol:

```python
from dataclasses import dataclass
import packify

@dataclass
class User:
    name: str
    id: int

    def pack(self) -> bytes:
        return packify.pack({'name': self.name, 'id': self.id})

    @classmethod
    def unpack(cls, data: bytes, inject: dict = {}):
        fields = packify.unpack(data, inject=inject)
        return cls(**fields)

users = [User('Alice', 1), User('Bob', 2)]
packed = packify.pack(users)
unpacked = packify.unpack(packed, inject={'User': User})
# Or: unpacked = packify.unpack(packed, inject={**globals()})
```

## Key Behaviors

- **Deterministic**: Dicts/sets sorted for consistent output
- **Type-safe**: Exact types preserved (tuple vs list, etc.)
- **Dependency injection**: Custom types required in `inject` when unpacking
- **Error handling**: `pack` raises `TypeError` for non-serializable types
  and `OverflowError` for values whose serialized length exceeds the 32-bit
  limit; `unpack` raises `ValueError` for truncated/corrupt bytes and
  `DependencyError` when a `Packable` dependency is missing or invalid

## Gotchas

- Only exact built-in types are serialized recursively. Subclasses such as
  `IntEnum`, `int`/`str` subclasses, and `namedtuple` raise `TypeError`;
  convert them (`int(v)`, `tuple(v)`) or implement `Packable`.
- Truncated or corrupt input raises `ValueError` with a descriptive message
  from `unpack`; bare `struct.error` never escapes.
- Values whose serialized length reaches 2**32 bytes raise `OverflowError`
  from `pack`; the 32-bit length prefixes cannot encode them.
- `unpack` resolves `Packable` dependencies only from `inject`; module
  `globals()` are not searched.
