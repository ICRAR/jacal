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
#include <parallel/SynParallel.h>
#include <parallel/GroupVisAggregator.h>


#include <gridding/IVisGridder.h>
#include <gridding/VisGridderFactory.h>
#include <fitting/ImagingNormalEquations.h>

#include <fitting/Params.h>


#include <string.h>
#include <sys/time.h>

#include <boost/regex.hpp>
#include <casacore/casa/BasicSL.h>
#include <casacore/casa/aips.h>
#include <casacore/casa/OS/Timer.h>
#include <casacore/ms/MeasurementSets/MeasurementSet.h>
#include <casacore/ms/MeasurementSets/MSColumns.h>
#include <casacore/ms/MSOper/MSReader.h>
#include <casacore/casa/Arrays/ArrayIO.h>
#include <casacore/casa/iostream.h>
#include <casacore/casa/namespace.h>
#include <casacore/casa/Quanta/MVTime.h>



namespace askap {

int NEUtils::getNChan(LOFAR::ParameterSet& parset) {
  // Read from the configruation the list of datasets to process
  const vector<string> ms = getDatasets(parset);

  const casa::MeasurementSet in(ms[0]);

  return casa::ROScalarColumn<casa::Int>(in.spectralWindow(),"NUM_CHAN")(0);

}

double NEUtils::getFrequency(LOFAR::ParameterSet& parset, int chan, bool barycentre) {

  // Read from the configruation the list of datasets to process
  const vector<string> ms = getDatasets(parset);


  const casa::MeasurementSet in(ms[0]);
  const casa::ROMSColumns srcCols(in);

  const casa::ROMSSpWindowColumns& sc = srcCols.spectralWindow();
  const casa::ROMSFieldColumns& fc = srcCols.field();
  const casa::ROMSObservationColumns& oc = srcCols.observation();
  const casa::ROMSAntennaColumns& ac = srcCols.antenna();
  const casa::ROArrayColumn<casa::Double> times = casa::ROArrayColumn<casa::Double>(oc.timeRange());
  const casa::ROArrayColumn<casa::Double> ants = casa::ROArrayColumn<casa::Double>(ac.position());
  const casa::uInt thisRef = casa::ROScalarColumn<casa::Int>(in.spectralWindow(),"MEAS_FREQ_REF")(0);

  casa::MVDirection Tangent;
  casa::Vector<casa::MDirection> DirVec;
  casa::MVEpoch Epoch;
  casa::MPosition Position;

  DirVec = fc.phaseDirMeasCol()(0);
  Tangent = DirVec(0).getValue();

  // Read the position on Antenna 0
  Array<casa::Double> posval;
  ants.get(0,posval,true);
  vector<double> pval = posval.tovector();

  MVPosition mvobs(Quantity(pval[0], "m").getBaseValue(),
  Quantity(pval[1], "m").getBaseValue(),
  Quantity(pval[2], "m").getBaseValue());

  Position = MPosition(mvobs,casa::MPosition::ITRF);

  // Get the Epoch
  Array<casa::Double> tval;
  vector<double> tvals;

  times.get(0,tval,true);
  tvals = tval.tovector();
  double mjd = tvals[0]/(86400.);
  casa::MVTime dat(mjd);

  Epoch = MVEpoch(dat.day());
  int srow = sc.nrow()-1;
  if (barycentre == false) {
    return sc.chanFreq()(srow)(casa::IPosition(1, chan));
  }
  else {
    // need to put the barycentreing in here - the logic is all in the AdviseDI
  }


  return 1.0;

}

int NEUtils::getChan(char *uid) {

    // FIXME: make this more robust

    char *token, *string, *tofree;

    tofree = string = strdup(uid);
    assert(string != NULL);

    char * sessionID = strsep(&string, "_");
    char * logicalGraphID = strsep(&string, "_");
    char * contextID = strsep(&string, "_");

    string = strdup(contextID);

    char * branchID = strsep(&string,"/");

    char * chanNum = strsep(&string,"/");

    if (chanNum != NULL)
      return atoi(chanNum);
    else
      return -1;


}

void NEUtils::receiveNE(askap::scimath::ImagingNormalEquations::ShPtr itsNE, dlg_input_info &input) {
    ASKAPCHECK(itsNE, "NormalEquations not defined");
    size_t itsNESize;
    size_t n_read = input.read((char *) &itsNESize, sizeof(itsNESize));
    LOFAR::BlobString b1;
    b1.resize(itsNESize);
    n_read = input.read(b1.data(), itsNESize);

    ASKAPCHECK(n_read == itsNESize, "Unable to read NE of expected size");

    LOFAR::BlobIBufString bib(b1);
    LOFAR::BlobIStream bis(bib);
    bis >> *itsNE;

  }
  void NEUtils::sendNE(askap::scimath::ImagingNormalEquations::ShPtr itsNe, dlg_output_info &output) {

      ASKAPCHECK(itsNe, "NormalEquations not defined");

      LOFAR::BlobString b1;
      LOFAR::BlobOBufString bob(b1);
      LOFAR::BlobOStream bos(bob);
      bos << *itsNe;
      size_t itsNeSize = b1.size();
      ASKAPCHECK(itsNeSize > 0,"Zero size NE");
      // first the size
      output.write((char *) &itsNeSize,sizeof(itsNeSize));
      // then the actual data
      output.write(b1.data(), b1.size());
  }
  void NEUtils::sendParams(askap::scimath::Params::ShPtr Params, dlg_output_info &output) {

    LOFAR::BlobString b1;
    LOFAR::BlobOBufString bob(b1);
    LOFAR::BlobOStream bos(bob);

    bos << *Params;

    size_t ParamsSize = b1.size();
    ASKAPCHECK(ParamsSize > 0,"Zero size NE");
    // first the size
    output.write((char *) &ParamsSize,sizeof(ParamsSize));
    // then the actual data
    output.write(b1.data(), b1.size());

  }
  void NEUtils::receiveParams(askap::scimath::Params::ShPtr Params, dlg_input_info &input) {
      ASKAPCHECK(Params, "Params not defined");
      size_t ParamsSize;
      size_t n_read = input.read((char *) &ParamsSize, sizeof(ParamsSize));
      LOFAR::BlobString b1;
      b1.resize(ParamsSize);
      n_read = input.read(b1.data(), ParamsSize);

      if (n_read == ParamsSize) {


        LOFAR::BlobIBufString bib(b1);
        LOFAR::BlobIStream bis(bib);
        bis >> *Params;
      }


  }
  LOFAR::ParameterSet NEUtils::addMissingParameters(LOFAR::ParameterSet& parset) {



      // Need to get some information from the input dataset
      // this is done in "prepare" in AdviseDI - need to get the minimum
      // set - or just throw an exception and make the user add
      // the info ....

      // test for missing image-specific parameters:

      // these parameters can be set globally or individually

      ASKAP_LOGGER(logger, ".addMissingParameters")

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
              ASKAPLOG_WARN_STR(logger, "Frequency not in Parset and it needs to be");
              ASKAPTHROW(std::runtime_error,"Frequency not in parset");

          }
          param ="Images."+imageNames[img]+".direction";
          if ( !parset.isDefined(param) && directionNeeded) {

              ASKAPLOG_WARN_STR(logger, "Direction not in Parset and it needs to be");
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
                ASKAPLOG_WARN_STR(logger, "Imaging with different nterms may not work");
              }
              nTerms = parset.getInt(param);
          }
          param = "Images."+imageNames[img]+".nchan";
          if ( !parset.isDefined(param)) {
              ASKAPLOG_WARN_STR(logger, "Param not found: " << param);
          }
      }

      if (nTerms > 1) { // check required MFS parameters
          param = "visweights"; // set to "MFS" if unset and nTerms > 1
          if (!parset.isDefined(param)) {
              std::ostringstream pstr;
              pstr << "MFS";
              ASKAPLOG_INFO_STR(logger, "Advising on parameter " << param <<": " << pstr.str().c_str());
              parset.add(param, pstr.str().c_str());
          }

          param = "visweights.MFS.reffreq"; // set to average frequency if unset and nTerms > 1
          if ((parset.getString("visweights")=="MFS")) {
              if (!parset.isDefined(param)) {
                  ASKAPLOG_WARN_STR(logger, "Param not found: " << param << " and cannot be predicted");
                  ASKAPTHROW(std::runtime_error,"MFS reference frequency not in parset");
              }

          }
      }

      // test for general missing parameters:
      if ( cellsizeNeeded && !parset.isDefined("nUVWMachines") ) {

      } else if ( cellsizeNeeded && !parset.isDefined("Images.cellsize") ) {

      } else if ( shapeNeeded && !parset.isDefined("Images.shape") ) {

      }

      ASKAPLOG_DEBUG_STR(logger, "Done adding missing params");

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

  int NEUtils::getInput(dlg_app_info *app, const char* tag) {

    boost::regex exp1(tag);
    boost::cmatch what;

    for (int i = 0; i < app->n_inputs; i++) {
        if (boost::regex_search(app->inputs[i].name, what, exp1)) {
           return i;
        }

    }
    return -1;

  }

  vector<int> NEUtils::getInputs(dlg_app_info *app, const char* tag) {

    boost::regex exp1(tag);
    boost::cmatch what;
    vector<int> inputs;

    for (int i = 0; i < app->n_inputs; i++) {
  
      if (boost::regex_search(app->inputs[i].name, what, exp1)) {

        inputs.push_back(i);
      }

    }
    return inputs;

  }

  int NEUtils::getOutput(dlg_app_info *app, const char* tag) {


    boost::regex exp1(tag);
    boost::cmatch what;

    for (int i = 0; i < app->n_outputs; i++) {
        if (boost::regex_search(app->outputs[i].name, what, exp1)) {
           return i;
        }

    }
    return -1;

  }

  void NEUtils::readModels(const LOFAR::ParameterSet& parset, const scimath::Params::ShPtr &pModel)
  {

    ASKAP_LOGGER(logger, ".readModels");
    ASKAPCHECK(pModel, "model is not initialised prior to call to SynParallel::readModels");

    const std::vector<std::string> sources = parset.getStringVector("sources.names");
    std::set<std::string> loadedImageModels;
    for (size_t i=0; i<sources.size(); ++i) {
       const std::string modelPar = std::string("sources.")+sources[i]+".model";
       const std::string compPar = std::string("sources.")+sources[i]+".components";
       // check that only one is defined
       ASKAPCHECK(parset.isDefined(compPar) != parset.isDefined(modelPar),
            "The model should be defined with either image (via "<<modelPar<<") or components (via "<<
             compPar<<"), not both");
       //
         if (parset.isDefined(modelPar)) {
             const std::vector<std::string> vecModels = parset.getStringVector(modelPar);
             int nTaylorTerms = parset.getInt32(std::string("sources.")+sources[i]+".nterms",1);
             ASKAPCHECK(nTaylorTerms>0, "Number of Taylor terms is supposed to be a positive number, you gave "<<
                       nTaylorTerms);
             if (nTaylorTerms>1) {
                 ASKAPLOG_WARN_STR(logger,"Simulation from model presented by Taylor series (a.k.a. MFS-model) with "<<
                             nTaylorTerms<<" terms is not supported");
                 nTaylorTerms = 1;
             }
             ASKAPCHECK((vecModels.size() == 1) || (int(vecModels.size()) == nTaylorTerms),
                  "Number of model images given by "<<modelPar<<" should be either 1 or one per taylor term, you gave "<<
                  vecModels.size()<<" nTaylorTerms="<<nTaylorTerms);
             synthesis::ImageParamsHelper iph("image."+sources[i]);
             // for simulations we don't need cross-terms
             for (int order = 0; order<nTaylorTerms; ++order) {
                  if (nTaylorTerms > 1) {
                      // this is an MFS case, setup Taylor terms
                      iph.makeTaylorTerm(order);
                      ASKAPLOG_INFO_STR(logger,"Processing Taylor term "<<order);
                  }
                  std::string model = vecModels[0];
                  if (vecModels.size() == 1) {
                      // only base name is given, need to add taylor suffix
                      model += iph.suffix();
                  }

                  if (std::find(loadedImageModels.begin(),loadedImageModels.end(),model) != loadedImageModels.end()) {
                      ASKAPLOG_INFO_STR(logger, "Model " << model << " has already been loaded, reusing it for "<< sources[i]);
                      if (vecModels.size()!=1) {
                          ASKAPLOG_WARN_STR(logger, "MFS simulation will not work correctly if you specified the same model "<<
                               model<<" for multiple Taylor terms");
                      }
                  } else {
                      ASKAPLOG_INFO_STR(logger, "Adding image " << model << " as model for "<< sources[i]
                                         << ", parameter name: "<<iph.paramName() );
                      // need to patch model to append taylor suffix
                      synthesis::SynthesisParamsHelper::loadImageParameter(*pModel, iph.paramName(), model);
                      loadedImageModels.insert(model);
                  }
             }
         } else {
             // loop through components
             ASKAPLOG_INFO_STR(logger, "Adding components as model for "<< sources[i] );
             const vector<string> compList = parset.getStringVector(compPar);
             for (vector<string>::const_iterator cmp = compList.begin(); cmp != compList.end(); ++cmp) {
                  ASKAPLOG_INFO_STR(logger, "Loading component " << *cmp << " as part of the model for " << sources[i]);
                  synthesis::SynthesisParamsHelper::copyComponent(pModel, parset,*cmp,"sources.");
              }
         }
    }
    ASKAPLOG_INFO_STR(logger, "Successfully read models");
  }

} // namespace
