"""
Optimization task (Quantitative Analysis screener), reproduced from the
individual version of the Optimization task in Weidmann & Deming,
"Team Players: How Social Skills Improve Team Performance" (Econometrica 2021),
original code: https://github.com/gabemansur/Teamwork
(public/js/optimization.js, app/Tasks/Optimization.php,
 resources/views/layouts/participants/tasks/optimization-individual*.blade.php).

As in their lab individual stage: practice on function a1 ('t1'), then three
scored rounds with functions 1, 2, 3 ('a', 'b', 'c'), 15 guesses each plus a
final answer; only the final answer counts. Score per round (their
calcOptimizationScore): 1 - (ymax - f(final)) / (ymax - ymin), in [0, 1].

Difference from the original: results are computed on the server (oTree
live_method) instead of in the browser, so the formulas cannot be read from
the page source.
"""

from math import sin, cos, exp

X_MIN, X_MAX = 0, 300
MAX_GUESSES = 15
ROUND_FUNCTIONS = ['a', 'b', 'c']   # their labels '1', '2', '3'
PRACTICE_FUNCTION = 't1'            # their label 'a1'


def _g(x, c, w):
    return exp(-(((x - c) / w) ** 2))


FUNCTIONS = {
    't1': lambda x: 100 * (sin(x / 30) + (x / 300) ** 2),
    't2': lambda x: -10 + 100 * sin(x / 50) + x ** 2 / 500,
    'a': lambda x: 40 * sin(x / 15) + 100 * cos(x / 60) + x / 10,
    'b': lambda x: 150 - (150 - x) ** 2 / 150 + 100 * cos(x / 20),
    'c': lambda x: 10 + x / 3 - 150 * _g(x, 245, 15),
    'd': lambda x: 40 * sin((x - 20) / 15) + 100 * cos((x - 20) / 15) + x / 3,
    'e': lambda x: 100 - x / 3 - 50 * _g(x, 50, 15) + 150 * _g(x, 245, 15),
    'f': lambda x: 100 + 50 * _g(x, 50, 15) + 100 * _g(x, 150, 15) + 150 * _g(x, 275, 15),
    'g': lambda x: -50 - x / 5 + 40 * _g(x, 270, 30),
    'h': lambda x: x / 4 + 100 * _g(x, 50, 15) + 50 * _g(x, 150, 10)
    - 50 * _g(x, 250, 30) - 50 * _g(x, 300, 15),
    'i': lambda x: x / 4 + _g(x, 50, 15) + 100 * cos(x / 10) + 100 * sin(x / 30),
    'j': lambda x: 80 * _g(x, 50, 20) + (x / 2 - 200 * _g(x, 280, 10)) + 30 * cos(x / 30),
    'k': lambda x: 30 * exp(-((x / 30) ** 2)) + 100 * _g(x, 150, 30) + 25 * cos(x / 40)
    + 50 * sin((x + 35) / 20),
    'l': lambda x: 30 * cos(x / 15) + 60 * sin(x / 40) + 50 * cos((x - 20) / 10),
}


def _stats(fn):
    # same grid as their published stats (0.1 steps on [0, 300])
    xs = [i / 10 for i in range(X_MIN * 10, X_MAX * 10 + 1)]
    ys = [FUNCTIONS[fn](x) for x in xs]
    i = max(range(len(ys)), key=ys.__getitem__)
    return dict(ymax=ys[i], ymin=min(ys), xmax=xs[i])


STATS = {fn: _stats(fn) for fn in ['t1'] + ROUND_FUNCTIONS}


def value(fn, x):
    """Output shown to the participant (rounded to 2 decimals, as in the original)."""
    return round(FUNCTIONS[fn](float(x)), 2)


def score(fn, final_x):
    s = STATS[fn]
    return 1 - (s['ymax'] - FUNCTIONS[fn](float(final_x))) / (s['ymax'] - s['ymin'])


def practice_curve(n=150):
    """Points of the practice function for the example graph on the instructions page."""
    return [[round(X_MAX * i / n, 1), round(FUNCTIONS[PRACTICE_FUNCTION](X_MAX * i / n), 1)]
            for i in range(n + 1)]
