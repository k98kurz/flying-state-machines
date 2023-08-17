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

To see the full documentation, read the
[dox.md](https://github.com/k98kurz/flying-state-machines/blob/master/dox.md)
generated by [autodox](https://pypi.org/project/autodox).

## Usage

To use this library to make a Flying State Machine™, import and extend as shown
below:

```python
from enum import Enum, auto
from flying_state_machines import Transition, FSM

class State(Enum):
    NORMAL_CLOTHES = auto()
    PIRATE_CLOTHES = auto()

class Event(Enum):
    IS_FRIDAY = auto()
    IS_NOT_FRIDAY = auto()


class Pastafarian(FSM):
    rules = set([
        Transition(State.NORMAL_CLOTHES, Event.IS_FRIDAY, State.PIRATE_CLOTHES),
        Transition(State.PIRATE_CLOTHES, Event.IS_NOT_FRIDAY, State.NORMAL_CLOTHES),
    ])
    initial_state = State.NORMAL_CLOTHES
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

### Randomized transitions

It is possible to encode randomized transitions by supplying multiple
`Transition`s with identical `from_state` and `on_event`. The cummulative
probability of all such `Transition`s must be <= 1.0.

```python
from flying_state_machines import FSM, Transition

class RussianRoulette(FSM):
    initial_state = 'safe'
    rules = set([
        Transition('safe', 'spin', 'safe', 5.0/6.0),
        Transition('safe', 'spin', 'dead', 1.0/6.0),
    ])

gun = RussianRoulette()
state = gun.input('spin') # 1/6 chance of getting shot
```

### `Transition.to_any` and `Transition.from_any`

There are helper class methods available for generating lists of `Transition`s
in case they are useful. The `.to_any` method will return a list of `Transition`s
that represents a random transition from a specific state to any valid state on
the given event. The `.from_any` method will return a list of `Transition`s that
represents a random transition from any valid state to a specific state on a
given event. They can be used as follows:

```python
from enum import Enum, auto
from flying_state_machines import FSM, Transition


class State(Enum):
    WAITING = auto()
    GOING = auto()
    NEITHER = auto()
    SUPERPOSITION = auto()

class Event(Enum):
    START = auto()
    STOP = auto()
    CONTINUE = auto()
    QUANTUM_FOAM = auto()
    NORMALIZE = auto()

class Machine(FSM):
    rules = set([
        Transition(State.WAITING, Event.CONTINUE, State.WAITING),
        Transition(State.WAITING, Event.START, State.GOING),
        Transition(State.GOING, Event.CONTINUE, State.GOING),
        Transition(State.GOING, Event.STOP, State.WAITING),
        *Transition.from_any(
            State, Event.QUANTUM_FOAM, State.SUPERPOSITION, 0.5
        ),
        *Transition.from_any(
            State, Event.QUANTUM_FOAM, State.NEITHER, 0.5
        ),
        *Transition.to_any(
            State.NEITHER, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
        *Transition.to_any(
            State.SUPERPOSITION, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
    ])
    initial_state = State.WAITING
```

The above will create a FSM that will transition to either `SUPERPOSITION` or
`NEITHER` at random upon the `QUANTUM_FOAM` event, and it will transition to
either `WAITING` or `GOING` at random upon the `NORMALIZE` event.

### Hooks

What good is a pirate without a hook? Hooks can be specified for events and for
transitions. The hooks for an event get called when the event is being processed
and before any transition occurs, and if an event hook returns `False`, the
state transition will be cancelled. For example:

```python
from flying_state_machines import Transition, FSM


class PastaMachine(FSM):
    rules = set([
        Transition('in a box', 'pour into pot', 'is cooking'),
        Transition('is cooking', '7 minutes pass', 'al dente'),
        Transition('is cooking', '10 minutes pass', 'done'),
        Transition('is cooking', '15 minutes pass', 'mush'),
    ])
    initial_state = 'in a box'

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

# License

ISC License

Copyleft (c) 2023 k98kurz

Permission to use, copy, modify, and/or distribute this software
for any purpose with or without fee is hereby granted, provided
that the above copyleft notice and this permission notice appear in
all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
