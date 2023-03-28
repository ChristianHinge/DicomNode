from copy import deepcopy
import logging
import os
from random import randint
from pathlib import Path
from sys import getrefcount
from time import sleep
from typing import List, Dict, Any, Iterable
from unittest import TestCase

from pydicom import Dataset
from pydicom.uid import RawDataStorage, ImplicitVRLittleEndian

from dicomnode.lib.dicom import gen_uid, make_meta
from dicomnode.lib.dimse import Address, send_image, send_images_thread
from dicomnode.lib.dicom_factory import Blueprint, CopyElement, StaticElement
from dicomnode.lib.numpy_factory import NumpyFactory
from dicomnode.lib.exceptions import CouldNotCompleteDIMSEMessage
from dicomnode.lib.image_tree import DicomTree

from tests.helpers import generate_numpy_datasets, personify, bench, get_test_ae, TESTING_TEMPORARY_DIRECTORY

from dicomnode.server.input import AbstractInput, HistoricAbstractInput
from dicomnode.server.nodes import AbstractPipeline, AbstractThreadedPipeline, AbstractQueuedPipeline
from dicomnode.server.output import NoOutput, PipelineOutput
from dicomnode.server.pipelineTree import InputContainer


TEST_AE_TITLE = "TEST_AE"
SENDER_AE = "SENDER_AE"

DEFAULT_DATASET = Dataset()
DEFAULT_DATASET.SOPClassUID = RawDataStorage
DEFAULT_DATASET.PatientSex = 'M'
make_meta(DEFAULT_DATASET)
DATASET_SOPInstanceUID = DEFAULT_DATASET.SOPInstanceUID.name

ENDPOINT_PORT = 50000

TEST_CPR = "1502799995"
INPUT_KW = "test_input"
HISTORIC_KW = "historic_input"

DEFAULT_DATASET.PatientID = TEST_CPR

DICOM_STORAGE_PATH = Path(f"{TESTING_TEMPORARY_DIRECTORY}/file_storage")
PROCESSING_DIRECTORY = Path(f"{TESTING_TEMPORARY_DIRECTORY}/working_directory")

##### Test Input Implementations #####

class TestInput(AbstractInput):
  required_tags: List[int] = [0x00080018, 0x00100040]

  def validate(self):
    return True

class TestNeverValidatingInput(AbstractInput):
  required_tags: List[int] = [0x00080018]

  def validate(self):
    return False

class TestHistoricInput(HistoricAbstractInput):
  address = Address('localhost', ENDPOINT_PORT, "DUMMY")
  required_tags: List[int] = [0x00080018]
  c_move_blueprint = Blueprint([CopyElement(0x00100020), StaticElement(0x00080052, 'CS', 'PATIENT')])

  def validate(self) -> bool:
    return True

##### Test Output Implementations #####
class FaultyPipelineOutput(PipelineOutput):
  def send(self) -> bool:
    raise Exception

##### Test Pipeline Implementations #####

class TestNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def process(self, InputData: InputContainer) -> PipelineOutput:
    self.logger.info("process is called")
    return NoOutput()


class NeverValidateNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestNeverValidatingInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def process(self, InputData: InputContainer) -> PipelineOutput:
    self.logger.info("process is called")
    return NoOutput()


class FaultyNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def process(self, InputData: InputContainer) -> PipelineOutput:
    raise Exception



class FileStorageNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = True
  root_data_directory = DICOM_STORAGE_PATH
  processing_directory = PROCESSING_DIRECTORY

  def process(self, input_data: InputContainer) -> PipelineOutput:
    log_message =  f"process is called at cwd: {os.getcwd()}"
    self.logger.info(log_message)
    return NoOutput()

class FaultyFilterNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def filter(self, dataset: Dataset) -> bool:
    raise Exception

  def process(self, InputData: InputContainer) -> PipelineOutput:
    raise Exception

class MaxFilterNode(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.CRITICAL
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def filter(self, dataset: Dataset) -> bool:
    return False

  def process(self, InputData: InputContainer) -> PipelineOutput:
    raise Exception

class TestThreadedNode(AbstractThreadedPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestNeverValidatingInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.CRITICAL
  disable_pynetdicom_logger: bool = True
  processing_directory = None

  def process(self, InputData: InputContainer) -> PipelineOutput:
    self.logger.info("process is called")
    return NoOutput()

fs_threaded_path = Path("/tmp/pipeline_tests/fs_threaded")

class FileStorageThreadedNode(AbstractThreadedPipeline):
  ae_title = TEST_AE_TITLE
  input = {INPUT_KW : TestNeverValidatingInput }
  require_calling_aet = [SENDER_AE]
  log_level: int = logging.CRITICAL
  disable_pynetdicom_logger: bool = True
  root_data_directory = fs_threaded_path
  processing_directory = None

  def process(self, InputData: InputContainer) -> PipelineOutput:
    self.logger.info("process is called")
    return NoOutput()

class HistoricPipeline(AbstractPipeline):
  ae_title = TEST_AE_TITLE
  input = {
    INPUT_KW : TestNeverValidatingInput,
    HISTORIC_KW : TestHistoricInput
   }
  require_calling_aet = [SENDER_AE, "DUMMY"]
  log_level: int = logging.DEBUG
  disable_pynetdicom_logger: bool = False
  dicom_factory = NumpyFactory()
  processing_directory = None

  def process(self, input_container: InputContainer) -> PipelineOutput:
    return NoOutput()


class QueueNode(AbstractQueuedPipeline):
  input = { INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  ae_title = TEST_AE_TITLE
  disable_pynetdicom_logger = True
  processing_directory = None

  def process(self, input_container: InputContainer) -> PipelineOutput:
    self.logger.info("process is called")
    return NoOutput()

class FaultyQueueNode(AbstractQueuedPipeline):
  input = { INPUT_KW : TestInput }
  require_calling_aet = [SENDER_AE]
  ae_title = TEST_AE_TITLE
  disable_pynetdicom_logger = True
  processing_directory = None

  def process(self, input_container: InputContainer) -> PipelineOutput:
    raise Exception

##### Test Cases #####
class PipelineTestCase(TestCase):
  def setUp(self):
    self.node = TestNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()

  def test_send_C_store_success(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    with self.assertLogs("dicomnode", logging.DEBUG) as cm:
      response = send_image(SENDER_AE, address, DEFAULT_DATASET)

    self.assertEqual(response.Status, 0x0000)
    self.assertIn("INFO:dicomnode:process is called", cm.output)
    self.assertIn(f"DEBUG:dicomnode:Removing Patient {DEFAULT_DATASET.PatientID}", cm.output)

    # Okay This is mostly to ensure lazyness
    # See the advanced docs guide for details
    self.assertEqual(self.node.data_state.images, 0)

  def test_reject_connection(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    self.assertRaises(CouldNotCompleteDIMSEMessage,send_image,"NOT_SENDER_AE", address, DEFAULT_DATASET)

  def test_missing_sex(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    ds = deepcopy(DEFAULT_DATASET)
    del ds.PatientSex
    response = send_image(SENDER_AE, address, ds)
    self.assertEqual(response.Status, 0xB006)

  def test_missing_PatientID(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    ds = deepcopy(DEFAULT_DATASET)
    del ds.PatientID
    response = send_image(SENDER_AE, address, ds)
    self.assertEqual(response.Status, 0xB007)

  @bench
  def performance_send(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    images_1 = DicomTree(generate_numpy_datasets(50, PatientID = "1502799995"))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))
    thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
    ret_1 = thread_1.join()


class NeverValidatingTestNode(TestCase):
  """This class is a standard pipeline, where the input never validates.

  This is relevant to test various state changes without processing

  """


class FaultyNodeTestCase(TestCase):
  def setUp(self):
    self.node = FaultyNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    self.node.close()

  def test_faulty_process(self):
    with self.assertLogs("dicomnode", logging.CRITICAL) as cm:
      address = Address('localhost', self.test_port, TEST_AE_TITLE)
      response = send_image(SENDER_AE, address, DEFAULT_DATASET)
      self.assertEqual(response.Status, 0x0000)
    self.assertIn("CRITICAL:dicomnode:Encountered error in user function Process", cm.output)

class FileStorageTestCase(TestCase):
  def setUp(self):
    DICOM_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    self.node = FileStorageNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()

  @bench
  def performance_send_fs(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    images_1 = DicomTree(generate_numpy_datasets(50, PatientID = "1502799995"))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))

    thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
    ret_1 = thread_1.join()
    self.assertEqual(ret_1, 0)
    self.assertEqual(self.node.data_state.images,50) # type: ignore

  def test_send_concurrently_fs(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    num_images = 2

    CPR_1 = "1502799995"
    CPR_2 = "0201919996"

    images_1 = DicomTree(generate_numpy_datasets(num_images, PatientID = CPR_1))
    images_2 = DicomTree(generate_numpy_datasets(num_images, PatientID = CPR_2))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))

    images_2.map(personify(
      tags=[
        (0x00100010,"PN", "Ellen Louise Test"),
        (0x00100040,"CS", "M")
      ]
    ))

    with self.assertLogs("dicomnode", logging.DEBUG) as cm:
      thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
      thread_2 = send_images_thread(SENDER_AE, address, images_2, None, False)
      ret_1 = thread_1.join()
      ret_2 = thread_2.join()

    self.assertIn(f"INFO:dicomnode:process is called at cwd: {str(self.node.processing_directory)}/{CPR_1}",cm.output)
    self.assertIn(f"INFO:dicomnode:process is called at cwd: {str(self.node.processing_directory)}/{CPR_2}",cm.output)

    self.assertEqual(ret_1, 0)
    self.assertEqual(ret_2, 0)
    self.assertEqual(self.node.data_state.images, 0)

class SetupLessFileStorageTestCase(TestCase):
  """This test case is for testing the various current working directory changes
  done by the node.

  Args:
      TestCase (_type_): _description_
  """
  def test_setup_and_teardown_of_tmp_directories(self):
    os.chdir(TESTING_TEMPORARY_DIRECTORY)
    node = FileStorageNode()
    node.port = randint(1025,65535)
    self.assertEqual(os.getcwd(), TESTING_TEMPORARY_DIRECTORY)
    node.open(blocking=False)
    self.assertEqual(os.getcwd(), str(node.processing_directory))
    node.close()
    self.assertEqual(os.getcwd(), TESTING_TEMPORARY_DIRECTORY)
    self.assertFalse(node.processing_directory.exists()) #type: ignore


class MaxFilterTestCase(TestCase):
  def setUp(self):
    self.node = MaxFilterNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()

  def test_send_C_store_rejected(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    response = send_image(SENDER_AE, address, DEFAULT_DATASET)
    self.assertEqual(response.Status, 0xB006)


class FaultyFilterTestCase(TestCase):
  def setUp(self):
    self.node = FaultyFilterNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    self.node.close()

  def test_send_C_store_rejected(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    response = send_image(SENDER_AE, address, DEFAULT_DATASET)
    self.assertEqual(response.Status, 0xA801)


class TestNodeTestCase(TestCase):
  def setUp(self):
    self.node = TestThreadedNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    self.node.join_threads()
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()

  @bench
  def performance_threaded_send(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    images_1 = DicomTree(generate_numpy_datasets(50, PatientID = "1502799995"))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))


    thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)

    ret_1 = thread_1.join()

    self.assertEqual(ret_1, 0)

    self.assertEqual(self.node.data_state.images, 50) # type: ignore

  def test_threaded_send_concurrently(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    num_images = 2

    images_1 = DicomTree(generate_numpy_datasets(num_images, PatientID = "1502799995"))
    images_2 = DicomTree(generate_numpy_datasets(num_images, PatientID = "0201919996"))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))

    images_2.map(personify(
      tags=[
        (0x00100010,"PN", "Ellen Louise Test"),
        (0x00100040,"CS", "M")
      ]
    ))

    with self.assertLogs("dicomnode", logging.DEBUG) as cm:
      thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
      thread_2 = send_images_thread(SENDER_AE, address, images_2, None, False)

      ret_1 = thread_1.join()
      ret_2 = thread_2.join()

    self.assertIn("DEBUG:dicomnode:insufficient data for patient 1502799995", cm.output)
    self.assertIn("DEBUG:dicomnode:insufficient data for patient 0201919996", cm.output)

    self.assertEqual(ret_1, 0)
    self.assertEqual(ret_2, 0)

    self.assertEqual(self.node.data_state.images, 2* num_images)


class FileStorageThreadedNodeTestCase(TestCase):
  def setUp(self):
    DICOM_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    self.node = FileStorageThreadedNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()

  @bench
  def performance_threaded_send_concurrently_fs(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    images_1 = DicomTree(generate_numpy_datasets(50, PatientID = "1502799995"))
    images_2 = DicomTree(generate_numpy_datasets(50, PatientID = "0201919996"))


    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Name Test"),
        (0x00100040, "CS", "M")
      ]
    ))

    images_2.map(personify(
      tags=[
        (0x00100010,"PN", "Ellen Louise Test"),
        (0x00100040,"CS", "M")
      ]
    ))

    thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
    thread_2 = send_images_thread(SENDER_AE, address, images_2, None, False)

    ret_1 = thread_1.join()
    ret_2 = thread_2.join()

    self.assertEqual(ret_1, 0)
    self.assertEqual(ret_2, 0)

    self.assertEqual(self.node.data_state.images,100) # type: ignore

  def test_threaded_send_concurrently_fs(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    num_images = 2

    images_1 = DicomTree(generate_numpy_datasets(num_images, PatientID = "1502799995"))
    images_2 = DicomTree(generate_numpy_datasets(num_images, PatientID = "0201919996"))

    images_1.map(personify(
      tags=[
        (0x00100010, "PN", "Odd Haugen Test"),
        (0x00100040, "CS", "M")
      ]
    ))

    images_2.map(personify(
      tags=[
        (0x00100010,"PN", "Ellen Louise Test"),
        (0x00100040,"CS", "M")
      ]
    ))

    thread_1 = send_images_thread(SENDER_AE, address, images_1, None, False)
    thread_2 = send_images_thread(SENDER_AE, address, images_2, None, False)

    ret_1 = thread_1.join()
    ret_2 = thread_2.join()

    self.assertEqual(ret_1, 0)
    self.assertEqual(ret_2, 0)

    self.assertEqual(self.node.data_state.images,2 * num_images)

class QueuedNodeTestCase(TestCase):
  def setUp(self):
    self.node = QueueNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    while self.node.ae.active_associations != []:
      sleep(0.005)
    self.node.close()
    os.chdir(TESTING_TEMPORARY_DIRECTORY)

  def test_send_C_store_success(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    with self.assertLogs("dicomnode", logging.DEBUG) as cm:
      response = send_image(SENDER_AE, address, DEFAULT_DATASET)

    self.assertIn("INFO:dicomnode:process is called", cm.output)
    self.assertNotIn("ERROR:dicomnode:Could not export data", cm.output)

    self.assertEqual(response.Status, 0x0000)
    self.assertEqual(self.node.data_state.images,0)

class FaultyQueueTestCase(TestCase):
  def setUp(self):
    self.node = FaultyQueueNode()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    self.node.close()

  def test_send_C_store_Faulty(self):
    address = Address('localhost', self.test_port, TEST_AE_TITLE)
    with self.assertLogs("dicomnode", logging.CRITICAL) as cm:
      response = send_image(SENDER_AE, address, DEFAULT_DATASET)

    self.node.process_queue.join()

    self.assertIn("CRITICAL:dicomnode:Encountered error in user function process", cm.output)
    self.assertEqual(response.Status, 0x0000)

class HistoricTestCase(TestCase):
  def setUp(self) -> None:
    self.node = HistoricPipeline()
    self.test_port = randint(1025,65535)
    self.node.port = self.test_port
    self.node.open(blocking=False)

  def tearDown(self) -> None:
    self.node.close()

  def test_create_and_send(self):
    address = Address("localhost", self.test_port, TEST_AE_TITLE)
    endpoint = get_test_ae(ENDPOINT_PORT, self.test_port, logging.getLogger("dicomnode"))

    with self.assertLogs("dicomnode", logging.DEBUG) as cm:
      response = send_image(SENDER_AE, address, DEFAULT_DATASET)
      sleep(0.25) # wait for all the threads to be done
    endpoint.shutdown()