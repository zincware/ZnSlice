[![PyPI version](https://badge.fury.io/py/znslice.svg)](https://badge.fury.io/py/znslice)
[![Coverage Status](https://coveralls.io/repos/github/zincware/ZnSlice/badge.svg?branch=main)](https://coveralls.io/github/zincware/ZnSlice?branch=main)
[![zincware](https://img.shields.io/badge/Powered%20by-zincware-darkcyan)](https://github.com/zincware)
# ZnSlice

A lightweight library  (without external dependencies) for:
- advanced slicing.
- cache `__getitem__(self, item)`
- lazy load `__getitem__(self, item)`

# Installation

```bash
pip install znslice
```

# Usage

## Advanced Slicing and Cache
Convert List to `znslice.LazySequence` to allow advanced slicing.
```python
import znslice

lst = znslice.LazySequence.from_obj([1, 2, 3], indices=[0, 2])
print(lst[[0, 1]].tolist())  # [1, 3]
```


```python
import znslice
import collections.abc

class MapList(collections.abc.Sequence):
    def __init__(self, data, func):
        self.data = data
        self.func = func
    
    @znslice.znslice
    def __getitem__(self, item: int):
        print(f"Loading item = {item}")
        return self.func(self.data[item])
    
    def __len__(self):
        return len(self.data)

data = MapList([0, 1, 2, 3, 4], lambda x: x ** 2)

assert data[0] == 0
assert data[[1, 2, 3]] == [1, 4, 9]
# calling data[:] will now only compute data[4] and load the remaining data from cache
assert data[:] == [0, 1, 4, 9, 16]
```

## Lazy Database Loading

You can use `znslice` to lazy load data from a database. This is useful if you have a large database and only want to load a small subset of the data.

In the following we will use the `ase` package to generate `Atoms` objects stored in a database and load them lazily.

```python 
import ase.io
import ase.db
import znslice
import tqdm
import random

# create a database
with ase.db.connect("data.db", append=False) as db:
    for _ in range(10):
        atoms = ase.Atoms('CO', positions=[(0, 0, 0), (0, 0, random.random())])
        db.write(atoms, group="data")
        
# load the database lazily
class ReadASEDB:
    def __init__(self, file):
        self.file = file
    
    @znslice.znslice(
        advanced_slicing=True, # this getitem supports advanced slicingn
        lazy=True # we want to lazy load the data
    )
    def __getitem__(self, item):
        data = []
        with ase.db.connect(self.file) as database:
            if isinstance(item, int):
                print(f"get {item = }")
                return database[item + 1].toatoms()
            for idx in tqdm.tqdm(item):
                data.append(database[idx + 1].toatoms())
        return data
            
    def __len__(self):
        with ase.db.connect(self.file) as db:
            return len(db)

db = ReadASEDB("data.db")

data = db[::2] # LazySequence([<__main__.ReadASEDB>], [[0, 2, 4, 6, 8]])
data.tolist() # list[ase.Atoms] 

# supports addition, advanced slicing, etc.
data = db[::2] + db[1::2]
```
