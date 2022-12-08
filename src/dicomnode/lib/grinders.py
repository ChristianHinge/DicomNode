"""This module contains a number of functions, which all have the same
call signature. Namely: Iterator[pydicom.Dataset].

They are called grinders for their similarly to meat grinders.
you pour some unprocessed data, and out come data mushed together.

Meta grinders are functions which produce grinders, which means they should be
called and not just referenced.
"""

__author__ = "Christoffer Vilstrup Jensen"

from typing import Dict, Iterator, List, Callable, Any
from pydicom import Dataset

from dicomnode.lib.exceptions import InvalidDataset
from dicomnode.lib.imageTree import DicomTree

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

def dicom_tree_grinder(image_generator: Iterator[Dataset]) -> DicomTree:
  return DicomTree(image_generator)

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

try:
  import numpy
  unsigned_array_encoding: Dict[int, type] = {
    8 : numpy.uint8,
    16 : numpy.uint16,
    32 : numpy.uint32,
    64 : numpy.uint64,
  }

  signed_array_encoding: Dict[int, type] = {
    8 : numpy.int8,
    16 : numpy.int16,
    32 : numpy.int32,
    64 : numpy.int64,
  }

  def numpy_grinder(datasets_iterator: Iterator[Dataset]) -> numpy.ndarray:
    """
      Requires Tags:
        0x7FE00008 or 0x7FE0009 or 0x7FE00010
    """
    datasets: List[Dataset] = list(datasets_iterator)
    pivot = datasets[0]
    x_dim = pivot.Columns
    y_dim = pivot.Rows
    z_dim = len(datasets)

    if 0x7FE00008 in pivot:
      dataType = numpy.float32
    elif 0x7FE00009 in pivot:
      dataType = numpy.float64
    elif 0x002801052 in pivot and 0x00281053 in pivot:
      dataType = numpy.float64
    elif pivot.PixelRepresentation == 0:
      dataType = unsigned_array_encoding.get(pivot.BitsAllocated, None)
    else:
      dataType = signed_array_encoding.get(pivot.BitsAllocated, None)
    
    if dataType is None:
      raise InvalidDataset
    
    image_array: numpy.ndarray = numpy.empty((x_dim, y_dim, z_dim), dtype=dataType)

    for i, dataset in enumerate(datasets):
      image_array[i,:,:] = dataset.pixel_array

    return image_array
  
except ImportError:
  pass
