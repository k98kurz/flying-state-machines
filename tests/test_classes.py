from context import classes
from enum import Enum, auto
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


class Machine(classes.FSM):
    def __init__(self) -> None:
        rules = [
            classes.Transition(State.WAITING, State.WAITING, Event.CONTINUE),
            classes.Transition(State.WAITING, State.GOING, Event.START),
            classes.Transition(State.GOING, State.GOING, Event.CONTINUE),
            classes.Transition(State.GOING, State.WAITING, Event.STOP),
        ]
        rules.extend(classes.Transition.from_any(
            State, State.SUPERPOSITION, Event.QUANTUM_FOAM, 0.5
        ))
        rules.extend(classes.Transition.from_any(
            State, State.NEITHER, Event.QUANTUM_FOAM, 0.5
        ))
        self.rules = set(rules)
        self.initial_state = State.WAITING
        super().__init__()


class TestTransition(unittest.TestCase):
    def test_Transition_initializes_properly(self):
        classes.Transition(State.WAITING, State.GOING, Event.START)

        with self.assertRaises(AssertionError) as e:
            classes.Transition(b'waiting', State.GOING, Event.START)
        assert str(e.exception) == 'from_state must be Enum or str'

        with self.assertRaises(AssertionError) as e:
            classes.Transition(State.WAITING, b'State.GOING', Event.START)
        assert str(e.exception) == 'to_state must be Enum or str'

        with self.assertRaises(AssertionError) as e:
            classes.Transition(State.WAITING, State.GOING, b'Event.START')
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
            State, State.SUPERPOSITION, Event.QUANTUM_FOAM
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.to_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM

    def test_Transition_to_any_returns_list_of_Transition(self):
        tns = classes.Transition.to_any(
            State.SUPERPOSITION, State, Event.QUANTUM_FOAM
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, classes.Transition)
            assert tn.from_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM


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

    def test_FSM_subclass_input_returns_state_after_Transition(self):
        machine = Machine()
        assert machine.current is State.WAITING
        res = machine.input(Event.START)
        assert machine.current is State.GOING
        assert isinstance(res, State)

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

        assert superposition > 0
        assert neither > 0
        assert superposition + neither == 10

    def test_FSM_subclass_str_is_Flying_Spaghetti_monster(self):
        machine = Machine()
        print('\n' + machine.touched())
        assert len(machine.touched()) > 10 * len(machine.rules)
        assert machine.touched()[-33:] == '~Touched by His Noodly Appendage~'


if __name__ == "__main__":
    unittest.main()
