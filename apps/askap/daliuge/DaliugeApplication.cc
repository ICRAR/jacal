/// @file DaliugeApplication.cc
///
/// @copyright (c) 2017 CSIRO
/// Australia Telescope National Facility (ATNF)
/// Commonwealth Scientific and Industrial Research Organisation (CSIRO)
/// PO Box 76, Epping NSW 1710, Australia
/// atnf-enquiries@csiro.au
///
/// This file is part of the ASKAP software distribution.
///
/// The ASKAP software distribution is free software: you can redistribute it
/// and/or modify it under the terms of the GNU General Public License as
/// published by the Free Software Foundation; either version 2 of the License,
/// or (at your option) any later version.
///
/// This program is distributed in the hope that it will be useful,
/// but WITHOUT ANY WARRANTY; without even the implied warranty of
/// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
/// GNU General Public License for more details.
///
/// You should have received a copy of the GNU General Public License
/// along with this program; if not, write to the Free Software
/// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
///
/// @author Stephen Ord <stephen.ord@csiro.au>

// Include own header file first
#include "daliuge/DaliugeApplication.h"

// System includes
#include <string>
#include <sstream>
#include <cstdlib>
#include <unistd.h>
#include <iostream>

// ASKAPsoft includes

#include "askap/AskapError.h"


// Using/namespace
using namespace askap;

DaliugeApplication::DaliugeApplication() {
    fprintf(stdout,"\t DaliugeApplication - default constructor\n");
}

DaliugeApplication::~DaliugeApplication() {
    fprintf(stdout,"\t DaliugeApplication - default destructor\n");
}

DaliugeApplication::ShPtr DaliugeApplication::createDaliugeApplication(const std::string& name)
{
   ASKAPTHROW(AskapError, "createDaliugeApplication is supposed to be defined for every derived application, "
                          "DaliugeApplication::createDaliugeApplication should never be called");
   return DaliugeApplication::ShPtr();
}
