import pytest

import znslice


def test_LazySequenceInit():
    lst = znslice.LazySequence.from_obj([1, 2, 3])
    assert lst._obj == [[1, 2, 3]]
    assert lst._indices == [[0, 1, 2]]
    assert lst[:].tolist() == [1, 2, 3]
    assert lst[0] == 1
    assert lst[[0, 2]].tolist() == [1, 3]
    assert len(lst) == 3


def test_LazySequence_empty_Init():
    lst = znslice.LazySequence.from_obj([])
    assert len(lst) == 0
    lst += znslice.LazySequence.from_obj([1, 2, 3])
    assert len(lst) == 3
    assert lst[:].tolist() == [1, 2, 3]


def test_LazySequence_indices():
    lst = znslice.LazySequence.from_obj([1, 2, 3], indices=[0, 2])
    assert len(lst) == 2
    assert lst[:].tolist() == [1, 3]
    assert lst[0] == 1
    assert lst[[0, 1]].tolist() == [1, 3]
    assert lst[1] == 3

    lst += znslice.LazySequence.from_obj([4, 5, 6], indices=[1, 2])
    assert len(lst) == 4
    assert lst[:].tolist() == [1, 3, 5, 6]
    assert lst[0] == 1
    assert lst[[0, 2]].tolist() == [1, 5]


def test_add_LazySequence_list():
    lst = znslice.LazySequence.from_obj([1, 2, 3], indices=[0, 2])
    lst += [4, 5, 6]

    assert len(lst) == 5
    assert lst[:] == [1, 3, 4, 5, 6]
    assert isinstance(lst, list)


def test_from_LazySequence():
    lst = znslice.LazySequence.from_obj(list(range(10)), indices=[0, 2, 4, 6, 8])
    lst2 = znslice.LazySequence.from_obj(lst, indices=[0, 2, 4])
    assert lst2[:].tolist() == [0, 4, 8]
    assert lst2[0] == 0
    assert lst[[0, 2]].tolist() == [0, 4]


def test_from_LazySequence_err():
    with pytest.raises(TypeError):
        znslice.LazySequence.from_obj("Lorem Ipsum")
