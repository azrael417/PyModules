//
//  PyModules.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "LuscherClm.hpp"

//methods
static PyMethodDef LuscherClmMethods[] = {
    {"init",  clm_init, METH_VARARGS, "Initialize clm class!"},
    {"eval", clm_evaluate, METH_VARARGS, "Evaluate the Zeta-Function!"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
initLuscherClm(void)
{
    PyObject *m = Py_InitModule("LuscherClm", LuscherClmMethods);
    return;
}
