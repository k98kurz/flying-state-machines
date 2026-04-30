---
name: flying-state-machines
description: >
  Use this skill when the user needs to implement deterministic or probabilistic finite state machines (FSMs/Markov chains), state transitions, or game AI logic. Apply even for workflow automation, NPC behavior, or decision systems where state-based logic would help, even if they don't explicitly mention "FSM" or "state machine."
---

# Flying State Machines Agent Skill

Helps AI agents use the flying-state-machines library for deterministic and probabilistic finite state machines (FSMs/Markov chains).

## Quick Start

Create an FSM by subclassing `FSM` and defining `rules` and `initial_state`:

```python
from enum import Enum, auto
from flying_state_machines import FSM, Transition

class State(Enum):
    WAITING = auto()
    GOING = auto()

class Event(Enum):
    START = auto()
    STOP = auto()

class Machine(FSM):
    initial_state = State.WAITING
    rules = set([
        Transition(State.WAITING, Event.START, State.GOING),
        Transition(State.GOING, Event.STOP, State.WAITING),
    ])
```

Process events:
```python
machine = Machine()
machine.input(Event.START)  # Returns new state
machine.current              # State.GOING
machine.previous             # State.WAITING
```

## Core Concepts

**Accessing State**: An instance of an FSM subclass will have `current`, `next`, and `previous` properties.
  - `fsm.current` will always have the current state, starting with the `initial_state`.
  - `fsm.previous` has the state prior to the most recent transition, if any.
  - `fsm.next` is populated with the target state before event hooks fire.
    It remains populated if the transition is canceled, or is cleared after a successful transition.

**States and Events**: Use `Enum` or `str`. Enums are preferred for type safety.

**Transitions**: Define state changes with `Transition(from_state, event, to_state, probability=1.0)`.

**Context Dict**: Each FSM instance has `context` dict for storing arbitrary state data. Passed to hooks and dynamic probability callbacks.

**Hooks**: 
- **Event hooks**: Fire before state changes. Return `False` to cancel.
- **Transition hooks**: Fire after state changes occur.

## Common Patterns

### Deterministic Transitions

The example in the Quick Start section above shows a deterministic FSM.

### Probabilistic Transitions

```python
class Roulette(FSM):
    initial_state = 'safe'
    rules = set([
        Transition('safe', 'spin', 'safe', 5/6),
        Transition('safe', 'spin', 'dead', 1/6),
    ])
```

### Dynamic Probabilities (Context-Aware)

```python
def attack_probability(context: dict) -> float:
    return 1.0 if context.get('strength', 0) > 0.5 else 0.0

class Guard(FSM):
    initial_state = 'patrol'
    rules = set([
        Transition('patrol', 'see_enemy', 'attack', attack_probability),
        Transition('patrol', 'see_enemy', 'retreat', lambda ctx: 1.0 - attack_probability(ctx)),
    ])

guard = Guard(context={'strength': 0.8})
guard.input('see_enemy')  # Will attack
```

### Event Hooks (Can Cancel)

```python
def validate_condition(event, fsm, data) -> bool:
    return fsm.context.get('some_val', 1.0) > 0.5

# Can be added and removed
machine.add_event_hook(Event.START, validate_condition)
machine.remove_event_hook(Event.START, validate_condition)
```

### Transition Hooks (Cannot Cancel)

```python
transition = machine.would(Event.START)[0]
def log_transition(transition, context, data):
    print(f"{transition.from_state} -> {transition.to_state}")

# Can be added and removed
machine.add_transition_hook(transition, log_transition)
machine.remove_transition_hook(transition, log_transition)
```

### Batch Transitions with `from_any`/`to_any`

```python
class NPC(FSM):
    initial_state = State.IDLE
    rules = set([
        # From any state to specific state (e.g. abort to error)
        *Transition.from_any(State, Event.ERROR, State.ERROR, 1.0),
        # From specific state to any state (e.g. Markov chain)
        *Transition.to_any(State.IDLE, Event.WAKEUP, [State.ACTIVE, State.ALERT], 0.5),
    ])
```

### Custom Random Function

```python
def deterministic_random():
    return 0.3  # Always returns same value

machine = Machine(random=deterministic_random)
```

See the readme.md file for a concise implementation of a PRNG using sha256.

### Serialization

**Important**: Hooks and callables cannot be serialized. Must be re-supplied on unpack.

```python
# Pack
packed = machine.pack()

# Unpack - must inject dependencies
unpacked = Machine.unpack(
    packed,
    inject={'State': State, 'Event': Event}, # likely required
    transition_hooks={transition: [hook]}, # optional
    event_hooks={Event.START: [my_hook]}, # optional
    random=my_random_func  # optional
)
```

### Debug Visualization (Optional)

```python
fsm.touched() # Returns ASCII art showing FSM state and transitions
```

## Best Practices

1. **Use Enum states and events** for better error messages and type checking.
2. **Use `fsm.context` dict** for instance-specific data (e.g., NPC stats, game state) instead of global variables.
3. **Total probability for transitions** from a state should be <= 1.0; library normalizes if needed.
4. **Query before transition**: Use `can(event)` or `would(event)` to check if an event is valid.
5. **Test probabilistic logic** with custom random function for deterministic testing.
6. **Event hooks return bool**: Return `True` to proceed, `False` to cancel.
7. **Transition hooks don't return**: They only observe, cannot cancel; good for side effects.

## Common Gotchas

- **Don't use** `FSM` directly; always subclass with `rules` and `initial_state` set.
- **Rules must be a set**: `Transition` objects are hashable for set membership.
- **Event hooks fire first**: If any returns `False`, transition is canceled (transition hooks won't fire).
- **Context updates**: Modifying `context` in hooks affects subsequent event processing.
- **Serialization**: Enums and callables require `inject` dict on unpack. Hooks must be re-added.
- **Multiple transitions**: If multiple valid transitions exist with same event/state, one is chosen probabilistically.
