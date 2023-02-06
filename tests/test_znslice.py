import collections.abc

import pytest

import znslice


def test_version():
    """Test 'ZnTrack' version."""
    assert znslice.__version__ == "0.1.2"


class CacheList(collections.abc.Sequence):
    def __init__(self, data):
        self.data = data

    @znslice.znslice
    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


class CacheListAdvancedSlicing(collections.abc.Sequence):
    def __init__(self, data):
        self.data = data

    @znslice.znslice(advanced_slicing=True)
    def __getitem__(self, item):
        if isinstance(item, int):
            return self.data[item]
        return [self.data[x] for x in item]

    def __len__(self):
        return len(self.data)


class NoCacheList(collections.abc.Sequence):
    def __init__(self, data):
        self.data = data

    @znslice.znslice(cache=False)
    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


class LazyCacheList(collections.abc.Sequence):
    def __init__(self, data):
        self.data = data

    @znslice.znslice(cache=True, lazy=True)
    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


class LazyCacheListLazySingle(collections.abc.Sequence):
    def __init__(self, data):
        self.data = data

    @znslice.znslice(cache=True, lazy=True, lazy_single_item=True)
    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


@pytest.mark.parametrize("cls", [CacheList, CacheListAdvancedSlicing])
@pytest.mark.parametrize(
    ["item", "expected"],
    [
        (5, 5),
        ([5], [5]),
        (slice(3, 7), [3, 4, 5, 6]),
        (slice(None, 5), [0, 1, 2, 3, 4]),
        (slice(5, None), [5, 6, 7, 8, 9]),
        (slice(2, 8, 2), [2, 4, 6]),
        ([1, 3, 5], [1, 3, 5]),
    ],
)
def test_CacheList(item, expected, cls):
    lst = cls(list(range(10)))
    assert len(lst) == 10
    assert lst[item] == expected

    # the values are cached, so changing data doesn't have an affect
    lst.data = list(range(10, 20))
    assert len(lst) == 10
    assert lst[item] == expected
    # now with a reset
    if isinstance(expected, int):
        assert lst[znslice.Reset(item)] == expected + 10
    else:
        assert lst[znslice.Reset(item)] == [x + 10 for x in expected]

    # create a second instance to test WeakKeyDict
    other_lst = cls(list(range(50, 60)))
    assert len(other_lst) == 10
    if isinstance(expected, int):
        assert other_lst[item] == expected + 50
    else:
        assert other_lst[item] == [x + 50 for x in expected]

    # now with a reset
    other_lst.data = list(range(100, 110))
    assert len(other_lst) == 10
    if isinstance(expected, int):
        assert other_lst[item] == expected + 50
        assert other_lst[znslice.Reset(item)] == expected + 100
    else:
        assert other_lst[item] == [x + 50 for x in expected]
        assert other_lst[znslice.Reset(item)] == [x + 100 for x in expected]


@pytest.mark.parametrize(
    ["item", "expected"],
    [
        (5, 5),
        ([5], [5]),
        (slice(3, 7), [3, 4, 5, 6]),
        (slice(None, 5), [0, 1, 2, 3, 4]),
        (slice(5, None), [5, 6, 7, 8, 9]),
        (slice(2, 8, 2), [2, 4, 6]),
        ([1, 3, 5], [1, 3, 5]),
    ],
)
def test_NoCacheList(item, expected):
    lst = NoCacheList(list(range(10)))
    assert len(lst) == 10
    assert lst[item] == expected

    # the values are not cached, so changing data does have an affect
    lst.data = list(range(10, 20))
    if isinstance(expected, int):
        assert lst[item] == expected + 10
    else:
        assert lst[item] == [x + 10 for x in expected]

    with pytest.raises(ValueError):
        _ = lst[znslice.Reset(item)]


@pytest.mark.parametrize(
    ["item", "expected"],
    [
        (5, 5),
        ([5], [5]),
        (slice(3, 7), [3, 4, 5, 6]),
        (slice(None, 5), [0, 1, 2, 3, 4]),
        (slice(5, None), [5, 6, 7, 8, 9]),
        (slice(2, 8, 2), [2, 4, 6]),
        ([1, 3, 5], [1, 3, 5]),
    ],
)
def test_LazyCacheList(item, expected):
    lst = LazyCacheList(list(range(10)))
    assert len(lst) == 10
    if isinstance(item, int):
        assert lst[item] == expected
    else:
        assert lst[item].tolist() == expected

    # the values are cached, so changing data doesn't have an affect
    lst.data = list(range(10, 20))
    assert len(lst) == 10
    if isinstance(item, int):
        assert lst[item] == expected
    else:
        assert lst[item].tolist() == expected
    # now with a reset
    if isinstance(expected, int):
        assert lst[znslice.Reset(item)] == expected + 10
    else:
        assert lst[znslice.Reset(item)].tolist() == [x + 10 for x in expected]

    # create a second instance to test WeakKeyDict
    other_lst = LazyCacheList(list(range(50, 60)))
    assert len(other_lst) == 10
    if isinstance(expected, int):
        assert other_lst[item] == expected + 50
    else:
        assert other_lst[item].tolist() == [x + 50 for x in expected]

    # now with a reset
    other_lst.data = list(range(100, 110))
    assert len(other_lst) == 10
    if isinstance(expected, int):
        assert other_lst[item] == expected + 50
        assert other_lst[znslice.Reset(item)] == expected + 100
    else:
        assert other_lst[item].tolist() == [x + 50 for x in expected]
        assert other_lst[znslice.Reset(item)].tolist() == [x + 100 for x in expected]


def test_LazyCacheList_nested():
    lst = LazyCacheList(list(range(10)))
    assert len(lst) == 10

    assert lst[0] == 0
    assert lst[[0, 1]].tolist() == [0, 1]

    partial_lst = lst[::2]
    assert len(partial_lst) == 5
    assert partial_lst[:].tolist() == [0, 2, 4, 6, 8]
    assert partial_lst[1] == 2
    assert partial_lst[[1]].tolist() == [2]

    partial_lst_2 = partial_lst[::2]
    assert len(partial_lst_2) == 3
    assert partial_lst_2[:].tolist() == [0, 4, 8]

    # with cache everything remains
    lst.data = list(range(10, 20))
    assert len(lst) == 10
    assert len(partial_lst) == 5
    assert partial_lst[:].tolist() == [0, 2, 4, 6, 8]
    assert len(partial_lst_2) == 3
    assert partial_lst_2[:].tolist() == [0, 4, 8]

    # reset the lst
    assert lst[znslice.Reset(slice(None))].tolist() == list(range(10, 20))
    # they all reference the original list, so they also change
    assert len(lst) == 10
    assert len(partial_lst) == 5
    assert partial_lst[:].tolist() == [10, 12, 14, 16, 18]
    assert len(partial_lst_2) == 3
    assert partial_lst_2[:].tolist() == [10, 14, 18]


def test_LazyCacheList_addition():
    lsta = LazyCacheList(list(range(10)))
    lstb = LazyCacheList(list(range(10, 20)))
    lstc = lsta[:] + lstb[:]
    assert len(lstc) == 20
    assert len(lstc._obj) == 2
    assert len(lstc._indices) == 2
    assert lstc[:].tolist() == list(range(20))
    assert lstc[::2].tolist() == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    assert lstc[[7]].tolist() == [7]
    assert lstc[[16]].tolist() == [16]
    assert lstc[7] == 7
    assert lstc[16] == 16
    assert lstc[8:12].tolist() == [8, 9, 10, 11]


def test_LazyCacheList_addition_sliced():
    lsta = LazyCacheList(list(range(10)))
    lstb = LazyCacheList(list(range(10, 20)))
    lstc = lsta[::2] + lstb[::2]
    assert len(lstc) == 10
    assert len(lstc._obj) == 2
    assert len(lstc._indices) == 2
    assert lstc[:].tolist() == list(range(0, 20, 2))
    assert lstc[::2].tolist() == [0, 4, 8, 12, 16]
    assert lstc[[9]].tolist() == [18]
    assert lstc[9] == 18

    assert list(lsta) == list(range(10))
    assert list(lstc) == list(range(0, 20, 2))
    with pytest.raises(IndexError):
        _ = lstc[10]


def test_LazyCacheList_addition_error():
    lst = LazyCacheList(list(range(10)))
    with pytest.raises(TypeError):
        lst[:] + (1, 2, 3)


def test_LazyCacheListLazySingle():
    lsta = LazyCacheListLazySingle(list(range(10)))
    lstb = LazyCacheListLazySingle(list(range(10, 20)))
    lstc = lsta[::2] + lstb[::2]
    assert len(lstc) == 10
    assert len(lstc._obj) == 2
    assert len(lstc._indices) == 2
    assert lstc._indices == [[0, 2, 4, 6, 8], [0, 2, 4, 6, 8]]
    assert lstc[:].tolist() == list(range(0, 20, 2))
    assert lstc[::2].tolist() == [0, 4, 8, 12, 16]
    assert lstc[[9]].tolist() == [18]
    assert lstc[9].tolist() == [18]

    assert list(lsta)[8].tolist() == [8]
    assert list(lstc)[8].tolist() == [16]
    with pytest.raises(IndexError):
        _ = lstc[10]


def test_iter_LazyCacheList():
    lst = LazyCacheList(list(range(10)))
    for i, v in enumerate(lst):
        assert i == v


def test_add_lists():
    lst = LazyCacheList(list(range(10)))[:]
    assert lst + [1, 2, 3] == list(range(10)) + [1, 2, 3]
