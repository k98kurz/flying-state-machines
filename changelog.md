## 0.3.1

- Added ability to specify a random function for probabilistic transitions
- Removed `/, *,` from method signatures to remove previous keyword-only constraints
- Added CLI for exporting agent skill to AI coding environments (generic,
  OpenCode, Claude Code, Cursor, Codex): `fsm [skill|opencode|claude|cursor|codex]`

## 0.3.0

- Added `context` dict property to FSM (and init param) for arbitrary state data
  - `FSM.input` now passes `self.context` to `transition.trigger`
  - `context` included in `pack()` and `unpack()`
- Added dynamic transition probabilities:
  - `Transition.probability` is now `float | Callable[[dict], float]`
  - `Transition.from_any` and `Transition.to_any` can also accept callables
  - `FSM.input` calls `transition.probability(self.context)` if relevant
  - Updated transition hook signatures from `(transition, data)` to
    `(transition, context, data)`
  - Added serialization support for callable probabilities (stores function names,
    reconstructed via `inject` parameter)
  - `FSM.__init__` cumulative probability validation skips callables
- Added test coverage for all new features
- Updated packify dependency from 0.2.2 to 0.3.1

## 0.2.1

- Fixed mutable default argument in `Transition.__init__` which caused hooks to be shared across instances
- Added more docstrings to `Transition` and `FSM` classes and their methods
- Corrected type annotations for Transition hook parameters

## 0.2.0

- Added `Transition.pack` and `Transition.unpack` for serialization using packify
- Added `FSM.pack` and `FSM.unpack` for serialization using packify
- Added `FSM.can` to determine if an event can be processed
