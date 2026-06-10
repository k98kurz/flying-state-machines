from flying_state_machines import AsyncFSM, AsyncTransition
from enum import Enum, auto
from hashlib import sha256
from random import random
from typing import Any
import asyncio
import struct
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


class Machine(AsyncFSM):
    rules = set([
        AsyncTransition(State.WAITING, Event.CONTINUE, State.WAITING),
        AsyncTransition(State.WAITING, Event.START, State.GOING),
        AsyncTransition(State.GOING, Event.CONTINUE, State.GOING),
        AsyncTransition(State.GOING, Event.STOP, State.WAITING),
        *AsyncTransition.from_any(
            State, Event.QUANTUM_FOAM, State.SUPERPOSITION, 0.5
        ),
        *AsyncTransition.from_any(
            State, Event.QUANTUM_FOAM, State.NEITHER, 0.5
        ),
        *AsyncTransition.to_any(
            State.SUPERPOSITION, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
        *AsyncTransition.to_any(
            State.NEITHER, Event.NORMALIZE, [State.WAITING, State.GOING]
        ),
    ])
    initial_state = State.WAITING


class StrMachine(AsyncFSM):
    rules = set([
        AsyncTransition('hungry', 'get food', 'eating'),
        AsyncTransition('eating', 'food gone', 'sad'),
        AsyncTransition('sad', 'time passes', 'hungry'),
    ])
    initial_state = 'hungry'


class TestTransition(unittest.TestCase):
    def test_AsyncTransition_initializes_properly(self):
        AsyncTransition(State.WAITING, Event.START, State.GOING)
        AsyncTransition("WAITING", "START", "GOING")

        with self.assertRaises(TypeError) as e:
            AsyncTransition(b'waiting', State.GOING, Event.START)
        assert str(e.exception) == 'from_state must be Enum or str'

        with self.assertRaises(TypeError) as e:
            AsyncTransition(State.WAITING, Event.START, b'State.GOING')
        assert str(e.exception) == 'to_state must be Enum or str'

        with self.assertRaises(TypeError) as e:
            AsyncTransition(State.WAITING, b'Event.START', State.GOING)
        assert str(e.exception) == 'on_event must be Enum or str'

    def test_AsyncTransition_is_hashable(self):
        tn1 = AsyncTransition(State.WAITING, State.GOING, Event.START)
        tn2 = AsyncTransition(State.GOING, State.WAITING, Event.STOP)
        assert hash(tn1) != hash(tn2)

    def test_AsyncTransition_callable_probability_evaluates_with_context(self):
        def weight_based_probability(ctx):
            return ctx.get('weight', 0.5)

        transition = AsyncTransition(
            'patrol', 'see_enemy', 'hunt', probability=weight_based_probability
        )

        assert callable(transition.probability)
        assert transition.probability({'weight': 1.0}) == 1.0
        assert transition.probability({'weight': 0.0}) == 0.0
        assert transition.probability({'weight': 0.75}) == 0.75
        assert transition.probability({}) == 0.5

    def test_AsyncTransition_hooks_e2e(self):
        transition = AsyncTransition(State.WAITING, State.GOING, Event.START)
        log = {'count': 0, 'data': []}

        with self.assertRaises(TypeError) as e:
            transition.add_hook(1)
        assert str(e.exception) == 'hook must be Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]'

        with self.assertRaises(TypeError) as e:
            transition.remove_hook(1)
        assert str(e.exception) == 'hook must be Callable[[AsyncTransition, dict, Any], None | Awaitable[None]]'

        def hook(tn, *args):
            log['count'] += 1
            if len(args) and args[0] is not None:
                log['data'].append(args[0])
        async def async_hook(tn, *args):
            log['count'] += 1
            if len(args) and args[0] is not None:
                log['data'].append(args[0])
        transition.add_hook(hook)
        transition.add_hook(async_hook)
        asyncio.run(transition.trigger())
        assert log['count'] == 2
        assert len(log['data']) == 0
        asyncio.run(transition.trigger('some event data'))
        assert log['count'] == 4
        assert len(log['data']) == 2
        transition.remove_hook(hook)
        transition.remove_hook(async_hook)
        asyncio.run(transition.trigger('some event data'))
        assert log['count'] == 4
        assert len(log['data']) == 2

    def test_transition_hooks_receive_context(self):
        t = AsyncTransition('patrol', 'see_enemy', 'hunt')
        captured = {'context': None, 'data': None}

        def hook(transition, context, data):
            captured['context'] = context
            captured['data'] = data

        t.add_hook(hook)

        test_context = {'key': 'value', 'hunger': True}
        asyncio.run(t.trigger(test_context, 'event_data'))

        assert captured['context'] == test_context
        assert captured['data'] == 'event_data'

    def test_AsyncTransition_from_any_returns_list_of_AsyncTransition(self):
        tns = AsyncTransition.from_any(
            State, Event.QUANTUM_FOAM, State.SUPERPOSITION
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert tn.to_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM

        tns = AsyncTransition.from_any(
            ['WAITING', 'GOING'], 'QUANTUM_FOAM', 'SUPERPOSITION'
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert tn.to_state == 'SUPERPOSITION'
            assert tn.on_event == 'QUANTUM_FOAM'

    def test_AsyncTransition_to_any_returns_list_of_AsyncTransition(self):
        tns = AsyncTransition.to_any(
            State.SUPERPOSITION, Event.QUANTUM_FOAM, State, 0.8
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert tn.from_state is State.SUPERPOSITION
            assert tn.on_event is Event.QUANTUM_FOAM
            assert tn.probability == 0.2, (
                f'total_probability should be split evenly; 0.2 != {tn.probability}')

        tns = AsyncTransition.to_any(
            "SUPERPOSITION", "QUANTUM_FOAM", ["GOING", "GONE"]
        )
        assert type(tns) is list
        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert tn.from_state == 'SUPERPOSITION'
            assert tn.on_event == 'QUANTUM_FOAM'

    def test_AsyncTransition_from_any_with_callable_probability(self):
        def ctx_based_prob(ctx):
            return 1.0 if ctx.get('condition', False) else 0.5

        tns = AsyncTransition.from_any(
            ['idle', 'active'], 'event', 'result_state',
            probability=ctx_based_prob
        )

        assert type(tns) is list
        assert len(tns) == 2

        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert callable(tn.probability)
            assert tn.to_state == 'result_state'
            assert tn.on_event == 'event'
            assert tn.probability({'condition': True}) == 1.0
            assert tn.probability({'condition': False}) == 0.5

    def test_AsyncTransition_to_any_with_callable_probability(self):
        def dynamic_prob(ctx):
            return ctx.get('energy', 0.0)

        tns = AsyncTransition.to_any(
            'start', 'trigger', ['state_a', 'state_b', 'state_c'],
            total_probability=dynamic_prob
        )

        assert type(tns) is list
        assert len(tns) == 3

        for tn in tns:
            assert isinstance(tn, AsyncTransition)
            assert callable(tn.probability)
            assert tn.from_state == 'start'
            assert tn.on_event == 'trigger'
            assert tn.probability({'energy': 0.8}) == 0.8

    def test_AsyncTransition_pack_and_unpack_e2e(self):
        t = AsyncTransition(State.WAITING, Event.CONTINUE, State.WAITING)
        hooked = False
        def hook(_tn, *_args):
            nonlocal hooked
            hooked = True
            return True

        t.add_hook(hook)
        packed = t.pack()
        assert type(packed) is bytes
        unpacked = AsyncTransition.unpack(packed, inject={
            'State': State,
            'Event': Event,
        }, hooks=[hook])
        assert type(unpacked) is AsyncTransition
        assert hash(t) == hash(unpacked)
        assert not hooked
        asyncio.run(unpacked.trigger())
        assert hooked

        def energy_based_probability(ctx):
            return ctx.get('energy', 0.5)

        transition_with_callable = AsyncTransition(
            'resting', 'wake_up', 'active',
            probability=energy_based_probability
        )

        packed = transition_with_callable.pack()
        assert type(packed) is bytes

        unpacked = AsyncTransition.unpack(
            packed, inject={
                'energy_based_probability': energy_based_probability,
            }, hooks=[]
        )

        assert type(unpacked) is AsyncTransition
        assert hash(transition_with_callable) == hash(unpacked)
        assert callable(unpacked.probability)
        assert unpacked.probability({'energy': 0.8}) == 0.8

    def test_AsyncTransition_hooks_are_not_shared(self):
        t1 = AsyncTransition(State.WAITING, Event.START, State.GOING)
        t2 = AsyncTransition(State.GOING, Event.STOP, State.WAITING)
        assert t1.hooks is not t2.hooks

        def hook1(_tn, *_args):
            ...

        t1.add_hook(hook1)
        assert len(t1.hooks) == 1
        assert len(t2.hooks) == 0


class TestFSM(unittest.TestCase):
    def test_direct_AsyncFSM_initialization_raises_error(self):
        with self.assertRaises(ValueError) as e:
            AsyncFSM()
        assert str(e.exception) == 'self.rules must be set[AsyncTransition]'

    def test_AsyncFSM_subclass_initializes_properly(self):
        machine = Machine()
        assert hasattr(machine, 'rules') and type(machine.rules) is set
        assert hasattr(machine, 'initial_state') and type(machine.initial_state) is State
        assert hasattr(machine, 'current') and type(machine.current) is State
        assert hasattr(machine, 'previous') and machine.previous is None
        assert hasattr(machine, 'next') and machine.next is None

    def test_AsyncFSM_subclass_would_returns_tuple_of_AsyncTransition(self):
        machine = Machine()
        tns = machine.would(Event.CONTINUE)
        assert type(tns) is tuple
        for tn in tns:
            assert isinstance(tn, AsyncTransition)

        assert len(machine.would('random event')) == 0

    def test_AsyncFSM_subclass_can_returns_bool_for_event(self):
        async def test():
            machine = Machine()
            assert machine.can(Event.START)
            assert not machine.can('random event')
            await machine.input(Event.START)
            assert not machine.can(Event.START)
            assert machine.can(Event.CONTINUE)
            assert machine.can(Event.STOP)
        asyncio.run(test())

    def test_AsyncFSM_subclass_input_returns_state_after_AsyncTransition(self):
        async def _test():
            machine = Machine()
            assert machine.current is State.WAITING
            res = await machine.input(Event.START)
            assert machine.current is State.GOING
            assert res is machine.current
        asyncio.run(_test())

    def test_AsyncFSM_dynamic_probabilities_with_context(self):
        def attack_when_strong(ctx):
            return 1.0 if ctx['strength'] else 0.0

        def retreat_when_weak(ctx):
            return 0.0 if ctx['strength'] else 1.0

        class GuardFSM(AsyncFSM):
            rules = set([
                AsyncTransition(
                    'patrol', 'see_enemy', 'attack', probability=attack_when_strong
                ),
                AsyncTransition(
                    'patrol', 'see_enemy', 'retreat', probability=retreat_when_weak
                ),
            ])
            initial_state = 'patrol'

        async def _test():
            strong_guard = GuardFSM(context={'strength': True})
            for _ in range(5):
                strong_guard.current = 'patrol'
                result = await strong_guard.input('see_enemy')
                assert result == 'attack'
                assert strong_guard.current == 'attack'

            weak_guard = GuardFSM(context={'strength': False})
            for _ in range(5):
                weak_guard.current = 'patrol'
                result = await weak_guard.input('see_enemy')
                assert result == 'retreat'
                assert weak_guard.current == 'retreat'

            strong_guard.context = {'strength': False}
            for _ in range(5):
                strong_guard.current = 'patrol'
                result = await strong_guard.input('see_enemy')
                assert result == 'retreat'
        asyncio.run(_test())

    def test_AsyncFSM_subclass_event_hooks_fire_on_event(self):
        machine = Machine()
        log = {}
        def hook(event, *args):
            if event not in log:
                log[event] = 0
            if (event, 'data') not in log:
                log[(event, 'data')] = [a for a in args if a is not None]
            log[event] += 1
        async def async_hook(event, *args):
            if event not in log:
                log[event] = 0
            if (event, 'data') not in log:
                log[(event, 'data')] = [a for a in args if a is not None]
            log[event] += 1

        with self.assertRaises(TypeError) as e:
            machine.add_event_hook(Event.START, 1)
        assert str(e.exception) == 'hook must be Callable[[Enum|str, AsyncFSM, Any], bool | Awaitable[bool]]'

        machine.add_event_hook(Event.START, hook)
        machine.add_event_hook(Event.START, async_hook)
        machine.add_event_hook('fake event', hook)
        machine.add_event_hook('fake event', async_hook)

        async def _test():
            assert 'fake event' not in log
            await machine.input('fake event')
            assert 'fake event' in log and log['fake event'] == 2, log
            assert ('fake event', 'data') in log, log
            assert len(log[('fake event', 'data')]) == 1, log

            assert Event.START not in log
            await machine.input(Event.START, 'some data')
            assert Event.START in log and log[Event.START] == 2, log
            assert (Event.START, "data") in log, log
            assert len(log[(Event.START, "data")]) == 2, log[(Event.START, "data")]
            assert log[(Event.START, "data")][1] == 'some data', (
                log[(Event.START, "data")])
            await machine.input(Event.START)
            assert log[Event.START] == 4, log[Event.START]
            machine.remove_event_hook(Event.START, hook)
            machine.remove_event_hook(Event.START, async_hook)
            await machine.input(Event.START)
            assert log[Event.START] == 4, log[Event.START]
        asyncio.run(_test())

    def test_AsyncFSM_subclass_event_hooks_can_cancel_AsyncTransition(self):
        machine = Machine()
        log = {}
        def hook(event, *args):
            if event not in log:
                log[event] = 0
            log[event] += 1
            return False

        assert machine.current is State.WAITING
        machine.add_event_hook(Event.START, hook)
        asyncio.run(machine.input(Event.START))
        assert machine.current is State.WAITING
        assert Event.START in log and log[Event.START] == 1, log

        # also verify async event hook can cancel
        machine2 = Machine()
        log = {}
        async def async_hook(event, *args):
            if event not in log:
                log[event] = 0
            log[event] += 1
            return False

        assert machine2.current is State.WAITING
        machine2.add_event_hook(Event.START, async_hook)
        asyncio.run(machine2.input(Event.START))
        assert machine2.current is State.WAITING
        assert Event.START in log and log[Event.START] == 1, log

    def test_AsyncFSM_subclass_transition_hooks_e2e(self):
        machine = Machine()
        log = {}
        def hook(transition, *args):
            if transition not in log:
                log[transition] = 0
            log[transition] += 1
        async def async_hook(transition, *args):
            if transition not in log:
                log[transition] = 0
            log[transition] += 1

        tn = machine.would(Event.START)[0]
        machine.add_transition_hook(tn, hook)
        machine.add_transition_hook(tn, async_hook)
        async def _test():
            assert tn not in log
            await machine.input(Event.START)
            assert tn in log and log[tn] == 2, log

            machine.remove_transition_hook(tn, hook)
            machine.remove_transition_hook(tn, async_hook)
            await machine.input(Event.STOP)
            assert machine.would(Event.START)[0] is tn
            await machine.input(Event.START)
            assert log[tn] == 2, log[tn]
        asyncio.run(_test())

    def test_transition_hooks_receive_context(self):
        machine = Machine()
        captured = {'context': None, 'data': None}

        def hook(transition, context, data):
            captured['context'] = context
            captured['data'] = data

        transition = machine.would(Event.START)[0]
        machine.add_transition_hook(transition, hook)

        machine.context = {'key': 'value', 'hunger': True}
        asyncio.run(machine.input(Event.START, 'event_data'))

        assert captured['context'] == machine.context
        assert captured['data'] == 'event_data'

    def test_AsyncFSM_subclass_random_transitions(self):
        machine = Machine()
        superposition, neither = 0, 0

        async def _test():
            nonlocal superposition, neither
            for _ in range(10):
                await machine.input(Event.QUANTUM_FOAM)
                if machine.current is State.SUPERPOSITION:
                    superposition += 1
                if machine.current is State.NEITHER:
                    neither += 1

        asyncio.run(_test())

        assert superposition + neither == 10
        assert superposition > 0
        assert neither > 0

        waiting, going = 0, 0
        async def _test2():
            nonlocal waiting, going
            for i in range(10):
                machine.current = State.SUPERPOSITION if i%2 else State.NEITHER
                await machine.input(Event.NORMALIZE)
                if machine.current is State.WAITING:
                    waiting += 1
                if machine.current is State.GOING:
                    going += 1

        asyncio.run(_test2())

        assert waiting + going == 10
        assert waiting > 0
        assert going > 0

    def test_AsyncFSM_pack_and_unpack_e2e(self):
        machine = Machine()
        hooked = False
        def hook(_event, *_args):
            nonlocal hooked
            hooked = True
            return True
        machine.add_event_hook(Event.START, hook)
        packed = machine.pack()
        assert type(packed) is bytes
        unpacked = Machine.unpack(packed, inject={
            'State': State,
            'Event': Event,
        }, event_hooks={Event.START: [hook]})
        assert type(unpacked) is Machine
        assert machine.initial_state == unpacked.initial_state, \
            (machine.initial_state, unpacked.initial_state)
        assert machine.current == unpacked.current, \
            (machine.current, unpacked.current)
        assert machine.previous == unpacked.previous, \
            (machine.previous, unpacked.previous)
        assert machine.next == unpacked.next, \
            (machine.next, unpacked.next)
        assert not hooked
        asyncio.run(unpacked.input(Event.START))
        assert hooked

        machine_with_context = Machine(context={'hunger': 0.7, 'energy': 0.5})
        packed = machine_with_context.pack()
        unpacked = Machine.unpack(packed, inject={
            'State': State,
            'Event': Event,
        })
        assert unpacked.context == {'hunger': 0.7, 'energy': 0.5}
        assert unpacked.initial_state == machine_with_context.initial_state

    def test_AsyncFSM_subclass_touched_is_Flying_Spaghetti_monster_str(self):
        machine = Machine()
        async def _test():
            if random() < 0.2:
                await machine.input(Event.START)
            elif random() < 0.5:
                await machine.input(Event.QUANTUM_FOAM)
        asyncio.run(_test())
        print('\n' + machine.touched())
        assert len(machine.touched()) > 10 * len(machine.rules)
        assert machine.touched()[-33:] == '~Touched by His Noodly Appendage~'

    def test_AsyncFSM_subclass_with_str_states_and_events_e2e(self):
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
        async def _test():
            nonlocal log
            assert tn not in log and 'get food' not in log
            state = await machine.input('get food')
            assert tn in log and 'get food' in log
            assert machine.current == state == 'eating'
            assert machine.previous == 'hungry'
            await machine.input('get food')
            assert machine.current == 'eating'
            await machine.input('time passes')
            assert machine.current == 'eating'
            await machine.input('food gone')
            assert machine.current == 'sad'
            assert machine.previous == 'eating'
            await machine.input('time passes')
            assert machine.current == 'hungry'
            assert machine.previous == 'sad'
        asyncio.run(_test())

    def test_AsyncFSM_custom_random_e2e(self):
        class Randomizer:
            def __init__(self, seed: bytes = b'test'):
                self.seed = seed
                self.nonce = 0
            def next(self) -> bytes:
                self.nonce += 1
                return sha256(self.seed + self.nonce.to_bytes(4, 'big')).digest()
            def next_float(self) -> float:
                return struct.unpack('!d', self.next()[:8])[0]
            def reset(self):
                self.nonce = 0

        randomizer = Randomizer()
        random = lambda: randomizer.next_float()

        # quick sanity check for the Randomizer
        assert Randomizer(b'123').next() != Randomizer(b'321').next(), (
            'different seeds should produce different byte streams'
        )
        assert randomizer.next() != randomizer.next(), (
            'subsequent calls should return different bytes'
        )

        # first run without the custom randomizer
        transitions1 = [0, 0]
        for _ in range(100):
            machine = Machine()
            asyncio.run(machine.input(Event.QUANTUM_FOAM))
            if machine.current is State.NEITHER:
                transitions1[0] += 1
            else:
                transitions1[1] += 1

        # now run with custom, deterministic randomizer
        transitions2 = [0, 0]
        for _ in range(100):
            randomizer.reset()
            machine = Machine(random=random)
            asyncio.run(machine.input(Event.QUANTUM_FOAM))
            if machine.current is State.NEITHER:
                transitions2[0] += 1
            else:
                transitions2[1] += 1

        # using random.random() should provide a mix of transitions
        assert transitions1[0] > 1 and transitions1[1] > 1, transitions1
        # custom randomizer with reset should be deterministic
        assert transitions2[0] == 0 or transitions2[1] == 0, transitions2
        assert transitions2[0] == 100 or transitions2[1] == 100, transitions2

        # now test pack and unpack with custom randomizer
        transitions3 = [0, 0]
        for _ in range(100):
            randomizer.reset()
            machine = Machine.unpack(
                Machine().pack(),
                inject=globals(),
                random=random
            )
            asyncio.run(machine.input(Event.QUANTUM_FOAM))
            if machine.current is State.NEITHER:
                transitions3[0] += 1
            else:
                transitions3[1] += 1

        # should be deterministic
        assert transitions3[0] == 0 or transitions3[1] == 0, transitions3
        assert transitions3[0] == 100 or transitions3[1] == 100, transitions2


if __name__ == "__main__":
    unittest.main()
