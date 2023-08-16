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


class TestFSM(unittest.TestCase):
    ...


if __name__ == "__main__":
    unittest.main()
