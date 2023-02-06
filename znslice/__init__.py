"""The znslice package."""
import importlib.metadata

from znslice import utils
from znslice.znslice import LazySequence, Reset, znslice

__all__ = ["znslice", "LazySequence", "Reset", "utils"]
__version__ = importlib.metadata.version("znslice")
