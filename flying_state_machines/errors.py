def type_assert(condition: bool, msg: str):
    if not condition:
        raise TypeError(msg)

def value_assert(condition: bool, msg: str):
    if not condition:
        raise ValueError(msg)

