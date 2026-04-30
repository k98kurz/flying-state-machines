## 0.3.0

### Core Features
- **Context-aware state management**: Added `context` dict property to FSM for arbitrary instance data
  - `FSM.input` passes `self.context` to `transition.trigger`
  - `context` included in `pack()` and `unpack()` serialization
- **Dynamic transition probabilities**: Probabilities can now be context-aware callables
  - `Transition.probability` accepts `float | Callable[[dict], float]`
  - `Transition.from_any` and `Transition.to_any` support callables
  - `FSM.input` calls `transition.probability(self.context)` when applicable
  - Serialization support for callable probabilities (stores function names, reconstructed via `inject`)
  - `FSM.__init__` skips probability validation for callables
- **Custom random functions**: Ability to specify deterministic random function for probabilistic transitions
  - Useful for testing and reproducible simulations

### API & Developer Experience
- **Simplified method signatures**: Removed `/, *,` keyword-only constraints for easier usage
- **AI agent integration**: Added CLI for exporting agent skills to AI coding environments
  - Commands: `fsm [skill|opencode|claude|cursor|codex]`
  - Supports generic, OpenCode, Claude Code, Cursor, and Codex formats

### Breaking Changes
- **Transition hook signatures**: Updated from `(transition, data)` to `(transition, context, data)`
  - Affects custom transition hook implementations

### Miscellaneous
- **Dependencies**: packify upgraded from 0.2.2 to 0.3.3
- **Testing**: Comprehensive test coverage for all new features (CLI tested manually)


## 0.2.1

- Fixed mutable default argument in `Transition.__init__` which caused hooks to be shared across instances
- Added more docstrings to `Transition` and `FSM` classes and their methods
- Corrected type annotations for Transition hook parameters


## 0.2.0

- Added `Transition.pack` and `Transition.unpack` for serialization using packify
- Added `FSM.pack` and `FSM.unpack` for serialization using packify
- Added `FSM.can` to determine if an event can be processed
