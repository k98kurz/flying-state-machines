from context import classes
from enum import Enum, auto
import unittest


class State(Enum):
    WAITING = auto()
    GOING = auto()


class Event(Enum):
    START = auto()
    STOP = auto()
    CONTINUE = auto()


class Machine(classes.FSM):
    def __init__(self) -> None:
        self.rules = set([
            classes.Transition(State.WAITING, State.WAITING, Event.CONTINUE),
            classes.Transition(State.WAITING, State.GOING, Event.START),
            classes.Transition(State.GOING, State.GOING, Event.CONTINUE),
            classes.Transition(State.GOING, State.WAITING, Event.STOP),
        ])
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


if __name__ == "__main__":
    unittest.main()
