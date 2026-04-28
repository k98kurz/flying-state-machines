## 0.3.0

- Added dynamic transition probabilities: `Transition.probability` now accepts
  `float | Callable[[dict], float]`
- Added `context` dict parameter to `FSM` for storing arbitrary state data
  accessible to callable probabilities and hooks
- Updated transition hook signatures from `(transition, data)` to
  `(transition, context, data)`
- Added serialization support for callable probabilities (stores function names,
  reconstructed via `inject` parameter)
- FSM `context` dict is now serialized/deserialized along with machine state
- Probability validation now skips callables during initialization (treats as 0)
- Added test coverage for dynamic probabilities, context passing to hooks, and
  serialization with callables/context
- Updated packify dependency from 0.2.2 to 0.3.1

## 0.2.1

- Fixed mutable default argument in `Transition.__init__` which caused hooks to be shared across instances
- Added more docstrings to `Transition` and `FSM` classes and their methods
- Corrected type annotations for Transition hook parameters

## 0.2.0

- Added `Transition.pack` and `Transition.unpack` for serialization using packify
- Added `FSM.pack` and `FSM.unpack` for serialization using packify
- Added `FSM.can` to determine if an event can be processed
