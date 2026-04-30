---
name: packify
description: Serialize Python data structures to/from bytes for reliable storage, transmission, and API integration. Handles complex nested data, custom objects, and ensures deterministic serialization. Use when users need to save, send, or convert data — whether they mention serialization, packing, or simply need to store/transfer complex Python structures.
---

# Packify

Universal serialization for Python data structures to/from bytes.

## When to Use

- Serialize complex, nested data structures for storage or transmission
- Support custom types via the `Packable` protocol
- Ensure deterministic, version-independent serialization

## Quick Start

```python
import packify

# Serialize to bytes
packed: bytes = packify.pack(data)

# Deserialize from bytes
data = packify.unpack(packed, inject={})  # inject provides custom types
```

### Supported Types

Built-in: `int`, `bool`, `float`, `Decimal`, `str`, `bytes`, `bytearray`, `NoneType`, `list`, `tuple`, `set`, `dict`

All types can be nested arbitrarily.

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
- **Error handling**: Raises `UsageError` for invalid types/missing dependencies
