import collections.abc
import functools
import typing
import weakref

from znslice import utils


class Reset:
    """Reset the cache for the given items."""

    def __init__(self, item):
        self.item = item


class LazySequence(collections.abc.Sequence):
    """Lazy Sequence for 'znslice' lazy features."""

    def __init__(
        self,
        obj: list,
        indices: typing.List[typing.Union[list, int]],
        lazy_single_item: bool,
    ):
        self._obj = obj
        self._indices = indices
        self._lazy_single_item = lazy_single_item

    def __getitem__(self, item):
        cls = type(self)
        indices = utils.item_to_indices(item, self)
        single_item = False
        if isinstance(indices, int):
            single_item = True
            indices = [indices]
        matched_indices = []

        max_index = 0

        for index in self._indices:
            _indices = [
                val for idx, val in enumerate(index) if idx + max_index in indices
            ]
            if single_item and len(_indices) == 1:
                _indices = _indices[0]
            max_index += len(index)
            matched_indices.append(_indices)

        if any(x >= len(self) for x in indices):
            raise IndexError("Index out of range")
        lazy_sequence = cls(self._obj, matched_indices, self._lazy_single_item)
        return (
            lazy_sequence.tolist()[0]
            if (single_item and not self._lazy_single_item)
            else lazy_sequence
        )

    def __repr__(self):
        return f"{type(self).__name__}({self._obj}, {self._indices})"

    def __len__(self):
        return sum(len(x) for x in self._indices)

    def __add__(self, other):
        if not isinstance(other, LazySequence):
            raise TypeError("Can only add LazySequence to LazySequence")
        cls = type(self)
        return cls(
            self._obj + other._obj,
            self._indices + other._indices,
            self._lazy_single_item,
        )

    def tolist(self):
        data = []
        for obj, indices in zip(self._obj, self._indices):
            if isinstance(indices, int):
                indices = [indices]
            data.extend(obj.__getitem__(indices, _resolve=True))

        return data


@utils.optional_kwargs_decorator
def znslice(
    func, cache=True, lazy=False, advanced_slicing=False, lazy_single_item=False
):
    """The 'znslice' decorator.

    Enable advanced slicing, lazy loading and caching for '__getitem__'.

    Parameters
    ----------
    func: callable
        the '__getitem__(self, item)' method of the class to decorate.
    cache: bool, default=True
        Cache the output, so it will be loaded from a cache and not via getitem.
    lazy: bool, default=False
        Return 'LazySequence' instead of the actual data.
    advanced_slicing: bool, default=False
        Use advanced slicing, e.g. 'atoms[[0, 1, 2]]'. This can speed up
        the getitem process but must be supported by the class.
    lazy_single_item: bool, default=False
        If a single item is requested, return the item instead of a 'LazySequence'.
        Typically, loading a single item is fast enough to not need lazy loading.

    Returns
    -------
    callable:
        the decorated '__getitem__(self, item)' method.
    """
    instance_cache = weakref.WeakKeyDictionary()

    @functools.wraps(func)
    def wrapper(self, item, _resolve: bool = False):
        """The wrapper function.

        Parameters
        ----------
        self: object
        item: int, slice, list, tuple, Reset
            The item to get.
        _resolve: bool, default=False
            If True, return the actual data instead of a 'LazySequence'.
        """
        if cache:
            if self not in instance_cache:
                instance_cache[self] = {}
            _cache: dict = instance_cache[self]
        else:
            _cache = {}

        if isinstance(item, Reset):
            if not cache:
                raise ValueError("Cannot reset cache if cache=False")
            item = item.item
            indices = utils.item_to_indices(item, self)
            if isinstance(indices, int):
                _cache.pop(indices, None)
            else:
                for idx in indices:
                    _cache.pop(idx, None)
        else:
            indices = utils.item_to_indices(item, self)

        if lazy and not _resolve:
            if not lazy_single_item and isinstance(indices, int):
                return utils.handle_item([indices], _cache, func, self)[0]
            if isinstance(indices, int):
                indices = [indices]
            if any(x >= len(self) for x in indices):
                raise IndexError("Index out of range")
            return LazySequence([self], [indices], lazy_single_item)
        if isinstance(indices, int):
            return utils.handle_item([indices], _cache, func, self)[0]
        return utils.handle_item(indices, _cache, func, self, advanced_slicing)

    return wrapper
