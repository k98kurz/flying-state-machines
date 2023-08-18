from context import classes
from enum import Enum, auto
from random import random
import unittest


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


class Machine(classes.FSM):
    rules = set([
        classes.Transition(State.WAITING, Event.CONTINUE, State.WAITING),
        classes.Transition(State.WAITING, Event.START, State.GOING),
        classes.Transition(State.GOING, Event.CONTINUE, State.GOING),
        classes.Transition(State.GOING, Event.STOP, State.WAITING),
        *classes.Transition.from_any(
            State, Event.QUANTUM_FOAM, State.SUPERPOSITION, 0.5
        ),
        *classes.Transition.from_any(
            State, Event.QUANTUM_FOAM, State.NEITHER, 0.5
        ),
        *classes.Transition.to_any(
            State.SUPERPOSITION, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
        *classes.Transition.to_any(
            State.NEITHER, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
    ])
    initial_state = State.WAITING


class StrMachine(classes.FSM):
    rules = set([
        classes.Transition('hungry', 'get food', 'eating'),
        classes.Transition('eating', 'food gone', 'sad'),
        classes.Transition('sad', 'time passes', 'hungry'),
    ])
    initial_state = 'hungry'


class TestTransition(unittest.TestCase):
    def test_Transition_initializes_properly(self):
        classes.Transition(State.WAITING, Event.START, State.GOING)
        classes.Transition("WAITING", "START", "GOING")

        with self.assertRaises(AssertionError) as e:
            classes.Transition(b'waiting', State.GOING, Event.START)
        assert str(e.exception) == 'from_state must be Enum or str'

        with self.assertRaises(AssertionError) as e:
            classes.Transition(State.WAITING, Event.START, b'State.GOING')
        assert str(e.exception) == 'to_state must be Enum or str'

        with self.assertRaises(AssertionError) as e:
            classes.Transition(State.WAITING, b'Event.START', State.GOING)
        assert str(e.exception) == 'on_event must be Enum or str'

    def test_Transition_is_hashable(self):
        tn1 = classes.Transition(State.WAITING, State.GOING, Event.START)
        tn2 = classes.Transition(State.GOING, State.WAITING, Event.STOP)
        assert hash(tn1) != hash(tn2)

    def test_Transition_hooks_e2e(self):
        transition = classes.Transition(State.WAITING, State.GOING, Event.START)
        log = {'count': 0}

        with self.assertRaises(AssertionError) as e:
            transition.add_hook(1)
        assert str(e.exception) == 'hook must be Callable[[Transition]]'

        with self.assertRaises(AssertionError) as e:
            transition.remove_hook(1)
        assert str(e.exception) == 'hook must be Callable[[Transition]]'

        def hook(tn):
            log['count'] += 1
        transition.add_hook(hook)
        transition.trigger()
        assert log['count'] == 1
        transition.trigger()
        assert log['count'] == 2
        transition.remove_hook(hook)
        transition.trigger()
        assert log['count'] == 2

    def test_Transition_from_any_returns_list_of_Transition(self):
        tns = classes.Transition.from_any(
            State, Event.QUANTUM_FOAM, State.SUPERPOSITION
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.to_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM

        tns = classes.Transition.from_any(
            ['WAITING', 'GOING'], 'QUANTUM_FOAM', 'SUPERPOSITION'
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.to_state == 'SUPERPOSITION'
            assert tn.on_event == 'QUANTUM_FOAM'

    def test_Transition_to_any_returns_list_of_Transition(self):
        tns = classes.Transition.to_any(
            State.SUPERPOSITION, Event.QUANTUM_FOAM, State
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.from_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM

        tns = classes.Transition.to_any(
            "SUPERPOSITION", "QUANTUM_FOAM", ["GOING", "GONE"]
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.from_state == 'SUPERPOSITION'
            assert tn.on_event == 'QUANTUM_FOAM'


class TestFSM(unittest.TestCase):
    def test_direct_FSM_initialization_raises_error(self):
        with self.assertRaises(AssertionError) as e:
            classes.FSM()
        assert str(e.exception) == 'self.rules must be set[Transition]'

    def test_FSM_subclass_initializes_properly(self):
        machine = Machine()
        assert hasattr(machine, 'rules') and type(machine.rules) is set
        assert hasattr(machine, 'initial_state') and type(machine.initial_state) is State
        assert hasattr(machine, 'current') and type(machine.current) is State
        assert hasattr(machine, 'previous') and machine.previous is None
        assert hasattr(machine, 'next') and machine.next is None

    def test_FSM_subclass_would_returns_tuple_of_Transition(self):
        machine = Machine()
        tns = machine.would(Event.CONTINUE)
        assert type(tns) is tuple
        for tn in tns:
            assert isinstance(tn, classes.Transition)

        assert len(machine.would('random event')) == 0

    def test_FSM_subclass_input_returns_state_after_Transition(self):
        machine = Machine()
        assert machine.current is State.WAITING
        res = machine.input(Event.START)
        assert machine.current is State.GOING
        assert res is machine.current

    def test_FSM_subclass_event_hooks_fire_on_event(self):
        machine = Machine()
        log = {}
        def hook(event, _):
            if event not in log:
                log[event] = 0
            log[event] += 1

        with self.assertRaises(AssertionError) as e:
            machine.add_event_hook(Event.START, 1)
        assert str(e.exception) == 'hook must be Callable[[Enum|str, FSM], bool]'

        machine.add_event_hook(Event.START, hook)
        machine.add_event_hook('fake event', hook)

        assert 'fake event' not in log
        machine.input('fake event')
        assert 'fake event' in log and log['fake event'] == 1

        assert Event.START not in log
        machine.input(Event.START)
        assert Event.START in log and log[Event.START] == 1
        machine.input(Event.START)
        assert log[Event.START] == 2
        machine.remove_event_hook(Event.START, hook)
        machine.input(Event.START)
        assert log[Event.START] == 2

    def test_FSM_subclass_event_hooks_can_cancel_Transition(self):
        machine = Machine()
        log = {}
        def hook(event, _):
            if event not in log:
                log[event] = 0
            log[event] += 1
            return False

        assert machine.current is State.WAITING
        machine.add_event_hook(Event.START, hook)
        machine.input(Event.START)
        assert machine.current is State.WAITING
        assert Event.START in log and log[Event.START] == 1

    def test_FSM_subclass_transition_hooks_e2e(self):
        machine = Machine()
        log = {}
        def hook(transition):
            if transition not in log:
                log[transition] = 0
            log[transition] += 1

        tn = machine.would(Event.START)[0]
        machine.add_transition_hook(tn, hook)
        assert tn not in log
        machine.input(Event.START)
        assert tn in log and log[tn] == 1

        machine.remove_transition_hook(tn, hook)
        machine.input(Event.STOP)
        assert machine.would(Event.START)[0] is tn
        machine.input(Event.START)
        assert log[tn] == 1

    def test_FSM_subclass_random_transitions(self):
        machine = Machine()
        superposition, neither = 0, 0

        for _ in range(10):
            machine.input(Event.QUANTUM_FOAM)
            if machine.current is State.SUPERPOSITION:
                superposition += 1
            if machine.current is State.NEITHER:
                neither += 1

        assert superposition + neither == 10
        assert superposition > 0
        assert neither > 0

        waiting, going = 0, 0
        for i in range(10):
            machine.current = State.SUPERPOSITION if i%2 else State.NEITHER
            machine.input(Event.NORMALIZE)
            if machine.current is State.WAITING:
                waiting += 1
            if machine.current is State.GOING:
                going += 1

        assert waiting + going == 10
        assert waiting > 0
        assert going > 0

    def test_FSM_subclass_touched_is_Flying_Spaghetti_monster_str(self):
        machine = Machine()
        if random() < 0.2:
            machine.input(Event.START)
        elif random() < 0.5:
            machine.input(Event.QUANTUM_FOAM)
        print('\n' + machine.touched())
        assert len(machine.touched()) > 10 * len(machine.rules)
        assert machine.touched()[-33:] == '~Touched by His Noodly Appendage~'

    def test_FSM_subclass_with_str_states_and_events_e2e(self):
        machine = StrMachine()
        log = {}
        def hook(whatever, *args):
            if whatever not in log:
                log[whatever] = 0
            log[whatever] += 1

        assert machine.current == 'hungry'
        tn = machine.would('get food')[0]
        machine.add_event_hook('get food', hook)
        machine.add_transition_hook(tn, hook)
        assert tn not in log and 'get food' not in log
        state = machine.input('get food')
        assert tn in log and 'get food' in log
        assert machine.current == state == 'eating'
        assert machine.previous == 'hungry'
        machine.input('get food')
        assert machine.current == 'eating'
        machine.input('time passes')
        assert machine.current == 'eating'
        machine.input('food gone')
        assert machine.current == 'sad'
        assert machine.previous == 'eating'
        machine.input('time passes')
        assert machine.current == 'hungry'
        assert machine.previous == 'sad'


if __name__ == "__main__":
    unittest.main()
