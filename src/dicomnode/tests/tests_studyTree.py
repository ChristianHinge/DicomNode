
from asyncore import write
from curses import pair_content
from pydicom import Dataset
from pydicom.uid import generate_uid, UID, MediaStorageDirectoryStorage
from unittest import TestCase

from dicomnode.lib.imageTree import DicomTree, SeriesTree, StudyTree, PatientTree, IdentityMapping, ImageTreeInterface

class lib_studyTree(TestCase):
  def setUp(self) -> None:
    self.patientID_1 = "testID_1"
    self.patientID_2 = "testID_2"

    self.patientName_1 = "TestP1"
    self.patientName_2 = "TestP2"

    self.studyUID_1 = generate_uid()
    self.studyUID_2 = generate_uid()

    self.seriesUID_1 = generate_uid()
    self.seriesUID_2 = generate_uid()

    self.dataset_1 = Dataset()
    self.dataset_1_SOPInstanceUID = generate_uid()
    self.dataset_1.MediaStorageSOPClassUID = MediaStorageDirectoryStorage
    self.dataset_1.SOPInstanceUID = self.dataset_1_SOPInstanceUID
    self.dataset_1.SeriesInstanceUID = self.seriesUID_1
    self.dataset_1.StudyInstanceUID = self.studyUID_1
    self.dataset_1.PatientID = self.patientID_1
    self.dataset_1.PatientName = self.patientName_1
    self.dataset_1.ensure_file_meta()


    self.dataset_2 = Dataset()
    self.dataset_2_SOPInstanceUID = generate_uid()
    self.dataset_1.MediaStorageSOPClassUID = self.dataset_1.MediaStorageSOPClassUID = MediaStorageDirectoryStorage
    self.dataset_2.SOPInstanceUID = self.dataset_2_SOPInstanceUID
    self.dataset_2.SeriesInstanceUID = self.seriesUID_1
    self.dataset_2.StudyInstanceUID = self.studyUID_1
    self.dataset_2.PatientID = self.patientID_1
    self.dataset_2.PatientName = self.patientName_1
    self.dataset_2.ensure_file_meta()

    self.dataset_3 = Dataset()
    self.dataset_3_SOPInstanceUID = generate_uid()
    self.dataset_1.MediaStorageSOPClassUID = MediaStorageDirectoryStorage
    self.dataset_3.SOPInstanceUID = self.dataset_3_SOPInstanceUID
    self.dataset_3.SeriesInstanceUID = self.seriesUID_2
    self.dataset_3.StudyInstanceUID = self.studyUID_1
    self.dataset_3.PatientID = self.patientID_1
    self.dataset_3.PatientName = self.patientName_1
    self.dataset_3.ensure_file_meta()

    self.dataset_4 = Dataset()
    self.dataset_4_SOPInstanceUID = generate_uid()
    self.dataset_1.MediaStorageSOPClassUID = MediaStorageDirectoryStorage
    self.dataset_4.SOPInstanceUID = self.dataset_4_SOPInstanceUID
    self.dataset_4.SeriesInstanceUID = self.seriesUID_1
    self.dataset_4.StudyInstanceUID = self.studyUID_2
    self.dataset_4.PatientID = self.patientID_2
    self.dataset_4.PatientName = self.patientName_2
    self.dataset_4.ensure_file_meta()

    self.dataset_5 = Dataset()
    self.dataset_5_SOPInstanceUID = generate_uid()
    self.dataset_1.MediaStorageSOPClassUID = MediaStorageDirectoryStorage
    self.dataset_5.SOPInstanceUID = self.dataset_5_SOPInstanceUID
    self.dataset_5.SeriesInstanceUID = self.seriesUID_1
    self.dataset_5.StudyInstanceUID = self.studyUID_2
    self.dataset_5.PatientID = self.patientID_2
    self.dataset_5.PatientName = self.patientName_2
    self.dataset_5.ensure_file_meta()

    self.datasets = [self.dataset_1, self.dataset_2, self.dataset_3, self.dataset_4, self.dataset_5]

    self.empty_dataset = Dataset()


  ##### Test for creating the datastructure DicomTrees #####
  def test_create_DicomTree_createEmptyDataset(self):
    dt = DicomTree()
    # Assertions
    self.assertEqual(dt.images, 0)
    self.assertEqual(len(dt.data), 0)
    self.assertTrue(isinstance(dt.data, dict))

  def test_create_DicomTree_OnePicture(self):
    dt = DicomTree(self.dataset_1)
    pt = dt.data[self.dataset_1.PatientID]
    stt = pt.data[self.dataset_1.StudyInstanceUID]
    setree = stt.data[self.dataset_1.SeriesInstanceUID]
    # Assertions
    self.assertEqual(dt.images, 1)
    self.assertEqual(len(dt.data), 1)
    self.assertTrue(isinstance(pt, PatientTree))
    self.assertEqual(pt.images, 1)
    self.assertTrue(isinstance(stt, StudyTree))
    self.assertEqual(stt.images, 1)
    self.assertTrue(isinstance(setree, SeriesTree))
    self.assertEqual(setree.images, 1)
    self.assertEqual(setree.data[self.dataset_1.SOPInstanceUID], self.dataset_1)

  def test_create_DicomTree_ManyPictures(self):
    dt = DicomTree(self.datasets)
    # Assertions
    self.assertEqual(dt.images, len(self.datasets))

  def test_DicomTree_add_images(self):
    dt = DicomTree()
    dt.add_images(self.datasets)
    # Assertions
    self.assertEqual(dt.images, len(self.datasets))

  def test_Dicomtree_add_image(self):
    dt = DicomTree()
    dt.add_image(self.dataset_1)
    pt = dt.data[self.dataset_1.PatientID]
    stt = pt.data[self.dataset_1.StudyInstanceUID]
    setree = stt.data[self.dataset_1.SeriesInstanceUID]
    # Assertions
    self.assertEqual(dt.images, 1)
    self.assertEqual(dt.images, 1)
    self.assertEqual(len(dt.data), 1)
    self.assertTrue(isinstance(pt, PatientTree))
    self.assertEqual(pt.images, 1)
    self.assertTrue(isinstance(stt, StudyTree))
    self.assertEqual(stt.images, 1)
    self.assertTrue(isinstance(setree, SeriesTree))
    self.assertEqual(setree.images, 1)
    self.assertEqual(setree.data[self.dataset_1.SOPInstanceUID], self.dataset_1)

  def test_DicomTree_to_str_method_pictures(self):
    dt = DicomTree(self.datasets)
    self.assertEqual(str(dt), f"""Dicom Tree with {len(self.datasets)} images
  Patient StudyTree of TestP1 with 3 images
    Undefined Study Description with 3 images with Series:
      Tree of Undefined Series with 2 images
      Tree of Undefined Series with 1 images
  Patient StudyTree of TestP2 with 2 images
    Undefined Study Description with 2 images with Series:
      Tree of Undefined Series with 2 images
""")
  # Invalid Adding Data to trees
  def test_DicomTree_add_Invalid_dataset(self):
    dt = DicomTree()
    self.assertRaises(ValueError, dt.add_image, self.empty_dataset)

  def test_PatientTree_add_Empty_dataset(self):
    st = PatientTree()
    self.assertRaises(ValueError, st.add_image, self.empty_dataset)

  def test_PatintTree_add_missing_patient_ID(self):
    new_DS = Dataset()
    new_DS.StudyInstanceUID = self.studyUID_1

    pt = PatientTree()
    self.assertRaises(ValueError, pt.add_image, new_DS)

  def test_StudyTree_add_Empty_dataset(self):
    st = StudyTree()
    self.assertRaises(ValueError, st.add_image, self.empty_dataset)

  def test_StudyTree_add_missing_patient_ID(self):
    new_DS = Dataset()
    new_DS.StudyInstanceUID = self.studyUID_1
    st = StudyTree()
    self.assertRaises(ValueError, st.add_image, new_DS)


  def test_SeriesTree_add_Empty_dataset(self):
    st = SeriesTree()
    self.assertRaises(ValueError, st.add_image, self.empty_dataset)


  # Functions of DicomTree
  def test_DicomTree_apply_mapping(self):
    def writeModality(ds : Dataset):
      ds.Modality = 'OT'

    dt = DicomTree(self.datasets)
    dt.map(writeModality)

    for ds in self.datasets:
      self.assertEqual(ds.Modality, "OT")

  def test_DicomTree_trimTree(self):
    def filterfunc(ds):
      return ds.PatientID == self.patientID_1

    dt = DicomTree(self.datasets)
    removed_images = dt.trim_tree(filterfunc)
    self.assertEqual(removed_images + dt.images, len(self.datasets))

  # Interface is actually an interface
  def test_interface(self):
    class Tree(ImageTreeInterface):
      pass

    self.assertRaises(TypeError, Tree)

###### IdentityMapping #########
  def test_create_IdentityMapping(self):
    im = IdentityMapping()

    self.assertTrue(isinstance(im.StudyUIDMapping, dict))
    self.assertTrue(isinstance(im.SeriesUIDMapping, dict))
    self.assertTrue(isinstance(im.SOPUIDMapping, dict))
    self.assertTrue(isinstance(im.PatientMapping, dict))

    self.assertEqual(len(im.StudyUIDMapping), 0)
    self.assertEqual(len(im.SeriesUIDMapping), 0)
    self.assertEqual(len(im.SOPUIDMapping), 0)
    self.assertEqual(len(im.PatientMapping), 0)
    self.assertEqual(im.prefixSize, 4)

  def test_create_IM_with_DT(self):
    im = IdentityMapping()
    dt = DicomTree(self.datasets)
    im.fill_from_DicomTree(dt)

  def test_IdentityMapping_add_StudyUID(self):
    im = IdentityMapping()
    uid = im.add_StudyUID(self.studyUID_1)
    uid2 = im.StudyUIDMapping[self.studyUID_1.name]
    self.assertEqual(uid, uid2)

  def test_IdentityMapping_add_SeriesUID(self):
    im = IdentityMapping()
    uid = im.add_SeriesUID(self.seriesUID_1)
    uid2 = im.SeriesUIDMapping[self.seriesUID_1.name]
    self.assertEqual(uid, uid2)

  def test_IdentityMapping_add_SOPUID(self):
    im = IdentityMapping()
    uid =  im.add_SOPUID(self.dataset_1_SOPInstanceUID)
    uid2 = im.SOPUIDMapping[self.dataset_1_SOPInstanceUID.name]
    self.assertEqual(uid, uid2)

  def test_Getting_PatientID(self):
    im = IdentityMapping()
    ret_1 = im.add_Patient("Patient")
    ret_2 = im.add_Patient("Patient")
    self.assertEqual(ret_1, ret_2)

  def test_IdentityMapping_get_mapping(self):
    prefix = "pp_"
    im = IdentityMapping()
    dt = DicomTree(self.datasets)
    im.fill_from_DicomTree(dt, prefix)

    sop_uid_ret_1 = im.get_mapping(self.dataset_1_SOPInstanceUID)
    sop_str_ret_1 = im.get_mapping(self.dataset_1_SOPInstanceUID.name)

    study_uid_ret_1 = im.get_mapping(self.studyUID_1)
    study_str_ret_1 = im.get_mapping(self.studyUID_1.name)

    series_uid_ret_1 = im.get_mapping(self.seriesUID_1)
    series_str_ret_1 = im.get_mapping(self.seriesUID_1.name)

    patientID = im.get_mapping(self.patientID_1)

    self.assertEqual(patientID[:len(prefix)], prefix)

    self.assertEqual(sop_uid_ret_1, sop_str_ret_1)
    self.assertEqual(study_uid_ret_1, study_str_ret_1)
    self.assertEqual(series_uid_ret_1, series_str_ret_1)

    self.assertIsNone(im.get_mapping(generate_uid(prefix='1.3.')))

  def test_IdentityMapping_str(self):
    im = IdentityMapping()
    dt = DicomTree(self.datasets)
    im.fill_from_DicomTree(dt)

    self.assertEqual(str(im), """Identity Mapping
  Patient Mapping
{'testID_1': 'AnonymizedPatientID_0', 'testID_2': 'AnonymizedPatientID_1'}
  Study Mapping with 2 Mappings
  Series Mapping with 2
  SOP Mapping with 5 Mappings""")
