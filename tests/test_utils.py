import pytest

import znslice


def test_item_to_indices():

    lst = list(range(10))

    assert znslice.utils.item_to_indices(1, lst) == 1
    assert znslice.utils.item_to_indices(slice(4, 6), lst) == [4, 5]
    assert znslice.utils.item_to_indices([1, 2, 3], lst) == [1, 2, 3]
    assert znslice.utils.item_to_indices((1, 2, 3), lst) == [1, 2, 3]

    with pytest.raises(ValueError):
        znslice.utils.item_to_indices("data", lst)
