"""
Module containing low-level math utilities used by iter8
"""

# core python dependencies
import math
from random import random

# round a sequence of weights into a sequence of integer weights so that they sum up to Math.floor(total)
# further, rounded values equal the original values in expectation
# assumption: all inputs are non-negative


def gen_round(weights, total):
    """Given float weights, round them to int weights so that they sum up to a given value

    Args:
        weights (Sequence[float]): A sequence of float weights
        total (float): Returned values will sum up to Math.floor(total)

    Yields:
        int: The next weight
    """
    # initialize the generator. We will always work with math.floor(total)
    total = math.floor(total)

    #  randomized rounding of float 'a' to its ceiling or floor
    def fix(a): return math.ceil(a) if random() < a - \
        math.floor(a) else math.floor(a)

    def normalize(weights):
        """Maintain the invariate that weights sum up to 'total'

        Args:
            weights (Sequence[float]): A sequence of float weights

        Returns:
            a sequence (Sequence[int]): A sequence of ints summing up to total
        """
        if sum(weights) == 0:
            # weights summing up now to a value > 0
            weights = [1 for x in weights]
        weightSum = sum(weights)
        return [x*total / weightSum for x in weights]

    # yield rounded values iteratively and update weights and total after yielding
    while len(weights):
        fixed = fix(normalize(weights)[0])
        yield fixed
        weights, total = weights[1:], total - fixed
