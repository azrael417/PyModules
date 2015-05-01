//
//  PyModules.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "LuscherClm.hpp"

/** to-python convert to complex<double> */
struct dcomplex_to_python_object
{
    static PyObject* convert(dcomplex const& comp)
    {
        if(fabs(comp.im())<std::numeric_limits<double>::epsilon()){
            boost::python::object result=boost::python::object(complex<double>(comp.re(),comp.im()));
            return boost::python::incref(result.ptr());
        }
        else{
            return Py_BuildValue("d",comp.re());
        }
    }
};


BOOST_PYTHON_MODULE(threevecd)
{
    class_< threevec<double> >("threevecd",init<double,double,double>());
}

BOOST_PYTHON_MODULE(LuscherClm)
{
    class_<Zetafunc>("LuscherClm",init<int,int, optional<double,threevec<double>,double,int> >())
    .def("eval",&Zetafunc::operator(),return_value_policy<return_by_value>());
    boost::python::to_python_converter<dcomplex,dcomplex_to_python_object>();
}
