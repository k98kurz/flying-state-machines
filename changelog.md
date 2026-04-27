## 0.2.1

- Fixed mutable default argument in `Transition.__init__` which caused hooks to be shared across instances
- Added more docstrings to `Transition` and `FSM` classes and their methods
- Corrected type annotations for Transition hook parameters

## 0.2.0

- Added `Transition.pack` and `Transition.unpack` for serialization using packify
- Added `FSM.pack` and `FSM.unpack` for serialization using packify
- Added `FSM.can` to determine if an event can be processed
