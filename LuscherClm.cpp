//
//  PyModules.cpp
//  modules
//
//  Created by Thorsten Kurth on 28.04.15.
//
//

#include "LuscherClm.hpp"


BOOST_PYTHON_MODULE(threevecd)
{
    class_< threevec<double> >("threevecd",init<double,double,double>());
}

BOOST_PYTHON_MODULE(LuscherClm)
{
    class_<Zetafunc>("LuscherClm",init<int,int, optional<double,threevec<double>,double,int> >())
    .def("eval",&Zetafunc::operator());
    boost::python::to_python_converter<dcomplex,dcomplex_to_python_object>();
}
