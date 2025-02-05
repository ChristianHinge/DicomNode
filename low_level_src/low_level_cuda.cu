#ifndef LOW_LEVEL_CUDA_DICOMNODE_H
#define LOW_LEVEL_CUDA_DICOMNODE_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

int cuda_add(int i, int j){
  return i + j;
}

PYBIND11_MODULE(_cuda, m){
  m.doc() = "pybind11 example plugin";
  m.attr("__name__") = "dicomnode._cuda";


  m.def("add", &cuda_add, "A function that adds two numbers");
}

#endif