import numpy as np


def tween(name, a=0, b=1, t=0):
    """Take an easing name as argument, and return the interpolated value
    where `a` is the starting value at t == 0 and `b` is the ending value
    at t == 1.

    Arguments:
        name {str} -- the name of the easing function, as in name2easing
        a {float} -- the starting value, returned when t == 0
        b {float} -- the ending value, returned when t == 1
        t {float} -- the time parameter. Unitless, must be between 0 and 1

    Keyword Arguments:
        a {int} -- [description] (default: {0})
        b {int} -- [description] (default: {1})
        t {int} -- [description] (default: {0})

    Returns:
        float or np.ndarray -- return the interpolated value at time t
    """

    if name == "constant":
        return a
    easing = name2easing.get(name, cubic_in_out)
    return (a - b) * (1 - easing(t)) + b


# ======
# Linear
# ======

def linear(x):
    return x


# ============
# Quad easings
# ============

def quad_in(x):
    return x**2


def quad_out(x):
    return -(x - 1)**2 + 1


def quad_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            2 * x**2,
            (-2 * x**2) + (4 * x) - 1,
        ]
        return np.select(condlist, choicelist)
    if x < 0.5:
        return 2 * x**2
    return (-2 * x**2) + (4 * x) - 1


# =============
# Cubic easings
# =============

def cubic_in(x):
    return x**3


def cubic_out(x):
    return (x - 1)**3 + 1


def cubic_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            4 * x**3,
            0.5 * (2 * x - 2)**3 + 1,
        ]
        return np.select(condlist, choicelist)
    else:
        if x < 0.5:
            return 4 * x**3
        p = 2 * x - 2
        return 0.5 * p**3 + 1


# =============
# Quart easings
# =============

def quart_in(x):
    return x**4


def quart_out(x):
    return -(x - 1)**4 + 1


def quart_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            8 * x**4,
            -8 * (x - 1)**4 + 1,
        ]
        return np.select(condlist, choicelist)
    else:
        if x < 0.5:
            return 8 * x**4
        p = x - 1
        return -8 * p**4 + 1


# =============
# Quint easings
# =============

def quint_in(x):
    return x**5


def quint_out(x):
    return (x - 1)**5 + 1


def quint_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            16 * x**5,
            0.5 * (2 * x - 2)**5 + 1,
        ]
        return np.select(condlist, choicelist)
    else:
        if x < 0.5:
            return 16 * x**5
        p = 2 * x - 2
        return 0.5 * p**5 + 1


# ===================
# Exponential easings
# ===================

def exp_in(x):
    return 2**(10 * (x - 1))


def exp_out(x):
    return -2**(-10 * x) + 1.


def exp_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            0.5 * 2**(20 * x - 10),
            1 - 0.5 * 2**(-20 * x + 10),
        ]
        return np.select(condlist, choicelist)
    else:
        if x < 0.5:
            return 0.5 * 2**(20 * x - 10)
        return 1 - 0.5 * 2**(-20 * x + 10)


# ================
# Circular easings
# ================

def sine_in_out(self, x):
    return 0.5 * (1 - np.cos(x * np.pi))


def circ_in_out(x):
    if isinstance(x, np.ndarray):
        condlist = [
            x < 0.5,
            x >= 0.5
        ]
        choicelist = [
            0.5 * (1 - (1 - 4 * x**2)**0.5),
            0.5 * ((-(2 * x - 3) * (2 * x - 1))**0.5 + 1),
        ]
        return np.select(condlist, choicelist)
    else:
        if x < 0.5:
            return 0.5 * (1 - (1 - 4 * x**2)**0.5)
        return 0.5 * ((-(2 * x - 3) * (2 * x - 1))**0.5 + 1)


# =========
# Namespace
# =========

name2easing = {
    "linear": linear,
    # quad easing
    "quad-in": quad_in,
    "quad-out": quad_out,
    "quad-in-out": quad_in_out,
    # cubic easing
    "cubic-in": cubic_in,
    "cubic-out": cubic_out,
    "cubic-in-out": cubic_in_out,
    # quart easing
    "quart-in": quart_in,
    "quart-out": quart_out,
    "quart-in-out": quart_in_out,
    # quint easing
    "quint-in": quint_in,
    "quint-out": quint_out,
    "quint-in-out": quint_in_out,
    # exp easing
    "exp-in": exp_in,
    "exp-out": exp_out,
    "exp-in-out": exp_in_out,
    # circular easing
    "sine-in-out": sine_in_out,
    "circ-in-out": circ_in_out,
}
