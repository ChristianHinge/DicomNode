"""This module contains a number of functions, which all have the same
call signature. Namely: Iterator[pydicom.Dataset].

They are called grinders for their similarly to meat grinders.
you pour some unprocessed data, and out come data mushed together.

Meta grinders are functions which produce grinders, which means they should be
called and not just referenced.
"""

__author__ = "Christoffer Vilstrup Jensen"

from typing import Iterator, List, Callable, Any
from pydicom import Dataset


def identity_grinder(image_generator: Iterator[Dataset] ) -> Iterator[Dataset]:
  """This is an identity function. The iterator is not called.

  Args:
      image_generator (Iterator[Dataset]): An iterator of dataset

  Returns:
      Iterator[Dataset]: The same iterator
  """
  return image_generator

def list_grinder(image_generator: Iterator[Dataset]) -> List[Dataset]:
  return list(image_generator)

def many_meta_grinder(*grinders: Callable[[Iterator[Dataset]], Any]) -> Callable[[Iterator[Dataset]], List[Any]]:
  """This meta grinder combines any number of grinders

  Args:
    grinders (Callable[[Iterator[Dataset]], Any])

  Returns:
      Callable[[Iterator[Dataset]], List[Any]]: _description_
  """
  def retFunc(image_generator: Iterator[Dataset]) -> List[Any]:
    grinded: List[Any] = []
    for grinder in grinders:
      grinded.append(grinder(image_generator))
    return grinded
  return retFunc
