"""The main znslice module."""
import collections.abc
import functools
import logging
import typing
import weakref

from znslice import utils

log = logging.getLogger(__name__)


class Reset:
    """Reset the cache for the given items."""

    def __init__(self, item):
        """Initialize the Reset object."""
        self.item = item


class LazySequence(collections.abc.Sequence):
    """Lazy Sequence for 'znslice' lazy features."""

    def __init__(
        self,
        obj: list,
        indices: typing.List[typing.Union[list, int]],
        lazy_single_item: bool = False,
    ):
        """Initialize the LazySequence.

        Todo: ...
        """
        self._obj = obj
        self._indices = indices
        self._lazy_single_item = lazy_single_item

    @classmethod
    def _get_new_instance(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @functools.singledispatchmethod
    @classmethod
    def from_obj(cls, obj, /, indices: list = None, lazy_single_item=False):
        """Create a LazySequence from a given object.

        Parameters
        ----------
        cls: LazySequence
            the LazySequence class.
        obj: list
            list to create a LazySequence from.
        indices: list, optional
            list of indices to gather from obj. If None, all items in obj are used.
        lazy_single_item: bool, optional
            currently unused.

        Returns
        -------
        LazySequence:
            LazySequence created from the list.
        """
        if isinstance(obj, cls):
            return obj if indices is None else obj[indices]
        raise TypeError(f"Can not create LazySequence from {type(obj)}")

    @from_obj.register(list)
    @classmethod
    def _(cls, obj, /, indices: list = None, lazy_single_item=False):
        indices = indices or list(range(len(obj)))
        return cls([obj], [indices], lazy_single_item=False)

    def __getitem__(self, item):
        """Get item from LazySequence.

        Todo ...
        """
        if item == -1:
            # special case, return last entry
            return self[len(self) - 1]

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
        lazy_sequence = self._get_new_instance(
            self._obj, matched_indices, self._lazy_single_item
        )
        return (
            lazy_sequence.tolist()[0]
            if (single_item and not self._lazy_single_item)
            else lazy_sequence
        )

    def __repr__(self) -> str:
        """Return the representation of the LazySequence."""
        return f"{type(self).__name__}({self._obj}, {self._indices})"

    def __len__(self) -> int:
        """Return the length of the LazySequence."""
        return sum(len(x) for x in self._indices)

    def __add__(self, other):
        """Add two LazySequences."""
        if isinstance(other, LazySequence):
            return self._get_new_instance(
                self._obj + other._obj,
                self._indices + other._indices,
                self._lazy_single_item,
            )
        elif isinstance(other, list):
            log.warning("Converting LazySequence to list")
            return self.tolist() + other
        else:
            raise TypeError("Can only add LazySequence to {LazySequence, list}")

    def tolist(self) -> list:
        """Return the LazySequence as a non-lazy list."""
        data = []
        for obj, indices in zip(self._obj, self._indices):
            if isinstance(indices, int):
                indices = [indices]
            try:
                data.extend(obj.__getitem__(indices, _resolve=True))
            except TypeError:
                data.extend(obj[x] for x in indices)

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
            the class instance.
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
