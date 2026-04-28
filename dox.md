# flying_state_machines

## Classes

### `Transition`

Represents a rule for transitioning between states within a Finite State
Machine. Specifies the states from and to which the transition occurs, the event
that triggers the transition, and optionally the probability of the transition
(for PFSMs/Markov chains). Probabilities can be static floats or determined
dynamically by a callback that accepts a context dict.

#### Annotations

- from_state: Enum | str
- to_state: Enum | str
- on_event: Enum | str
- probability: float | Callable[[dict], float]
- hooks: list[Callable[[Transition, dict, Any]]]

#### Methods

##### `__init__(from_state: Enum | str, on_event: Enum | str, to_state: Enum | str, probability: float | Callable[[dict], float] = 1.0, hooks: list[Callable[[Transition, dict, Any]]] = None) -> None:`

Initializaton of a Transition instance performs an array of sanity checks to
ensure the library is being used properly. Raises `AssertionError` if any
necessary precondition check fails, i.e. invalid `from_state`, `to_state`,
`event`, `probability`, or `hooks`.

##### `pack() -> bytes:`

Serialize to bytes using packify.

##### `@classmethod unpack(data: bytes, /, *, hooks: list[Callable[[Transition, dict, Any]]] = [], inject: dict = {}) -> Transition:`

Deserialize from bytes using packify. Inject dependencies as necessary, e.g. the
Enum classes representing states or events.

##### `add_hook(hook: Callable[[Transition, dict, Any]]) -> None:`

Adds a hook for when the Transition occurs. Any context and data passed to
`trigger` will be passed to the hook.

##### `remove_hook(hook: Callable[[Transition, dict, Any]]) -> None:`

Removes a hook if it had been previously added.

##### `trigger(context: dict = None, data: Any = None) -> None:`

Triggers all hooks with the given context and data.

##### `@classmethod from_any(from_states: type[Enum] | list[str], event: Enum | str, to_state: Enum | str, probability: float | Callable[[dict], float] = 1.0) -> list[Transition]:`

Makes a list of Transitions from any valid state to a specific state, each with
the given probability.

##### `@classmethod to_any(from_state: Enum | str, event: Enum | str, to_states: type[Enum] | list[str], total_probability: float | Callable[[dict], float] = 1.0) -> list[Transition]:`

Makes a list of Transitions from a specific state to any valid state, with the
given cumulative probability if `total_probability` is a float or with
`total_probability` assigned to each Transition if it is callable.

### `FSM`

Finite State Machine base. Should be used by subclassing with `rules` and
`initial_state` set as class attributes.

#### Annotations

- rules: set[Transition]
- initial_state: Enum | str
- current: Enum | str
- previous: Enum | str | None
- next: Enum | str | None
- context: dict
- _valid_transitions: dict[Enum | str, dict[Enum | str, list[Transition]]]
- _event_hooks: dict[Enum | str, list[Callable]]

#### Methods

##### `__init__(context: dict = None) -> None:`

Initialization of an FSM subclass instance performs an array of sanity checks to
ensure the library is being used properly. Raises `AssertionError` if any
necessary precondition checks fail, e.g. invalid `rules` or `initial_state`.
Also processes `rules` to seed internal structures to enable Markov chain
behaviors. Accepts an optional `context` dict that is passed to transition hooks
and any callable `transition.probability`.

##### `add_event_hook(event: Enum | str, hook: Callable[[Enum | str, FSM, Any], bool]) -> None:`

Adds a callback that fires before an event is processed. If any callback returns
False, the event is cancelled.

##### `remove_event_hook(event: Enum | str, hook: Callable[[Enum | str, FSM, Any], bool]) -> None:`

Removes a callback that fires before an event is processed.

##### `add_transition_hook(transition: Transition, hook: Callable[[Transition, dict, Any]]) -> None:`

Adds a callback that fires after a Transition occurs. `self.context` and any
data passed to `input` will be passed to `transition.trigger`, which will be
passed to the hook.

##### `remove_transition_hook(transition: Transition, hook: Callable[[Transition, dict, Any]]) -> None:`

Removes a callback that fires after a Transition occurs.

##### `would(event: Enum | str) -> tuple[Transition]:`

Given the current state of the machine and an event, return a tuple of possible
Transitions.

##### `can(event: Enum | str) -> bool:`

Given the current state of the machine and an event, return whether the event
can be processed.

##### `input(event: Enum | str, data: Any = None) -> Enum | str:`

Attempt to process an event, returning the resultant state. If multiple valid
transitions exist, select one according to the probabilities, passing
`self.context` when calling any callable transition probability. Call all
relevant hooks, passing `self`, `event`, and `data` to event hooks and
`self.context` and `data` to transition hooks. If an event hook returns `False`,
the transition is canceled.

##### `touched() -> str:`

Represent the state machine as a Flying Spaghetti Monster.

##### `pack() -> bytes:`

Serialize to bytes using packify.

##### `@classmethod unpack(data: bytes, /, *, event_hooks: dict[Enum | str, list[Callable[[Enum | str, FSM, Any], bool]]] = {}, transition_hooks: dict[Transition, list[Callable[[Transition, Any]]]] = {}, inject: dict = {}) -> FSM:`

Deserialize from bytes using packify. Inject dependencies as necessary, e.g. the
Enum classes representing states or events.

## Functions

### `version() -> str:`


