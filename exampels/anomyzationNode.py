from dicomnode.lib.anonymization import anonymize_dicom_tree
from dicomnode.lib.dimse import Address
from dicomnode.lib.grinders import dicom_tree_grinder
from dicomnode.lib.imageTree import DicomTree, IdentityMapping

from dicomnode.server.input import AbstractInput
from dicomnode.server.nodes import AbstractPipeline

from pydicom import Dataset
from pathlib import Path
from typing import List, Any, Iterator, Callable, Iterable, Dict, Optional

INPUT_ARG = "dataset"

class DicomObjectInput(AbstractInput):
  required_tags: List[int] = [
    0x00100020, # PatientID
    0x00100010, # PatientName
    0x00080016, # SOPInstanceUID
    0x0020000D, # StudyInstanceUID
    0x0020000E, # SeriesInstanceUID
  ]

  image_grinder: Callable[[Iterator[Dataset]], Any] = dicom_tree_grinder

  def validate(self):
    return True

  # DicomObjectInput Definition Done

class AnonymizationPipeline(AbstractPipeline):
  """Fully Anonymizing Dicom pipeline Including new SOPinstanceUID, Series UID, and StudyUID"""

  # Process Configuration
  prefix_size: int = 4
  BASE_NAME: str = "Anon"

  # Pipeline configuration
  port: int = 9999
  ae_title: str = "ANONYMIZATION"
  log_path: Optional[str | Path] = Path("Anon.log")

  # Input configuration
  input = {
    INPUT_ARG : DicomObjectInput
  }

  # Endpoint configuration
  endpoints: List[Address] = [Address('localhost', 4321, 'STORESCP')]

  def process(self, input_data: Dict[str, DicomTree]) -> Iterable[Dataset]:
    DT: DicomTree = input_data[INPUT_ARG]
    IM = IdentityMapping(prefix_size=self.prefix_size)
    IM.fill_from_DicomTree(DT)
    DT.map(anonymize_dicom_tree(IM, self.BASE_NAME))

    return DT

  # AnonymizationPipeline definition done

if __name__ == '__main__':
  AnonymizationPipeline()
