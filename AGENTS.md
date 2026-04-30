# Agent Instructions

## Testing

Run tests with:
```bash
source venv/bin/activate && python tests/test_classes.py
```

## Test Details

- **Framework**: unittest (25 tests total)
- **Test file**: `tests/test_classes.py`
- **Path setup**: Tests import via `context.py` which manipulates `sys.path` to import from parent directory
- **Run specific tests**: Use `-k` flag, e.g., `python tests/test_classes.py -k serialization`
- **Visual test**: `test_FSM_subclass_touched_is_Flying_Spaghetti_monster_str` prints FSM serialization output

## Project Structure

- **Main classes**: `FSM`, `Transition` (in `flying_state_machines/classes.py`)
- **Exports**: Both classes exported from `flying_state_machines/__init__.py`
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

