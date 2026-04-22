"""
lists.py

Handles custom list data structures
"""

import random
from typing import Any, List as PyList, Union, TYPE_CHECKING

from ..operators import toint

if TYPE_CHECKING:
    from .target import Target

__all__ = ['List', 'StaticList']


class List:
    """
    Emulates the correct list behavior

    Attributes:
        list: The internal list
    """

    __slots__ = ('list',)

    def __init__(self, values: PyList[Any]):
        self.list = values

    def __getitem__(self, key: Union[int, str]) -> Any:
        if isinstance(key, str):
            return self.get(key)

        index = int(key) - 1
        if 0 <= index < len(self.list):
            return self.list[index]
        return ""

    def get(self, key: Union[int, str]) -> Any:
        """
        Gets an item, supporting legacy indices
        (first, last, random)
        """
        if key == 'first':
            return self.list[0] if self.list else ""
        if key == 'last':
            return self.list[-1] if self.list else ""
        if key == 'random':
            return random.choice(self.list) if self.list else ""
        return self.__getitem__(toint(key))

    def __setitem__(self, key: Union[int, str], value: Any):
        index = toint(key) - 1
        if 0 <= index < len(self.list):
            self.list[index] = value

    def set(self, key: Union[int, str], item: Any):
        """
        Sets an item, supporting legacy indices
        (first, last, random)
        """
        if key == 'first':
            self.__setitem__(1, item)
        elif key == 'last':
            self.__setitem__(len(self.list), item)
        elif key == 'random':
            if self.list:
                self.__setitem__(random.randint(1, len(self.list)), item)
        else:
            self.__setitem__(toint(key), item)

    def append(self, value: Any):
        """Add an item to list"""
        self.list.append(value)

    def insert(self, key: int, value: Any):
        """Insert an item in list"""
        index = key - 1
        if 0 <= index <= len(self.list):
            self.list.insert(index, value)

    def insert2(self, key: Union[int, str], item: Any):
        """
        Inserts an item, supporting legacy indices
        (first, last random)
        """
        if key == 'first':
            self.insert(1, item)
        elif key == 'last':
            self.append(item)
        elif key == 'random':
            self.insert(random.randint(1, len(self.list) + 1), item)
        else:
            self.insert(toint(key), item)

    def delete(self, key: int):
        """Remove an item from list"""
        index = key - 1
        if 0 <= index < len(self.list):
            del self.list[index]

    def delete2(self, key: Union[int, str]):
        """
        Deletes an item, supporting legacy indices
        (first, last, random, all)
        """
        if key == 'all':
            self.delete_all()
        elif key == 'first':
            self.delete(1)
        elif key == 'last':
            self.delete(len(self.list))
        elif key == 'random':
            if self.list:
                self.delete(random.randint(1, len(self.list)))
        else:
            self.delete(toint(key))

    def delete_all(self):
        """Deletes all items in list"""
        self.list = []

    def __contains__(self, item: Any) -> bool:
        search_item = search_str(item)
        return any(search_item == search_str(value) for value in self.list)

    def join(self) -> str:
        """Joins the list"""
        if all(len(search_str(item)) == 1 for item in self.list):
            return ''.join(map(str, self.list))
        return ' '.join(map(str, self.list))

    def __len__(self) -> int:
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    # TODO Variable/list reporters
    def show(self):
        """Print list"""
        print(self.list)

    def hide(self):
        """Do nothing"""

    def index(self, item: Any) -> int:
        """Gets the position of item in list"""
        search_item = search_str(item)
        for i, value in enumerate(self.list):
            if search_item == search_str(value):
                return i + 1
        return 0

    def copy(self) -> 'List':
        """Return a copy of this List"""
        return self.__class__(self.list.copy())


class StaticList(List):
    """
    A list that doesn't change

    Attributes:
        list: Inherited from List, the internal list

        dict: Used to test if an item is contained in the list and to
            determine the index of items in the list.
    """

    __slots__ = ('dict',)

    def __init__(self, values: PyList[Any]):  # pylint: disable=super-init-not-called
        self.list = tuple(values)

        self.dict = {}
        for i, item in enumerate(values):
            self.dict.setdefault(search_str(item), i + 1)

    def index(self, item: Any) -> int:
        """Gets the position of item in list"""
        return self.dict.get(search_str(item), 0)

    def __contains__(self, item: Any) -> bool:
        return search_str(item) in self.dict

    def copy(self) -> 'StaticList':
        """Returns self; this list is static"""
        return self


def search_str(value: Any) -> str:
    """
    Gets a lowercase str for searching
    Also handles integer floats.
    """
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).lower()
