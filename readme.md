# Flying State Machines

Ever want to use a finite state machine (FSM) but didn't think it was okay to
not also pay homage to the great Flying Spaghetti Monster in the sky whose
Noodly abbreviation we use? This is the library for you, fellow Pastafarian.

## Installation

```bash
pip install flying-state-machines
```

## Code Structure

The code is organized into two classes: `FSM` and `Transition`.

- `FSM`
  - `add_event_hook(self, event: Enum|str, hook: Callable[[Enum|str, FSM], bool]) -> None:`
  - `remove_event_hook(self, event: Enum|str, hook: Callable[[Enum|str, FSM], bool]) -> None:`
  - `add_transition_hook(self, transition: Transition, hook: Callable[[Transition]]) -> None:`
  - `remove_transition_hook(self, transition: Transition, hook: Callable[[Transition]]) -> None:`
  - `would(self, event: Enum|str) -> tuple[Transition]:`
  - `input(self, event: Enum|str) -> Enum|str:`
  - `touched(self) -> str:`
- `Transition`
  - `add_hook(self, hook: Callable[[Transition]]) -> None:`
  - `remove_hook(self, hook: Callable[[Transition]]) -> None:`
  - `trigger(self) -> None:`
  - `@classmethod from_any(cls, from_states: type[Enum]|list[str], event: Enum|str, to_state: Enum|str, probability = 1.0) -> list[Transition]:`
  - `@classmethod to_any(cls, from_state: Enum|str, event: Enum|str, to_states: type[Enum]|list[str], total_probability = 1.0) -> list[Transition]:`

## Usage

To use this library to make a Flying State Machine™, import and extend as shown
below:

```python
from enum import Enum, auto()
from flying_state_machines import Transition, FSM

class State(Enum):
    NORMAL_CLOTHES: auto()
    PIRATE_CLOTHES: auto()

class Event(Enum):
    IS_FRIDAY: auto()
    IS_NOT_FRIDAY: auto()


class Pastafarian(FSM):
    def __init__(self):
        self.rules = set([
            Transition(State.NORMAL_CLOTHES, Event.IS_FRIDAY, State.PIRATE_CLOTHES),
            Transition(State.PIRATE_CLOTHES, Event.IS_NOT_FRIDAY, State.NORMAL_CLOTHES),
        ])
        self.initial_state = State.NORMAL_CLOTHES
        super().__init__()
```

This will represent the state of a Pastafarian. Events can be passed to the FSM,
either to cause a state transition or to see what state transitions are possible.

```python
me = Pastafarian()
would = me.would(Event.IS_FRIDAY) # tuple with the Transition of putting on pirate regalia
state = me.input(Event.IS_FRIDAY) # state is State.PIRATE_CLOTHES

state = me.input('ate a hotdog') # state is still State.PIRATE_CLOTHES
print(me.current) # State.PIRATE_CLOTHES
print(me.previous) # State.NORMAL_CLOTHES
```

It is also possible to use `str` and `list[str]` instead of `Enum`s for states
and events.

### Hooks

What good is a pirate without a hook? Hooks can be specified for events and for
transitions. The hooks for an event get called when the event is being processed
and before any transition occurs, and if an event hook returns `False`, the
state transition will be cancelled. For example:

```python
from flying_state_machines import Transition, FSM


class PastaMachine(FSM):
    def __init__(self):
        self.rules = set([
            Transition('in a box', 'pour into pot', 'is cooking'),
            Transition('is cooking', '7 minutes pass', 'al dente'),
            Transition('is cooking', '10 minutes pass', 'done'),
            Transition('is cooking', '15 minutes pass', 'mush'),
        ])
        super().__init__()

def status_hook(event, fsm):
    print(event, fsm.current, fsm.next)

machine = PastaMachine()
machine.add_event_hook('pour into pot', status_hook)
state = machine.input('pour into pot')
# console will show 'pour into pot', 'in a box', and 'is cooking'
# state and machine.current will be 'is cooking'
# machine.next will be None


def the_box_wasnt_open(event, fsm):
    print('you forgot to open the box')
    return False

machine = PastaMachine()
machine.add_event_hook('pour into pot', the_box_wasnt_open)
state = machine.input('pour into pot')
# console will show 'you forgot to open the box'
# state and machine.curent will be 'in a box'
# machine.next will be 'is cooking', indicating an aborted state transition
```

Transition hooks are set on the individual Transitions and are called whenever
the Transition is triggered (i.e. after the state has changed). `FSM` has an
`add_transition_hook` method for convenience; it is semantically identical to
calling the `add_hook` method on the `Transition`. Since the Transition has
already occurred by the time the hooks are called, they do not have any chance
to interact with the process.

```python
machine = PastaMachine()
transition = machine.would('pour into pot')[0]

def transition_hook(transition):
    print(f'{transition.from_state} => {transition.to_state}')

machine.add_transition_hook(transition, transition_hook)
# semantically identical to transition.add_hook(transition_hook)
```

One thing to note is that `FSM.add_transition_hook` will perform an additional
check to ensure that the `Transition` supplied is within the FSM rules.

### Serialization

`FSM`s have a unique serialization format that can be accessed by using the
`touched` method. `print(machine.touched())` will result in something like the
following:

```
        [None]                  [None]
           \                       /
                (((State.WAITING)))
{<State.SUPERPOSITION: 4>: {<Event.QUANTUM_FOAM: 4>: {<State.NEITHER: 3>: 0.5, <State.SUPERPOSITION: 4>: 0.5}}, <State.WAITING: 1>: {<Event.START: 1>: {<State.GOING: 2>: 1.0}, <Event.CONTINUE: 3>: {<State.WAITING: 1>: 1.0}, <Event.QUANTUM_FOAM: 4>: {<State.SUPERPOSITION: 4>: 0.5, <State.NEITHER: 3>: 0.5}}, <State.NEITHER: 3>: {<Event.QUANTUM_FOAM: 4>: {<State.SUPERPOSITION: 4>: 0.5, <State.NEITHER: 3>: 0.5}}, <State.GOING: 2>: {<Event.QUANTUM_FOAM: 4>: {<State.SUPERPOSITION: 4>: 0.5, <State.NEITHER: 3>: 0.5}, <Event.CONTINUE: 3>: {<State.GOING: 2>: 1.0}, <Event.STOP: 2>: {<State.WAITING: 1>: 1.0}}}
        s     s        s         s
       s        s     s            s
      s        s                  s
       s                            s

~Touched by His Noodly Appendage~
```

To the author's knowledge, this is the only FSM library that serializes FSMs as
FSMs.

## Testing

This is a simple library with just 15 tests. To run the tests, clone the
repo and then run the following:

```bash
python test/test_classes.py
```

One of the tests has visual output, which I suggest inspecting.
