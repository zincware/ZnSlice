import numpy as np
import numpy.testing as npt
import pytest

import znslice


def test_item_to_indices():
    lst = list(range(10))

    assert znslice.utils.item_to_indices(1, lst) == 1
    assert znslice.utils.item_to_indices(slice(4, 6), lst) == [4, 5]
    assert znslice.utils.item_to_indices([1, 2, 3], lst) == [1, 2, 3]
    assert znslice.utils.item_to_indices((1, 2, 3), lst) == [1, 2, 3]
    assert znslice.utils.item_to_indices(-1, lst) == 9
    assert znslice.utils.item_to_indices([0, -1], lst) == [0, 9]
    assert znslice.utils.item_to_indices(-4, lst) == 6
    assert znslice.utils.item_to_indices([-2, -3, 5], lst) == [8, 7, 5]
    assert znslice.utils.item_to_indices((-2, -3, 5), lst) == [8, 7, 5]
    assert znslice.utils.item_to_indices([0, 2], lst) == [0, 2]
    assert znslice.utils.item_to_indices([2, 0], lst) == [2, 0]

    with pytest.raises(ValueError):
        znslice.utils.item_to_indices("data", lst)


@pytest.mark.parametrize(
    "index",
    (1, 0, -1, -4, 4, [1, 2, 3], [-1, -5, -2], [2, -3, 1], [-3, 2, 1], [1, 2, -3]),
)
def test_item_to_indices_np(index):
    data = np.random.randn(10)
    npt.assert_array_equal(
        data[znslice.utils.item_to_indices(index, data)], data[index]
    )


def test_get_matched_indices():
    assert znslice.utils.get_matched_indices(
        selected=[0], available=[[0]], single_item=False
    ) == [[0]]
    assert znslice.utils.get_matched_indices(
        selected=[0], available=[[0]], single_item=True
    ) == [0]
    assert znslice.utils.get_matched_indices(
        selected=[2], available=[[0, 1], [10, 11]], single_item=False
    ) == [[], [10]]
    assert znslice.utils.get_matched_indices(
        selected=[2], available=[[0, 1], [10, 11]], single_item=True
    ) == [[], 10]
    # TODO: check if single item has to work like this
    assert znslice.utils.get_matched_indices(
        selected=[0, 2], available=[[0, 1], [10, 11]], single_item=True
    ) == [0, 10]
    assert znslice.utils.get_matched_indices(
        selected=[0, 2], available=[[0, 1], [10, 11]], single_item=False
    ) == [[0], [10]]

    with pytest.raises(ValueError):
        # TODO this should be possible in the future
        assert znslice.utils.get_matched_indices(
            selected=[2, 0], available=[[0, 1], [10, 11]], single_item=False
        ) == [[0], [10]]


def test_check_sorted():
    assert znslice.utils.check_sorted([1, 2, 3])
    assert not znslice.utils.check_sorted([2, 5, 1])
    assert znslice.utils.check_sorted([-3, -2, -1])
    assert not znslice.utils.check_sorted([-1, -2, -3])
