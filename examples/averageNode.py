import numpy
import logging
import os

from pathlib import Path

from dicomnode.server.grinders import ManyGrinder, TagGrinder, NumpyGrinder
from dicomnode.lib.dicom_factory import Blueprint, CopyElement, FillingStrategy, SOP_common_blueprint, general_series_blueprint, image_plane_blueprint
from dicomnode.lib.numpy_factory import NumpyFactory, image_pixel_blueprint


from dicomnode.server.nodes import AbstractPipeline
from dicomnode.server.input import DynamicInput
from dicomnode.server.pipeline_tree import InputContainer
from dicomnode.server.output import PipelineOutput, FileOutput, NoOutput

from typing import Dict, Any


DEFAULT_PATH = "/tmp/"
OUTPUT_PATH = Path(os.environ.get("AVERAGE_NODE_OUTPUT_PATH", default=DEFAULT_PATH))

INPUT_KW = "series"

blueprint: Blueprint = SOP_common_blueprint \
  + image_plane_blueprint \
  + image_pixel_blueprint \
  + general_series_blueprint

factory = NumpyFactory()
factory.series_description = "Averaged Image"

class SeriesInputs(DynamicInput):
  image_grinder = ManyGrinder(NumpyGrinder(), TagGrinder(0x00080031))
  required_tags = blueprint.get_required_tags()

  def validate(self) -> bool:
    if len(self.data) == 0:
      return False
    lengths = set()
    for leaf in self.data.values():
      lengths.add(len(leaf))
    return len(lengths) == 1 # this checks that all leafs are the same length

class AveragingPipeline(AbstractPipeline):
  header_blueprint = blueprint
  dicom_factory = factory
  filling_strategy = FillingStrategy.COPY

  ae_title = "AVERAGENODE"
  ip = '0.0.0.0'
  port = 1337

  log_level = logging.DEBUG
  disable_pynetdicom_logger = True

  input = {
    INPUT_KW : SeriesInputs
  }


  def process(self, input_data: InputContainer) -> PipelineOutput:
    if input_data.header is None or self.dicom_factory is None:
      raise Exception

    images = []
    SeriesTimes = []
    for image, SeriesTime in input_data[INPUT_KW].values():
      images.append(image)
      for __tag, series_time in SeriesTime:
        SeriesTimes.append(series_time)

    studies = numpy.array(images)
    result = studies.mean(axis=0)
    series = self.dicom_factory.build_from_header(input_data.header, result)

    return FileOutput([(OUTPUT_PATH, series)])

if __name__ == "__main__":
  AveragingPipeline()
