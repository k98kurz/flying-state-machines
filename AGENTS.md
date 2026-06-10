# Agent Instructions

## Code Style

The code style guidelines can be found in codestyle.md.

## Testing

Run tests with:
```bash
source venv/bin/activate && python tests/test_classes.py && python tests/test_asynclasses.py
```

## Test Details

- **Framework**: unittest (52 tests total: 26 sync + 26 async)
- **Test files**: `tests/test_classes.py` and `tests/test_asynclasses.py`
- **Import path**: Tests import directly from the `flying_state_machines` package
- **Run specific tests**: Use `-k` flag, e.g., `python tests/test_classes.py -k serialization`
- **Visual tests**: `test_FSM_subclass_touched_is_Flying_Spaghetti_monster_str` (sync) and `test_AsyncFSM_subclass_touched_is_Flying_Spaghetti_monster_str` (async) print FSM serialization output

## Project Structure

- **Main classes**: `FSM`, `Transition`, `AsyncFSM`, `AsyncTransition` (in `flying_state_machines/classes.py` and `asynclasses.py`)
- **Exports**: All four classes exported from `flying_state_machines/__init__.py`
- **Build system**: hatchling
- **Key dependency**: packify >= 0.3.1 (for serialization)

## Key Features

- Supports Enum or str for states/events
- Probabilistic transitions (Markov chains)
- Dynamic probabilities via callbacks accepting context dict
- Event hooks (can cancel transitions) and transition hooks
- Serialization via packify (hooks and callables require inject dict)

## Documentation

- dox.md: generated with the autodox command; let a human do this
- changelog.md: requires entries for each library change
- readme.md: requires updates to maintain alignment with library capabilities

