"""Library methods for manipulation of pydicom.dataset objects
"""
from typing import Any, List, Callable, Tuple

import numpy

from pydicom import Dataset
from pydicom.uid import UID, generate_uid, ImplicitVRLittleEndian, ExplicitVRBigEndian, ExplicitVRLittleEndian

from dicomnode.constants import DICOMNODE_IMPLEMENTATION_UID, DICOMNODE_IMPLEMENTATION_NAME, DICOMNODE_VERSION
from dicomnode.lib.exceptions import InvalidDataset


def gen_uid() -> UID:
  return generate_uid(prefix=DICOMNODE_IMPLEMENTATION_UID + '.')

def make_meta(dicom: Dataset) -> None:
  """Similar to fix_meta_info method, however UID are generated with dicomnodes prefix instead

  Args:
      dicom (Dataset): dicom dataset to be updated
  Raises:
      InvalidDataset: If meta header cannot be generated or is Transfer syntax is not supported
  """
  if dicom.is_little_endian is None:
    dicom.is_little_endian = True
  if dicom.is_implicit_VR is None:
    dicom.is_implicit_VR = True
  if not 0x00080016 in dicom:
    raise InvalidDataset("Cannot create meta header without SOPClassUID")
  if not 0x00080018 in dicom:
    dicom.SOPInstanceUID = gen_uid()

  dicom.ensure_file_meta()

  dicom.file_meta.FileMetaInformationVersion = b'\x00\x01'
  dicom.file_meta.ImplementationClassUID = DICOMNODE_IMPLEMENTATION_UID
  dicom.file_meta.ImplementationVersionName = f"{DICOMNODE_IMPLEMENTATION_NAME} {DICOMNODE_VERSION}"
  dicom.file_meta.MediaStorageSOPClassUID = dicom.SOPClassUID
  dicom.file_meta.MediaStorageSOPInstanceUID = dicom.SOPInstanceUID

  if dicom.is_little_endian and dicom.is_implicit_VR:
    dicom.file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
  elif dicom.is_little_endian and not dicom.is_implicit_VR:
    dicom.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
  elif not dicom.is_little_endian and not dicom.is_implicit_VR:
    dicom.file_meta.TransferSyntaxUID = ExplicitVRBigEndian
  else:
    raise InvalidDataset("Implicit VR Big Endian is not a "
                         "supported Transfer Syntax.")


def get_tag(Tag: int) -> Callable[[Dataset], Any]:
  def retFunc(Dataset):
    if Tag in Dataset:
      return Dataset[Tag]
    else:
      return None
  return retFunc


def extrapolate_image_position_patient(
    slice_thickness:float,
    orientation: int,
    initial_position:  Tuple[float, float, float],
    image_orientation: Tuple[float, float, float, float, float, float],
    image_number: int,
    slices: int) -> List[List[float]]:
  """Extrapolates a list of image positions from an initial position.

  Useful for when you want to generate positions for an series.

  Assumes even slice thickness throughout the series

  Args:
      slice_thickness (float): Thickness of an image slice
      orientation (int): Direction to the extrapolation
      initial_position (Tuple[float, float, float]): Initial position as x,y,z
      image_orientation (Tuple[float, float, float, float, float, float]): Vectors defining the patient vector space
      image_number (int): Image number of the initial position
      slices (int): Number of slices in the extrapolated positions

  Returns:
      List[List[float]]: List of positions in [x,y,z] sub-lists
  """

  cross_vector = slice_thickness * orientation * numpy.array([
    image_orientation[1] * image_orientation[5] - image_orientation[2] * image_orientation[4],
    image_orientation[2] * image_orientation[3] - image_orientation[0] * image_orientation[5],
    image_orientation[0] * image_orientation[4] - image_orientation[1] * image_orientation[3],
  ])

  
  position = [numpy.array(initial_position) + (slice_num - image_number) * cross_vector for slice_num in numpy.arange(1,slices + 1, 1, dtype=numpy.float64)]

  return [[float(val) for val in pos] for pos in position]



def extrapolate_image_position_patient_dataset(dataset: Dataset, slices: int) -> List[List[float]]:
  """Wrapper function for extrapolate_image_position_patient
  Extracts values from a dataset and passes it to the function

  Args:
      dataset (Dataset): Dataset that contains:
        * 0x00180050 - SliceThickness
        * 0x00185100 - PatientPosition
        * 0x00200013 - InstanceNumber
        * 0x00200032 - ImagePositionPatient
        * 0x00200037 - ImageOrientation
      slices (int): Number of slices in extrapolation

  Raises:
      InvalidDataset: If the dataset is invalid

  Returns:
      List[List[float]]: List of positions in [x,y,z] sub-lists
  """
  required_tags = [
    0x00180050, # SliceThickness
    0x00185100, # PatientPosition
    0x00200013, # InstanceNumber
    0x00200032, # ImagePositionPatient
    0x00200037, # ImageOrientation
  ]
  for required_tag in required_tags:
    if required_tag not in dataset: # Need Instance for offset calculation
      raise InvalidDataset

  if dataset[0x00200037].VM != 6: # ImageOrientation
    raise InvalidDataset

  image_orientation: Tuple[float, float, float, float, float, float] = tuple(pos for pos in dataset.ImageOrientationPatient)

  if dataset[0x00200032].VM != 3:
    raise InvalidDataset

  head_first = dataset.PatientPosition.startswith('HF') # Head First
  if head_first:
    orientation = -1
  else:
    orientation = 1

  initial_position: Tuple[float, float, float] = tuple(pos for pos in dataset.ImagePositionPatient)

  return extrapolate_image_position_patient(
    dataset.SliceThickness,
    orientation,
    initial_position,
    image_orientation,
    dataset.InstanceNumber,
    slices
  )
