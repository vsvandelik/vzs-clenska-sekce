from argparse import ArgumentTypeError


def lower_bounded_int(value, lower_bound_inclusive):
    v = int(value)
    if v < lower_bound_inclusive:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def upper_bounded_int(value, upper_bound_inclusive):
    v = int(value)
    if v > upper_bound_inclusive:
        raise ArgumentTypeError(f"{v} is an invalid value")
    return v


def age_int(value):
    lower_bounded_int(value, 1)
    return upper_bounded_int(value, 99)


def positive_int(value):
    return lower_bounded_int(value, 1)


def non_negative_int(value):
    return lower_bounded_int(value, 0)
