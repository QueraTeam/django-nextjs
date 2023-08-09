import typing

Key = typing.TypeVar("Key")
Value = typing.TypeVar("Value")


def filter_mapping_obj(
    mapping_obj: typing.Mapping[Key, Value], *, selected_keys: typing.Iterable
) -> typing.Dict[Key, Value]:
    """
    Selects the items in a mapping object (dict, etc.)
    """

    return {key: mapping_obj[key] for key in selected_keys if key in mapping_obj}
