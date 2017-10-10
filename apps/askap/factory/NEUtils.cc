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


void NEUtils::receiveNE(askap::scimath::ImagingNormalEquations::ShPtr itsNE, dlg_app_info *app, int input) {
    ASKAPCHECK(itsNE, "NormalEquations not defined");
    size_t itsNESize;
    size_t n_read = app->inputs[input].read((char *) &itsNESize, sizeof(itsNESize));
    LOFAR::BlobString b1;
    b1.resize(itsNESize);
    n_read = app->inputs[input].read(b1.data(), itsNESize);

    ASKAPCHECK(n_read == itsNESize, "Unable to read NE of expected size");

    LOFAR::BlobIBufString bib(b1);
    LOFAR::BlobIStream bis(bib);
    bis >> *itsNE;

  }
  void NEUtils::sendNE(askap::scimath::ImagingNormalEquations::ShPtr itsNe, dlg_app_info *app, int output ) {

      ASKAPCHECK(itsNe, "NormalEquations not defined");

      LOFAR::BlobString b1;
      LOFAR::BlobOBufString bob(b1);
      LOFAR::BlobOStream bos(bob);
      bos << *itsNe;
      size_t itsNeSize = b1.size();
      ASKAPCHECK(itsNeSize > 0,"Zero size NE");
      // first the size
      app->outputs[output].write((char *) &itsNeSize,sizeof(itsNeSize));
      // then the actual data
      app->outputs[output].write(b1.data(), b1.size());
  }
  void NEUtils::sendParams(askap::scimath::Params::ShPtr Params,dlg_app_info *app, int output) {

    LOFAR::BlobString b1;
    LOFAR::BlobOBufString bob(b1);
    LOFAR::BlobOStream bos(bob);

    bos << *Params;

    size_t ParamsSize = b1.size();
    ASKAPCHECK(ParamsSize > 0,"Zero size NE");
    // first the size
    app->outputs[output].write((char *) &ParamsSize,sizeof(ParamsSize));
    // then the actual data
    app->outputs[output].write(b1.data(), b1.size());

  }
  void NEUtils::receiveParams(askap::scimath::Params::ShPtr Params, dlg_app_info *app, int input) {
      ASKAPCHECK(Params, "Params not defined");
      size_t ParamsSize;
      size_t n_read = app->inputs[input].read((char *) &ParamsSize, sizeof(ParamsSize));
      LOFAR::BlobString b1;
      b1.resize(ParamsSize);
      n_read = app->inputs[input].read(b1.data(), ParamsSize);

      ASKAPCHECK(n_read == ParamsSize, "Unable to read Params of expected size");

      LOFAR::BlobIBufString bib(b1);
      LOFAR::BlobIStream bis(bib);
      bis >> *Params;

    }
  LOFAR::ParameterSet NEUtils::addMissingParameters(LOFAR::ParameterSet& parset) {



      // Need to get some information from the input dataset
      // this is done in "prepare" in AdviseDI - need to get the minimum
      // set - or just throw an exception and make the user add
      // the info ....

      // test for missing image-specific parameters:

      // these parameters can be set globally or individually

      bool cellsizeNeeded = false;
      bool shapeNeeded = false;
      bool directionNeeded = true;

      int nTerms = 1;

      string param;

      const vector<string> imageNames = parset.getStringVector("Images.Names", false);

      param = "Images.direction";

      if ( !parset.isDefined(param) ) {
          directionNeeded = true;
      }
      else {
          directionNeeded = false;
      }
      param = "Images.restFrequency";

      if ( !parset.isDefined(param) ) {
          std::ostringstream pstr;
          // Only J2000 is implemented at the moment.
          pstr<<"HI";

          parset.add(param, pstr.str().c_str());
      }

      for (size_t img = 0; img < imageNames.size(); ++img) {

          param = "Images."+imageNames[img]+".cellsize";
          if ( !parset.isDefined(param) ) {
              cellsizeNeeded = true;
          }
          else {
               param = "Images.cellsize";
               if (!parset.isDefined(param) ) {
                   const vector<string> cellSizeVector = parset.getStringVector("Images.cellsize");
                   std::ostringstream pstr;
                   pstr<<"["<< cellSizeVector[0].c_str() <<"arcsec,"<<cellSizeVector[1].c_str() <<"arcsec]";

                   parset.add(param, pstr.str().c_str());
               }
          }
          param = "Images."+imageNames[img]+".shape";
          if ( !parset.isDefined(param) ) shapeNeeded = true;

          param = "Images."+imageNames[img]+".frequency";

          if ( !parset.isDefined(param) ) {

              ASKAPTHROW(std::runtime_error,"Frequency not in parset");

          }
          param ="Images."+imageNames[img]+".direction";
          if ( !parset.isDefined(param) && directionNeeded) {

              ASKAPTHROW(std::runtime_error,"direction not in parset");
          }
          else if (!parset.isDefined(param) && !directionNeeded) {

              const vector<string> directionVector = parset.getStringVector("Images.direction");

              std::ostringstream pstr;
              pstr<<"["<< directionVector[0].c_str() <<","<<directionVector[1].c_str() <<"," << directionVector[2].c_str() << "]";
              parset.add(param, pstr.str().c_str());


          }
          param = "Images."+imageNames[img]+".nterms"; // if nterms is set, store it for later
          if (parset.isDefined(param)) {
              if ((nTerms>1) && (nTerms!=parset.getInt(param))) {
                std::cerr << "Imaging with different nterms may not work" << std::endl;
              }
              nTerms = parset.getInt(param);
          }
          param = "Images."+imageNames[img]+".nchan";
          if ( !parset.isDefined(param)) {
              std::cerr << "Param not found: " << param << std::cerr;
          }
      }

      if (nTerms > 1) { // check required MFS parameters
          param = "visweights"; // set to "MFS" if unset and nTerms > 1
          if (!parset.isDefined(param)) {
              std::ostringstream pstr;
              pstr<<"MFS";
              std::cout <<  "  Advising on parameter " << param <<": " << pstr.str().c_str() << std::endl;
              parset.add(param, pstr.str().c_str());
          }

          param = "visweights.MFS.reffreq"; // set to average frequency if unset and nTerms > 1
          if ((parset.getString("visweights")=="MFS")) {
              if (!parset.isDefined(param)) {
                  ASKAPTHROW(std::runtime_error,"MFS reference frequency not in parset");
              }

          }
      }

      // test for general missing parameters:
      if ( cellsizeNeeded && !parset.isDefined("nUVWMachines") ) {

      } else if ( cellsizeNeeded && !parset.isDefined("Images.cellsize") ) {

      } else if ( shapeNeeded && !parset.isDefined("Images.shape") ) {

      }
      std::cout << "Done adding missing params " << std::endl;

      return parset;
  }
  std::vector<std::string> NEUtils::getDatasets(const LOFAR::ParameterSet& parset)
  {
      if (parset.isDefined("dataset") && parset.isDefined("dataset0")) {
          ASKAPTHROW(std::runtime_error,
              "Both dataset and dataset0 are specified in the parset");
      }

      // First look for "dataset" and if that does not exist try "dataset0"
      vector<string> ms;
      if (parset.isDefined("dataset")) {
          ms = parset.getStringVector("dataset", true);
      } else {
          string key = "dataset0";   // First key to look for
          long idx = 0;
          while (parset.isDefined(key)) {
              const string value = parset.getString(key);
              ms.push_back(value);

              LOFAR::ostringstream ss;
              ss << "dataset" << idx + 1;
              key = ss.str();
              ++idx;
          }
      }

      return ms;
  }


} // namespace
