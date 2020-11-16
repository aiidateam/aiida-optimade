from typing import List, Union

__all__ = ("hex_to_floats",)


def check_floating_round_errors(
    some_list: List[Union[List[float], float]]
) -> List[Union[List[float], float]]:
    """Check whether there are some float rounding errors
    (check only for close to zero numbers)

    :param some_list: Must be a list of either lists or float values
    :type some_list: list
    """
    might_as_well_be_zero = (
        1e-8  # This is for Å, so 1e-8 Å can by all means be considered 0 Å
    )
    res = []

    for item in some_list:
        if isinstance(item, list):
            res.append(check_floating_round_errors(item))
        else:
            if abs(item) < might_as_well_be_zero:
                item = 0.0
            res.append(item)
    return res


def floats_to_hex(
    some_list: List[Union[List[float], float]]
) -> List[Union[List[str], str]]:
    """Convert floats embedded in lists to hex strings (for storing "precise" floats)

    :param some_list: Must be a list of either lists or float values
    :type some_list: list
    """
    res = []
    for item in some_list:
        if isinstance(item, list):
            res.append(floats_to_hex(item))
        else:
            if isinstance(item, float):
                item = item.hex()
            if not isinstance(item, str):
                raise TypeError(
                    "Wrong type passed to floats_to_hex method, must be a "
                    "list of either a list of floats or float values. "
                    f"Item: {item!r}. Type: {type(item)}."
                )
            res.append(item)
    return res


def hex_to_floats(
    some_list: List[Union[List[str], str]]
) -> List[Union[List[float], float]]:
    """Convert hex strings embedded in lists (back) to floats

    :param some_list: Must be a list of either lists or string values
    :type some_list: list
    """
    res = []

    for item in some_list:
        if isinstance(item, list):
            res.append(hex_to_floats(item))
        else:
            if isinstance(item, str):
                try:
                    item = float.fromhex(item)
                except ValueError as exc:
                    raise ValueError(
                        f"Could not turn item ({item}) into float from hex. "
                        f"Original exception: {exc!r}"
                    ) from exc
            if not isinstance(item, float):
                raise TypeError(
                    "Wrong type passed to hex_to_floats method, must be a "
                    "list of either a list of strings or string values. "
                    f"Item: {item!r}. Type: {type(item)}."
                )
            res.append(item)
    return res
