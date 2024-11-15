from __future__ import annotations
from enum import Enum
from packify import pack, unpack
from random import random
from typing import Any, Callable


class Transition:
    from_state: Enum|str
    to_state: Enum|str
    on_event: Enum|str
    probability: float
    hooks: list[Callable[[Transition]]]

    def __init__(self, from_state: Enum|str, on_event: Enum|str, to_state: Enum|str,
                 probability: float = 1.0, hooks: list[Callable[[Transition]]] = []) -> None:
        assert isinstance(from_state, Enum) or type(from_state) is str, \
            'from_state must be Enum or str'
        assert isinstance(to_state, Enum) or type(to_state) is str, \
            'to_state must be Enum or str'
        assert isinstance(on_event, Enum) or type(on_event) is str, \
            'on_event must be Enum or str'
        assert type(probability) is float, 'probability must be float'
        for hook in hooks:
            assert callable(hook), 'each hook must be callable'
        self.from_state = from_state
        self.to_state = to_state
        self.on_event = on_event
        self.probability = probability
        self.hooks = hooks

    def __hash__(self) -> int:
        """Makes the Transition hashable."""
        return hash((self.from_state, self.to_state, self.on_event))

    def __repr__(self) -> str:
        return repr((self.from_state, self.on_event, self.to_state, self.probability))

    def __bytes__(self) -> bytes:
        """Serialize to bytes."""
        return self.pack()

    def pack(self) -> bytes:
        """Serialize to bytes using packify."""
        if isinstance(self.from_state, Enum):
            from_state = [type(self.from_state).__name__, self.from_state.value]
        else:
            from_state = self.from_state
        if isinstance(self.to_state, Enum):
            to_state = [type(self.to_state).__name__, self.to_state.value]
        else:
            to_state = self.to_state
        if isinstance(self.on_event, Enum):
            on_event = [type(self.on_event).__name__, self.on_event.value]
        else:
            on_event = self.on_event
        return pack({
            'from_state': from_state,
            'to_state': to_state,
            'on_event': on_event,
            'probability': self.probability,
        })

    @classmethod
    def unpack(cls, data: bytes, /, *, inject: dict = {},
               hooks: list[Callable[[Transition]]] = []) -> Transition:
        """Deserialize from bytes using packify. Inject dependencies
            as necessary, e.g. the Enum classes representing states or
            events.
        """
        dependencies = {**globals(), **inject}
        data = unpack(data, inject=dependencies)
        from_state = data['from_state']
        to_state = data['to_state']
        on_event = data['on_event']

        if type(from_state) is list:
            classname = from_state[0]
            enumclass = dependencies[classname]
            from_state = enumclass(from_state[1])
        if type(to_state) is list:
            classname = to_state[0]
            enumclass = dependencies[classname]
            to_state = enumclass(to_state[1])
        if type(on_event) is list:
            classname = on_event[0]
            enumclass = dependencies[classname]
            on_event = enumclass(on_event[1])

        return cls(
            from_state=from_state,
            to_state=to_state,
            on_event=on_event,
            probability=data['probability'],
            hooks=hooks,
        )

    def add_hook(self, hook: Callable[[Transition, Any]]) -> None:
        """Adds a hook for when the Transition occurs."""
        assert callable(hook), 'hook must be Callable[[Transition, Any]]'
        self.hooks.append(hook)

    def remove_hook(self, hook: Callable[[Transition, Any]]) -> None:
        """Removes a hook if it had been previously added."""
        assert callable(hook), 'hook must be Callable[[Transition, Any]]'
        if hook in self.hooks:
            self.hooks.remove(hook)

    def trigger(self, data: Any = None) -> None:
        """Triggers all hooks."""
        for hook in self.hooks:
            hook(self, data)

    @classmethod
    def from_any(cls, from_states: type[Enum]|list[str], event: Enum|str,
                 to_state: Enum|str, probability: float = 1.0) -> list[Transition]:
        """Makes a list of Transitions from any valid state to a
            specific state, each with the given probability.
        """
        return [
            cls(state, event, to_state, probability)
            for state in from_states
        ]

    @classmethod
    def to_any(cls, from_state: Enum|str, event: Enum|str,
               to_states: type[Enum]|list[str],
               total_probability: float = 1.0) -> list[Transition]:
        """Makes a list of Transitions from a specific state to any
            valid state, with the given cumulative probability.
        """
        probability = total_probability / len(to_states)
        return [
            cls(from_state, event, state, probability)
            for state in to_states
        ]


class FSM:
    rules: set[Transition]
    initial_state: Enum|str
    current: Enum|str
    previous: Enum|str|None
    next: Enum|str|None
    _valid_transitions: dict[Enum|str, dict[Enum|str, list[Transition]]]
    _event_hooks: dict[Enum|str, list[Callable]]

    def __init__(self) -> None:
        assert hasattr(self, 'rules'), 'self.rules must be set[Transition]'
        assert isinstance(self.rules, set), 'self.rules must be set[Transition]'
        self._valid_transitions = {}
        self._event_hooks =  {}
        for rule in self.rules:
            assert isinstance(rule, Transition), 'self.rules must be set[Transition]'
            if rule.from_state not in self._valid_transitions:
                self._valid_transitions[rule.from_state] = {}
            if rule.on_event not in self._valid_transitions[rule.from_state]:
                self._valid_transitions[rule.from_state][rule.on_event] = []
            self._valid_transitions[rule.from_state][rule.on_event].append(rule)
        for from_state in self._valid_transitions:
            for on_event in self._valid_transitions[from_state]:
                transitions = self._valid_transitions[from_state][on_event]
                total_probability = sum([r.probability for r in transitions])
                assert total_probability <= 1.0, \
                    'total probability for state transitions must be <= 1.0'
        assert isinstance(self.initial_state, Enum) or type(self.initial_state) is str, \
            'self.initial_state must be Enum or str'
        self.current = self.initial_state
        self.previous = None
        self.next = None
        self._event_hooks = {}

    def add_event_hook(self, event: Enum|str,
                       hook: Callable[[Enum|str, FSM, Any], bool]) -> None:
        """Adds a callback that fires before an event is processed. If
            any callback returns False, the event is cancelled.
        """
        assert callable(hook), 'hook must be Callable[[Enum|str, FSM, Any], bool]'
        if event not in self._event_hooks:
            self._event_hooks[event] = []
        self._event_hooks[event].append(hook)

    def remove_event_hook(self, event: Enum|str,
                          hook: Callable[[Enum|str, FSM, Any], bool]) -> None:
        """Removes a callback that fires before an event is processed."""
        assert callable(hook), 'hook must be Callable[[Enum|str, FSM, Any], bool]'
        if event not in self._event_hooks:
            return
        if hook in self._event_hooks[event]:
            self._event_hooks[event].remove(hook)

    def add_transition_hook(self, transition: Transition,
                            hook: Callable[[Transition]]) -> None:
        """Adds a callback that fires after a Transition occurs."""
        assert isinstance(transition, Transition), 'transition must be a Transition'
        assert callable(hook), 'hook must be Callable[[Transition, Any]]'
        assert transition in self.rules, 'transition must be in self.rules'
        transition.add_hook(hook)

    def remove_transition_hook(self, transition: Transition,
                            hook: Callable[[Transition]]) -> None:
        """Removes a callback that fires after a Transition occurs."""
        assert isinstance(transition, Transition), 'transition must be a Transition'
        assert callable(hook), 'hook must be Callable[[Transition, Any]]'
        assert transition in self.rules, 'transition must be in self.rules'
        transition.remove_hook(hook)

    def would(self, event: Enum|str) -> tuple[Transition]:
        """Given the current state of the machine and an event, return a
            tuple of possible Transitions.
        """
        if self.current not in self._valid_transitions or \
            event not in self._valid_transitions[self.current]:
            return tuple()
        return tuple(self._valid_transitions[self.current][event])

    def can(self, event: Enum|str) -> bool:
        """Given the current state of the machine and an event, return
            whether the event can be processed.
        """
        return len(self.would(event)) > 0

    def input(self, event: Enum|str, data: Any = None) -> Enum|str:
        """Attempt to process an event, returning the resultant state."""
        possible_transitions = self.would(event)
        transition = None
        if len(possible_transitions) == 1:
            transition = possible_transitions[0]
            self.next = transition.to_state
        if len(possible_transitions) > 1:
            probabilities: list[tuple[float, Transition]] = []
            cumulative = 0.0
            for tn in possible_transitions:
                cumulative += tn.probability
                probabilities.append((cumulative, tn))
            choice = random()
            for probability, tn in probabilities:
                if choice < probability:
                    transition = tn
                    break
            self.next = transition.to_state

        if event in self._event_hooks:
            canceled = False
            for hook in self._event_hooks[event]:
                if hook(event, self, data) is False:
                    canceled = True
            if canceled:
                return self.current

        if transition:
            self.previous = self.current
            self.current = self.next
            self.next = None
            transition.trigger(data)

        return self.current

    def touched(self) -> str:
        """Represent the state machine as a Flying Spaghetti Monster."""
        left_eye = f"    [{self.previous}]"
        space = "        "
        right_eye = f"[{self.next}]"
        left_stem = int((len(left_eye) - 4)/2) + 4
        left_stem = "".join([" " for _ in range(left_stem)]) + '\\'
        right_stem = int((len(right_eye) + len(left_eye) + len(space))/2)
        right_stem = "".join([" " for _ in range(right_stem)]) + "/"
        middle_space = "".join([" " for _ in range(len(left_stem) - 2)])
        return f"""\
{left_eye}{space}{right_eye}
{left_stem}{right_stem}
{middle_space}((({self.current})))
{self._valid_transitions}
        s     s        s         s
       s        s     s            s
      s        s                  s
       s                            s

~Touched by His Noodly Appendage~"""

    def pack(self) -> bytes:
        """Serialize to bytes using packify."""
        if isinstance(self.initial_state, Enum):
            initial_state = [type(self.initial_state).__name__, self.initial_state.value]
        else:
            initial_state = self.initial_state
        if isinstance(self.current, Enum):
            current = [type(self.current).__name__, self.current.value]
        else:
            current = self.current
        if isinstance(self.previous, Enum):
            previous = [type(self.previous).__name__, self.previous.value]
        else:
            previous = self.previous
        if isinstance(self.next, Enum):
            next = [type(self.next).__name__, self.next.value]
        else:
            next = self.next
        return pack({
            'rules': {r.pack() for r in self.rules},
            'initial_state': initial_state,
            'current': current,
            'previous': previous,
            'next': next,
        })

    @classmethod
    def unpack(cls, data: bytes, /, *, inject: dict = {},
               transition_hooks: dict[Transition, list[Callable[[Transition]]]] = {},
               event_hooks: dict[Enum|str, list[Callable[[Enum|str, FSM, Any], bool]]] = {}
               ) -> FSM:
        """Deserialize from bytes using packify. Inject dependencies
            as necessary, e.g. the Enum classes representing states or
            events.
        """
        dependencies = {**globals(), **inject}
        data = unpack(data, inject=dependencies)
        fsm = cls()
        for transition, hooks in transition_hooks.items():
            assert type(hooks) is list, 'transition_hooks must be list[Callable]'
            for hook in hooks:
                fsm.add_transition_hook(transition, hook)
        initial_state = data['initial_state']
        current = data['current']
        previous = data['previous']
        next = data['next']

        if type(initial_state) is list:
            classname = initial_state[0]
            enumclass = dependencies[classname]
            initial_state = enumclass(initial_state[1])
        if type(current) is list:
            classname = current[0]
            enumclass = dependencies[classname]
            current = enumclass(current[1])
        if type(previous) is list:
            classname = previous[0]
            enumclass = dependencies[classname]
            previous = enumclass(previous[1])
        if type(next) is list:
            classname = next[0]
            enumclass = dependencies[classname]
            next = enumclass(next[1])

        fsm.initial_state = initial_state
        fsm.current = current
        fsm.previous = previous
        fsm.next = next
        for event, hooks in event_hooks.items():
            assert type(hooks) is list, 'event_hooks must be list[Callable]'
            for hook in hooks:
                fsm.add_event_hook(event, hook)
        return fsm
