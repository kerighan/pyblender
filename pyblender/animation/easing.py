"""Easing functions mapping a unitless time ``x`` in [0, 1] to a progress in [0, 1].

Every function accepts a float or a numpy array.
"""

import numpy as np


def tween(easing, a, b=None, t=0.0):
    """Interpolate from ``a`` (at ``t == 0``) to ``b`` (at ``t == 1``) with the named easing.

    ``"constant"`` or ``b is None`` always returns ``a``. Unknown names fall back to
    ``cubic-in-out``.
    """
    if easing == "constant" or b is None:
        return a
    progress = EASINGS.get(easing, cubic_in_out)(t)
    return a + (b - a) * progress


def _piecewise(x, below, above):
    """Apply ``below`` where ``x < 0.5`` and ``above`` elsewhere, for scalars and arrays."""
    x = np.asarray(x, dtype=float)
    # both branches are evaluated, so clamp their inputs to their own half-range
    result = np.where(x < 0.5, below(np.minimum(x, 0.5)), above(np.maximum(x, 0.5)))
    return float(result) if result.ndim == 0 else result


def linear(x):
    return x


def quad_in(x):
    return x ** 2


def quad_out(x):
    return 1 - (1 - x) ** 2


def quad_in_out(x):
    return _piecewise(x, lambda x: 2 * x ** 2, lambda x: 1 - 2 * (1 - x) ** 2)


def cubic_in(x):
    return x ** 3


def cubic_out(x):
    return 1 - (1 - x) ** 3


def cubic_in_out(x):
    return _piecewise(x, lambda x: 4 * x ** 3, lambda x: 1 - 4 * (1 - x) ** 3)


def quart_in(x):
    return x ** 4


def quart_out(x):
    return 1 - (1 - x) ** 4


def quart_in_out(x):
    return _piecewise(x, lambda x: 8 * x ** 4, lambda x: 1 - 8 * (1 - x) ** 4)


def quint_in(x):
    return x ** 5


def quint_out(x):
    return 1 - (1 - x) ** 5


def quint_in_out(x):
    return _piecewise(x, lambda x: 16 * x ** 5, lambda x: 1 - 16 * (1 - x) ** 5)


def _exact_ends(x, value):
    """Exponential easings never reach 0 or 1 exactly, so pin the endpoints."""
    x = np.asarray(x, dtype=float)
    result = np.where(x <= 0, 0.0, np.where(x >= 1, 1.0, value))
    return float(result) if result.ndim == 0 else result


def exp_in(x):
    return _exact_ends(x, 2.0 ** (10 * (np.asarray(x, dtype=float) - 1)))


def exp_out(x):
    return _exact_ends(x, 1 - 2.0 ** (-10 * np.asarray(x, dtype=float)))


def exp_in_out(x):
    return _exact_ends(x, _piecewise(
        x, lambda x: 0.5 * 2.0 ** (20 * x - 10), lambda x: 1 - 0.5 * 2.0 ** (10 - 20 * x)))


def sine_in(x):
    return 1 - np.cos(x * np.pi / 2)


def sine_out(x):
    return np.sin(x * np.pi / 2)


def sine_in_out(x):
    return 0.5 * (1 - np.cos(x * np.pi))


def circ_in(x):
    return 1 - np.sqrt(1 - x ** 2)


def circ_out(x):
    return np.sqrt(1 - (x - 1) ** 2)


def circ_in_out(x):
    return _piecewise(
        x,
        lambda x: 0.5 * (1 - np.sqrt(1 - 4 * x ** 2)),
        lambda x: 0.5 * (np.sqrt(1 - (2 * x - 2) ** 2) + 1),
    )


# ----------------------------------------------------------------------
# Motion-design easings: these overshoot, so they leave the [0, 1] range
# ----------------------------------------------------------------------

_BACK = 1.70158


def back_in(x):
    return x ** 2 * ((_BACK + 1) * x - _BACK)


def back_out(x):
    return _exact_ends(x, 1 - back_in(1 - np.asarray(x, dtype=float)))


def back_in_out(x):
    return _piecewise(x, lambda x: 0.5 * back_in(2 * x), lambda x: 0.5 * back_out(2 * x - 1) + 0.5)


def elastic_out(x):
    x = np.asarray(x, dtype=float)
    value = 2.0 ** (-10 * x) * np.sin((x * 10 - 0.75) * 2 * np.pi / 3) + 1
    return _exact_ends(x, value)


def bounce_out(x):
    x = np.asarray(x, dtype=float)
    n, d = 7.5625, 2.75
    result = np.where(
        x < 1 / d, n * x ** 2,
        np.where(x < 2 / d, n * (x - 1.5 / d) ** 2 + 0.75,
                 np.where(x < 2.5 / d, n * (x - 2.25 / d) ** 2 + 0.9375,
                          n * (x - 2.625 / d) ** 2 + 0.984375)))
    return _exact_ends(x, result)


EASINGS = {
    "linear": linear,
    "quad-in": quad_in, "quad-out": quad_out, "quad-in-out": quad_in_out,
    "cubic-in": cubic_in, "cubic-out": cubic_out, "cubic-in-out": cubic_in_out,
    "quart-in": quart_in, "quart-out": quart_out, "quart-in-out": quart_in_out,
    "quint-in": quint_in, "quint-out": quint_out, "quint-in-out": quint_in_out,
    "exp-in": exp_in, "exp-out": exp_out, "exp-in-out": exp_in_out,
    "sine-in": sine_in, "sine-out": sine_out, "sine-in-out": sine_in_out,
    "circ-in": circ_in, "circ-out": circ_out, "circ-in-out": circ_in_out,
    "back-in": back_in, "back-out": back_out, "back-in-out": back_in_out,
    "elastic-out": elastic_out, "bounce-out": bounce_out,
}
