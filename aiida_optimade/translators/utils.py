from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:  # pragma: no cover
    from typing import TypeVar

    NonListType = TypeVar("NonListType", float, str)
    RecursiveList = list[Union["RecursiveList[NonListType]", NonListType]]


def check_floating_round_errors(
    some_list: "RecursiveList[float]",
) -> "RecursiveList[float]":
    """Check whether there are some float rounding errors
    (check only for close to zero numbers)

    :param some_list: Must be a list of either lists or float values
    :type some_list: list
    """
    might_as_well_be_zero = (
        1e-8  # This is for Å, so 1e-8 Å can by all means be considered 0 Å
    )
    res: "RecursiveList[float]" = []

    for item in some_list:
        if isinstance(item, list):
            res.append(check_floating_round_errors(item))
        elif abs(item) < might_as_well_be_zero:
            res.append(0.0)
        else:
            res.append(item)

    return res


def floats_to_hex(some_list: "RecursiveList[float]") -> "RecursiveList[str]":
    """Convert floats embedded in lists to hex strings (for storing "precise" floats)

    :param some_list: Must be a list of either lists or float values
    :type some_list: list
    """
    res: "RecursiveList[str]" = []

    for item in some_list:
        if isinstance(item, list):
            res.append(floats_to_hex(item))
        else:
            item_updated = item
            if isinstance(item, float):
                item_updated = item.hex()  # type: ignore[assignment]
            if not isinstance(item_updated, str):
                raise TypeError(
                    "Wrong type passed to floats_to_hex method, must be a "
                    "list of either a list of floats or float values. "
                    f"Item: {item!r}. Type: {type(item)}."
                )
            res.append(item_updated)

    return res


def hex_to_floats(some_list: "RecursiveList[str]") -> "RecursiveList[float]":
    """Convert hex strings embedded in lists (back) to floats

    :param some_list: Must be a list of either lists or string values
    :type some_list: list
    """
    res: "RecursiveList[float]" = []

    for item in some_list:
        if isinstance(item, list):
            res.append(hex_to_floats(item))
        else:
            item_updated = item
            if isinstance(item, str):
                try:
                    item_updated = float.fromhex(item)  # type: ignore[assignment]
                except ValueError as exc:
                    raise ValueError(
                        f"Could not turn item ({item}) into float from hex. "
                        f"Original exception: {exc!r}"
                    ) from exc
            if not isinstance(item_updated, float):
                raise TypeError(
                    "Wrong type passed to hex_to_floats method, must be a "
                    "list of either a list of strings or string values. "
                    f"Item: {item!r}. Type: {type(item)}."
                )
            res.append(item_updated)

    return res
