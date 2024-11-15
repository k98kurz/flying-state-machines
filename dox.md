# flying_state_machines

## Classes

### `Transition`

#### Annotations

- from_state: Enum | str
- to_state: Enum | str
- on_event: Enum | str
- probability: float
- hooks: list[Callable[[Transition]]]

#### Methods

##### `__init__(from_state: Enum | str, on_event: Enum | str, to_state: Enum | str, probability: float = 1.0, hooks: list[Callable[[Transition]]] = []) -> None:`

##### `pack() -> bytes:`

Serialize to bytes using packify.

##### `@classmethod unpack(data: bytes, hooks: list[Callable[[Transition]]] = None, inject: dict = {}) -> Transition:`

Deserialize from bytes using packify. Inject dependencies as necessary, e.g. the
Enum classes representing states or events.

##### `add_hook(hook: Callable[[Transition, Any]]) -> None:`

Adds a hook for when the Transition occurs.

##### `remove_hook(hook: Callable[[Transition, Any]]) -> None:`

Removes a hook if it had been previously added.

##### `trigger(data: Any = None) -> None:`

Triggers all hooks.

##### `@classmethod from_any(from_states: type[Enum] | list[str], event: Enum | str, to_state: Enum | str, probability: float = 1.0) -> list[Transition]:`

Makes a list of Transitions from any valid state to a specific state, each with
the given probability.

##### `@classmethod to_any(from_state: Enum | str, event: Enum | str, to_states: type[Enum] | list[str], total_probability: float = 1.0) -> list[Transition]:`

Makes a list of Transitions from a specific state to any valid state, with the
given cumulative probability.

### `FSM`

#### Annotations

- rules: set[Transition]
- initial_state: Enum | str
- current: Enum | str
- previous: Enum | str | None
- next: Enum | str | None
- _valid_transitions: dict[Enum | str, dict[Enum | str, list[Transition]]]
- _event_hooks: dict[Enum | str, list[Callable]]

#### Methods

##### `__init__() -> None:`

##### `add_event_hook(event: Enum | str, hook: Callable[[Enum | str, FSM, Any], bool]) -> None:`

Adds a callback that fires before an event is processed. If any callback returns
False, the event is cancelled.

##### `remove_event_hook(event: Enum | str, hook: Callable[[Enum | str, FSM, Any], bool]) -> None:`

Removes a callback that fires before an event is processed.

##### `add_transition_hook(transition: Transition, hook: Callable[[Transition]]) -> None:`

Adds a callback that fires after a Transition occurs.

##### `remove_transition_hook(transition: Transition, hook: Callable[[Transition]]) -> None:`

Removes a callback that fires after a Transition occurs.

##### `would(event: Enum | str) -> tuple[Transition]:`

Given the current state of the machine and an event, return a tuple of possible
Transitions.

##### `can(event: Enum | str) -> bool:`

Given the current state of the machine and an event, return whether the event
can be processed.

##### `input(event: Enum | str, data: Any = None) -> Enum | str:`

Attempt to process an event, returning the resultant state.

##### `touched() -> str:`

Represent the state machine as a Flying Spaghetti Monster.


