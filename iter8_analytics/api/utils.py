"""
Module containing utilities used by iter8
"""

# core python dependencies
import math
from random import random
from enum import Enum
from typing import Sequence
from decimal import Decimal
import logging

# external dependencies
from kubernetes.utils.quantity import parse_quantity

logger = logging.getLogger('iter8_analytics')

def convert_to_float(value):
    """
    Convert an input value which could be a quantity to float.
    """
    if value is None:
        return None

    if isinstance(value, float):
        return value

    return float(parse_quantity(value))

def convert_to_quantity(value):
    """
    Convert an input value which could be a float to quantity.
    """
    if value is None:
        return None

    if isinstance(value, int):
        return int

    return str(Decimal(value))

def gen_round(weights, total):
    """Given float weights, round them to int weights so that they sum up to a given value.
    Rounded values equal the original values in expectation.
    All inputs are assumed to be non-negative.

    Args:
        weights (Sequence[float]): A sequence of float weights
        total (float): Returned values will sum up to Math.floor(total)

    Yields:
        int: The next weight
    """
    # initialize the generator. We will always work with math.floor(total)
    total = math.floor(total)

    def fix(value):
        """
        Randomized round of float 'value' to its ceiling or floor
        """
        return math.ceil(value) if random() < value - math.floor(value) else math.floor(value)

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
        weight_sum = sum(weights)
        return [x*total / weight_sum for x in weights]

    # yield rounded values iteratively and update weights and total after yielding
    while len(weights) > 0:
        fixed = fix(normalize(weights)[0])
        yield fixed
        weights, total = weights[1:], total - fixed

class MessageLevel(str, Enum):
    """
    Preferred directions for a metric
    """
    error = "Error"
    info = "Info"
    warning = "Warning"

class Message:
    """Message fragment shipped by iter8-analytics as part of its responses.

    Attributes:
        level (MessageLevel): Severity of this message.
        msg (str): Human readable message string.
    """

    def __init__(self, level, msg):
        """
        Args:
            level (MessageLevel): Severity of this message.
            msg (str): Human readable message string.
        """

        self.level = level
        self.msg = msg

    @staticmethod
    def join_messages(msgs):
        """Group messages by level and join them.

        Args:
            msgs (Sequence[Message]): a sequence of messages
        """
        errors = filter(lambda x: x.level == MessageLevel.error, msgs)
        error_message = "Error: " + ', '.join(map(lambda x: x.msg, errors))
        warnings = filter(lambda x: x.level == MessageLevel.warning, msgs)
        warning_message = "Warning: " + ', '.join(map(lambda x: x.msg, warnings))
        info = filter(lambda x: x.level == MessageLevel.info, msgs)
        info_message = "Info: " + ', '.join(map(lambda x: x.msg, info))
        return '; '.join([error_message, warning_message, info_message])
