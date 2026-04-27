## 0.2.1

- Fixed mutable default argument in `Transition.__init__` which caused hooks to be shared across instances

## 0.2.0

- Added `Transition.pack` and `Transition.unpack` for serialization using packify
- Added `FSM.pack` and `FSM.unpack` for serialization using packify
- Added `FSM.can` to determine if an event can be processed
