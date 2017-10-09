/// @file NEUtils.cc
///
/// @abstract Just some static utility funcitons
///
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "NEUtils"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_NEUtils() {
        return std::string("NEUtils");
    }


} // namespace askap

/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_NEUtils()

#include <iostream>
#include <vector>



#include <daliuge/DaliugeApplication.h>
#include <factory/NEUtils.h>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// LOFAR Blob
#include <Blob/BlobString.h>
#include <Blob/BlobOBufString.h>
#include <Blob/BlobIBufString.h>
#include <Blob/BlobOStream.h>
#include <Blob/BlobIStream.h>
// ASKAP Logger

#include <askap/AskapLogging.h>
#include <askap/AskapError.h>



// params helpers
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/ImageParamsHelper.h>
#include <measurementequation/ImageFFTEquation.h>
#include <parallel/GroupVisAggregator.h>


#include <gridding/IVisGridder.h>
#include <gridding/VisGridderFactory.h>
#include <fitting/ImagingNormalEquations.h>

#include <fitting/Params.h>


#include <string.h>
#include <sys/time.h>




namespace askap {

void NEUtils::receiveNE(askap::scimath::ImagingNormalEquations::ShPtr itsNE, dlg_app_info *app) {
    ASKAPCHECK(itsNE, "NormalEquations not defined");
    size_t itsNESize;
    size_t n_read = app->inputs[0].read((char *) &itsNESize, sizeof(itsNESize));
    LOFAR::BlobString b1;
    b1.resize(itsNESize);
    n_read = app->inputs[0].read(b1.data(), itsNESize);

    ASKAPCHECK(n_read == itsNESize, "Unable to read NE of expected size");

    LOFAR::BlobIBufString bib(b1);
    LOFAR::BlobIStream bis(bib);
    bis >> *itsNE;

  }
  void NEUtils::sendNE(askap::scimath::ImagingNormalEquations::ShPtr itsNe, dlg_app_info *app ) {

      ASKAPCHECK(itsNe, "NormalEquations not defined");

      LOFAR::BlobString b1;
      LOFAR::BlobOBufString bob(b1);
      LOFAR::BlobOStream bos(bob);
      bos << *itsNe;
      size_t itsNeSize = b1.size();
      ASKAPCHECK(itsNeSize > 0,"Zero size NE");
      // first the size
      app->outputs[0].write((char *) &itsNeSize,sizeof(itsNeSize));
      // then the actual data
      app->outputs[0].write(b1.data(), b1.size());
  }


} // namespace
