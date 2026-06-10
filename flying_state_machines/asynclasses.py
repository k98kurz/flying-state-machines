from __future__ import annotations
from .errors import type_assert, value_assert
from asyncio import iscoroutine
from enum import Enum
from random import random
from typing import Any, Awaitable, Callable
from packify import pack, unpack



class AsyncTransition:
    """Represents a rule for transitioning between states within an
        async Finite State Machine. Specifies the states from and to
        which the transition occurs, the event that triggers the
        transition, and optionally the probability of the transition
        (for PFSMs/Markov chains). Probabilities can be static floats or
        determined dynamically by a callback that accepts a context
        dict.
    """
    from_state: Enum|str
    to_state: Enum|str
    on_event: Enum|str
    probability: float|Callable[[dict], float]
    hooks: list[Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]]

    def __init__(
            self, from_state: Enum|str, on_event: Enum|str, to_state: Enum|str,
            probability: float | Callable[[dict], float] = 1.0,
            hooks: list[
                Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]
            ] = None
        ) -> None:
        """Initialization of an AsyncTransition instance performs an
            array of sanity checks to ensure the library is being used
            properly. Raises `TypeError` if any necessary
            precondition check fails, i.e. invalid `from_state`,
            `to_state`, `event`, `probability`, or `hooks`.
        """
        type_assert(isinstance(from_state, Enum) or type(from_state) is str,
            'from_state must be Enum or str')
        type_assert(isinstance(to_state, Enum) or type(to_state) is str,
            'to_state must be Enum or str')
        type_assert(isinstance(on_event, Enum) or type(on_event) is str,
            'on_event must be Enum or str')
        type_assert(type(probability) is float or callable(probability),
            'probability must be float | Callable[[dict], float]')
        hooks = hooks or []
        for hook in hooks:
            type_assert(callable(hook), 'each hook must be callable')
        self.from_state = from_state
        self.to_state = to_state
        self.on_event = on_event
        self.probability = probability
        self.hooks = hooks

    def __hash__(self) -> int:
        """Makes the AsyncTransition hashable."""
        return hash((self.from_state, self.to_state, self.on_event))

    def __repr__(self) -> str:
        """Produce a string representation."""
        return repr((
            self.from_state, self.on_event, self.to_state, self.probability
        ))

    def __bytes__(self) -> bytes:
        """Serialize to bytes."""
        return self.pack()

    def pack(self) -> bytes:
        """Serialize to bytes using packify."""
        from_state = self.from_state
        to_state = self.to_state
        on_event = self.on_event
        probability = self.probability
        if isinstance(from_state, Enum):
            from_state = [type(from_state).__name__, from_state.value]
        if isinstance(to_state, Enum):
            to_state = [type(to_state).__name__, to_state.value]
        if isinstance(on_event, Enum):
            on_event = [type(on_event).__name__, on_event.value]
        if callable(probability):
            probability = probability.__name__
        return pack({
            'from_state': from_state,
            'to_state': to_state,
            'on_event': on_event,
            'probability': probability,
        })

    @classmethod
    def unpack(
            cls, data: bytes, inject: dict = {},
            hooks: list[
                Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]
            ] = []
        ) -> AsyncTransition:
        """Deserialize from bytes using packify. Inject dependencies
            as necessary, e.g. the Enum classes representing states or
            events.
        """
        dependencies = {**globals(), **inject}
        data = unpack(data, inject=dependencies)
        from_state = data['from_state']
        to_state = data['to_state']
        on_event = data['on_event']
        probability = data['probability']

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
        if type(probability) is str:
            probability = dependencies.get(probability)
            type_assert(callable(probability),
                'probability callable must be available in inject')

        return cls(
            from_state=from_state,
            to_state=to_state,
            on_event=on_event,
            probability=probability,
            hooks=hooks,
        )

    def add_hook(
            self,
            hook: Callable[
                [AsyncTransition, dict, Any], None | Awaitable[None]
            ]
        ) -> None:
        """Adds a hook for when the AsyncTransition occurs. Any context
            and data passed to `trigger` will be passed to the hook.
        """
        type_assert(callable(hook),
            'hook must be Callable[[AsyncTransition, dict, Any], None | '
            'Awaitable[None]]'
        )
        self.hooks.append(hook)

    def remove_hook(
            self,
            hook: Callable[
                [AsyncTransition, dict, Any], None | Awaitable[None]
            ]
        ) -> None:
        """Removes a hook if it had been previously added."""
        type_assert(callable(hook),
            'hook must be Callable[[AsyncTransition, dict, Any], None | '
            'Awaitable[None]]'
        )
        if hook in self.hooks:
            self.hooks.remove(hook)

    async def trigger(self, context: dict = None, data: Any = None) -> None:
        """Triggers all hooks with the given context and data."""
        for hook in self.hooks:
            val = hook(self, context, data)
            if iscoroutine(val):
                await val

    @classmethod
    def from_any(
            cls, from_states: type[Enum]|list[str], event: Enum|str,
            to_state: Enum|str, probability: float | Callable[[dict], float] = 1.0
        ) -> list[AsyncTransition]:
        """Makes a list of Transitions from any valid state to a
            specific state, each with the given probability.
        """
        return [
            cls(state, event, to_state, probability)
            for state in from_states
        ]

    @classmethod
    def to_any(
            cls, from_state: Enum|str, event: Enum|str,
            to_states: type[Enum]|list[str],
            total_probability: float | Callable[[dict], float] = 1.0
        ) -> list[AsyncTransition]:
        """Makes a list of Transitions from a specific state to any
            valid state, with the given cumulative probability if
            `total_probability` is a float or with `total_probability`
            assigned to each AsyncTransition if it is callable.
        """
        if callable(total_probability):
            probability = total_probability
        else:
            probability = total_probability / len(to_states)
        return [
            cls(from_state, event, state, probability)
            for state in to_states
        ]


class AsyncFSM:
    """Finite State Machine base. Should be used by subclassing with
        `rules` and `initial_state` set as class attributes.
    """
    rules: set[AsyncTransition]
    initial_state: Enum|str
    current: Enum|str
    previous: Enum|str|None
    next: Enum|str|None
    context: dict
    random: Callable[[], float]
    _valid_transitions: dict[Enum|str, dict[Enum|str, list[AsyncTransition]]]
    _event_hooks: dict[Enum|str, list[Callable]]

    def __init__(
            self, context: dict = None, random: Callable[[], float] = random
        ) -> None:
        """Initialization of an FSM subclass instance performs an array
            of sanity checks to ensure the library is being used
            properly. Raises `TypeError` or `ValueError` if any
            necessary precondition checks fail, e.g. invalid `rules` or
            `initial_state`. Also processes `rules` to seed internal
            structures to enable Markov chain behaviors. Accepts an
            optional `context` dict that is passed to transition hooks
            and any callable `transition.probability`. Accepts an
            optional `random` callable that will be used for deciding
            probabilistic transitions (defaults to `random.random`).
        """
        value_assert(hasattr(self, 'rules'),
            'self.rules must be set[AsyncTransition]'
        )
        type_assert(isinstance(self.rules, set),
            'self.rules must be set[AsyncTransition]'
        )
        self._valid_transitions = {}
        for rule in self.rules:
            type_assert(isinstance(rule, AsyncTransition),
                'self.rules must be set[AsyncTransition]')
            if rule.from_state not in self._valid_transitions:
                self._valid_transitions[rule.from_state] = {}
            if rule.on_event not in self._valid_transitions[rule.from_state]:
                self._valid_transitions[rule.from_state][rule.on_event] = []
            self._valid_transitions[rule.from_state][rule.on_event].append(rule)
        for from_state in self._valid_transitions:
            for on_event in self._valid_transitions[from_state]:
                transitions = self._valid_transitions[from_state][on_event]
                total_probability = sum([
                    0 if callable(r.probability) else r.probability
                    for r in transitions
                ])
                value_assert(total_probability <= 1.0,
                    'total probability for state transitions must be <= 1.0')
        type_assert(
            isinstance(self.initial_state, Enum)
            or type(self.initial_state) is str,
            'self.initial_state must be Enum or str'
        )
        type_assert(isinstance(context, dict) or context is None,
            'context must be dict')
        type_assert(callable(random),
            'random must be a callable that returns a float'
        )
        self.current = self.initial_state
        self.previous = None
        self.next = None
        self._event_hooks = {}
        self.context = context or {}
        self.random = random

    def add_event_hook(
            self, event: Enum|str,
            hook: Callable[[Enum|str, AsyncFSM, Any], bool | Awaitable[bool]]
        ) -> None:
        """Adds a callback that fires before an event is processed. If
            any callback returns False, the event is cancelled.
        """
        type_assert(callable(hook),
            'hook must be Callable[[Enum|str, AsyncFSM, Any], bool | '
            'Awaitable[bool]]'
        )
        if event not in self._event_hooks:
            self._event_hooks[event] = []
        self._event_hooks[event].append(hook)

    def remove_event_hook(
            self,
            event: Enum|str,
            hook: Callable[
                [Enum|str, AsyncFSM, Any], bool | Awaitable[bool]
            ]
        ) -> None:
        """Removes a callback that fires before an event is processed."""
        type_assert(callable(hook),
            'hook must be Callable[[Enum|str, AsyncFSM, Any], bool | '
            'Awaitable[bool]]'
        )
        if event not in self._event_hooks:
            return
        if hook in self._event_hooks[event]:
            self._event_hooks[event].remove(hook)

    def add_transition_hook(
            self,
            transition: AsyncTransition,
            hook: Callable[
                [AsyncTransition, dict, Any], None | Awaitable[None]
            ]
        ) -> None:
        """Adds a callback that fires after an AsyncTransition occurs.
            `self.context` and any data passed to `input` will be passed
            to `transition.trigger`, which will be passed to the hook.
        """
        type_assert(isinstance(transition, AsyncTransition),
            'transition must be an AsyncTransition')
        type_assert(callable(hook),
            'hook must be Callable[[AsyncTransition, dict, Any], None | '
            'Awaitable[None]]'
        )
        value_assert(transition in self.rules, 'transition must be in self.rules')
        transition.add_hook(hook)

    def remove_transition_hook(
            self, transition: AsyncTransition,
            hook: Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]
        ) -> None:
        """Removes a callback that fires after an AsyncTransition occurs."""
        type_assert(isinstance(transition, AsyncTransition),
            'transition must be an AsyncTransition')
        type_assert(callable(hook),
            'hook must be Callable[[AsyncTransition, dict, Any], None | '
            'Awaitable[None]]'
        )
        value_assert(transition in self.rules, 'transition must be in self.rules')
        transition.remove_hook(hook)

    def would(self, event: Enum|str) -> tuple[AsyncTransition]:
        """Given the current state of the machine and an event, return a
            tuple of possible Transitions.
        """
        if  (   self.current not in self._valid_transitions
                or event not in self._valid_transitions[self.current]
            ):
            return tuple()
        return tuple(self._valid_transitions[self.current][event])

    def can(self, event: Enum|str) -> bool:
        """Given the current state of the machine and an event, return
            whether the event can be processed.
        """
        return len(self.would(event)) > 0

    async def input(self, event: Enum|str, data: Any = None) -> Enum|str:
        """Attempt to process an event, returning the resultant state.
            If multiple valid transitions exist, select one according to
            the probabilities, passing `self.context` when calling any
            callable transition probability. Call all relevant hooks,
            passing `self`, `event`, and `data` to event hooks and
            `self.context` and `data` to transition hooks. If an event
            hook returns `False`, the transition is canceled.
        """
        possible_transitions = self.would(event)
        transition = None

        if len(possible_transitions) == 1:
            transition = possible_transitions[0]
            self.next = transition.to_state

        if len(possible_transitions) > 1:
            probabilities: list[tuple[float, AsyncTransition]] = []
            cumulative = 0.0
            for tn in possible_transitions:
                if callable(tn.probability):
                    cumulative += tn.probability(self.context)
                else:
                    cumulative += tn.probability
                probabilities.append((cumulative, tn))
            choice = self.random() * cumulative
            for probability, tn in probabilities:
                if choice < probability:
                    transition = tn
                    break
            if not transition:
                return self.current # no valid transition selected
            self.next = transition.to_state

        if event in self._event_hooks:
            canceled = False
            for hook in self._event_hooks[event]:
                val = hook(event, self, data)
                if iscoroutine(val):
                    val = await val
                if val is False:
                    canceled = True
            if canceled:
                return self.current

        if transition:
            self.previous = self.current
            self.current = self.next
            self.next = None
            await transition.trigger(self.context, data)

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
        fsm = f"""\
        {left_eye}{space}{right_eye}
        {left_stem}{right_stem}
        {middle_space}((({self.current})))
        {self._valid_transitions}
                s     s        s         s
               s        s     s            s
              s        s                  s
               s                            s

        ~Touched by His Noodly Appendage~"""
        # fix formatting of output; avoid screwing up code folding of this
        # method in vim
        fsm = '\n'.join([l[8:] for l in fsm.split('\n')])
        return fsm

    def pack(self) -> bytes:
        """Serialize to bytes using packify."""
        if isinstance(self.initial_state, Enum):
            initial_state = [
                type(self.initial_state).__name__,
                self.initial_state.value
            ]
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
            'context': self.context,
        })

    @classmethod
    def unpack(
            cls, data: bytes, inject: dict = {},
            transition_hooks: dict[
                AsyncTransition,
                list[Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]]
            ] = {},
            event_hooks: dict[
                Enum|str,
                list[Callable[[Enum|str, AsyncFSM, Any], bool | Awaitable[bool]]]
            ] = {},
            random: Callable[[], float] = random
        ) -> AsyncFSM:
        """Deserialize from bytes using packify. Inject dependencies
            as necessary, e.g. the Enum classes representing states or
            events.
        """
        dependencies = {**globals(), **inject}
        data = unpack(data, inject=dependencies)
        fsm = cls(context=data['context'], random=random)
        for transition, hooks in transition_hooks.items():
            type_assert(type(hooks) is list,
                'transition_hooks must be list[Callable]'
            )
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
            type_assert(type(hooks) is list, 'event_hooks must be list[Callable]')
            for hook in hooks:
                fsm.add_event_hook(event, hook)
        return fsm
