from argparse import ArgumentTypeError


def lower_bounded_int(value, lower_bound_exclusive):
    v = int(value)
    if v < lower_bound_exclusive:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def upper_bounded_int(value, upper_bound_exclusive):
    v = int(value)
    if v > upper_bound_exclusive:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def age_int(value):
    lower_bounded_int(value, 0)
    return upper_bounded_int(value, 100)


def positive_int(value):
    return lower_bounded_int(value, 1)


def non_negative_int(value):
    return lower_bounded_int(value, 0)
