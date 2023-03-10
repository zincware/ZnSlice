"""ZnSlice utils module."""
import functools


def get_matched_indices(selected, available, single_item) -> list:
    """Get the indices selected from the available indices."""
    if not check_sorted(selected):
        raise ValueError("ZnSlice currently only supports sorted indices.")

    matched_indices = []

    max_index = 0

    for index in available:
        _indices = [val for idx, val in enumerate(index) if idx + max_index in selected]
        if single_item and len(_indices) == 1:
            _indices = _indices[0]
        max_index += len(index)
        matched_indices.append(_indices)

    return matched_indices


def check_sorted(data: list) -> bool:
    """Check if data is ordered."""
    return sorted(data) == data


def optional_kwargs_decorator(fn):
    """Decorator to allow optional kwargs."""

    @functools.wraps(fn)
    def wrapped_decorator(*args, **kwargs):
        """The wrapped decorator."""
        if len(args) == 1 and callable(args[0]):
            return fn(args[0])

        @functools.wraps(fn)
        def real_decorator(decoratee):
            """The real decorator."""
            return fn(decoratee, *args, **kwargs)

        return real_decorator

    return wrapped_decorator


@functools.singledispatch
def item_to_indices(item, self):
    """Convert item to indices."""
    raise ValueError(f"Cannot handle item of type {type(item)}")


@item_to_indices.register
def _(item: int, self) -> int:
    """Keep int as is."""
    if item < 0:
        return len(self) + item  # len + (- idx)
    return item


@item_to_indices.register
def _(item: list, self) -> list:
    """Keep list as is."""
    return [item_to_indices(x, self) for x in item]


@item_to_indices.register
def _(item: tuple, self) -> list:
    """Convert tuple to list."""
    return item_to_indices(list(item), self)


@item_to_indices.register
def _(item: slice, self) -> list:
    """Convert slice to list using the length of the item."""
    return list(range(len(self)))[item]


def handle_item(indices, cache, func, self, advanced_slicing=False) -> list:
    """Handle item.

    TODO ...
    """
    if advanced_slicing:
        if new_indices := [x for x in indices if x not in cache]:
            # only if len(new_indices) > 0
            data = func(self, new_indices)
            for idx, val in zip(new_indices, data):
                cache[idx] = val
        return [cache[x] for x in indices]

    for index in indices:
        if index not in cache:
            cache[index] = func(self, index)
    return [cache[index] for index in indices]
