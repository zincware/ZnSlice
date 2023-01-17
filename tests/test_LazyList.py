import collections.abc

import znslice


class DatabaseMock:
    def __init__(self, maximum: int = 100):
        self.maximum = maximum

    def __getitem__(self, item):
        if isinstance(item, int):
            if item > self.maximum:
                raise IndexError
            return item
        raise TypeError(
            f"Index of type {type(item)} not supported. Only int supported."
        )

    def __len__(self):
        return self.maximum


class LazyList(collections.abc.Sequence):
    """Lazy List for ASE Atoms Objects"""

    def __init__(self, obj=None, indices=None):
        self._obj = obj
        self._indices = (
            znslice.utils.item_to_indices(indices, range(len(obj))) if indices else None
        )

    @znslice.znslice(lazy=True)
    def __getitem__(self, item: int):
        if self._indices is None:
            return self._obj[item]
        return self._obj[self._indices[item]]

    def __len__(self):
        if self._indices is None:
            return len(self._obj)
        return len(self._indices)


def test_LazyList():
    lsta = LazyList(DatabaseMock(), indices=[1, 4, 7])
    assert lsta[0] == 1
    assert isinstance(lsta[:2], znslice.LazySequence)

    assert lsta[[0, 1, 2]].tolist() == [1, 4, 7]

    lstb = LazyList(DatabaseMock(), indices=[9, 11, 26])
    assert lstb[[0, 1, 2]].tolist() == [9, 11, 26]

    lstc = LazyList(DatabaseMock(), indices=slice(None, None, 3))
    assert lstc[:3].tolist() == [0, 3, 6]
