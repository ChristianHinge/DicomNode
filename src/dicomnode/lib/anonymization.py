
from types import NoneType
from pydicom import Dataset
from pydicom.valuerep import VR
from pydicom.tag import BaseTag

from typing import Callable, Optional

from dicomnode.lib.studyTree import IdentityMapping

BASE_ANONYMIZED_PATIENT_NAME = "Anonymized_PatientName"

def anonymize_dataset(
  UIDMapping : IdentityMapping,
  PatientName : str = BASE_ANONYMIZED_PATIENT_NAME,
  StudyID : Optional[str] = "Study"
  ) -> Callable[[Dataset], NoneType]:
  """Creates a function

  Args:
      UIDMapping (IdentityMapping): _description_
      PatientName (str, optional): _description_. Defaults to BASE_ANONYMIZED_PATIENT_NAME.
      StudyID (Optional[str], optional): _description_. Defaults to "Study".

  Returns:
      Callable[[Dataset], NoneType]: _description_
  """
  def retfunc(dataset) -> NoneType:
    newPatientID = UIDMapping.PatientMapping[dataset.PatientID]
    dataset.PatientID = newPatientID
    PatientNumber = newPatientID[-UIDMapping.prefixSize:]
    if StudyID:
      dataset.StudyID = f"{StudyID}_{PatientNumber}"

    def anon_ds(ds):
      if 'meta' in ds:
        anon_ds(ds.meta)
      for dataElement in ds.iterall():
        vr = dataElement.VR # The VR of a data set is either a pydicom.valuerep.VR or str
        if type(dataElement.VR) == VR: # The VR might be very wierd
          vr = str(vr)
          _, vr = vr.split('.')
        if dataElement.tag == BaseTag(0x00100010): # PatientName tag value
          dataElement.value  = f"{PatientName}_{PatientNumber}"
        elif vr == "PN":
          dataElement.value = "Anon_" + dataElement.name
        elif vr == "SQ":
          for seq in dataElement:
            anon_ds(seq)
        elif vr == "UI":
          if newUID := UIDMapping.get_mapping(dataElement.value):
            dataElement.value = newUID
    anon_ds(dataset)

  return retfunc
