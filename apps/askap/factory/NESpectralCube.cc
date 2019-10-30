/// @file NESpectralCube.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a method to generate a cube of NormalEquation slices

#define ASKAP_PACKAGE_NAME "NESpectralCube"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_NESpectralCube() {
        return std::string("NESpectralCube; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_NESpectralCube()

#include <vector>
#include <mutex>
#include <regex>



#include <daliuge/DaliugeApplication.h>
#include <factory/NESpectralCube.h>
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

// Data accessors
#include <dataaccess/TableConstDataSource.h>
#include <dataaccess/IConstDataIterator.h>
#include <dataaccess/IDataConverter.h>
#include <dataaccess/IDataSelector.h>
#include <dataaccess/IDataIterator.h>
#include <dataaccess/SharedIter.h>

// Image accessors
#include <imageaccess/ImageAccessFactory.h>

// params helpers
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/ImageParamsHelper.h>
#include <measurementequation/ImageFFTEquation.h>
#include <parallel/GroupVisAggregator.h>


#include <gridding/IVisGridder.h>
#include <gridding/VisGridderFactory.h>


#include <utils/PolConverter.h>

// casacore

#include <casacore/casa/Arrays/IPosition.h>
#include <casacore/coordinates/Coordinates/SpectralCoordinate.h>
#include <casacore/coordinates/Coordinates/DirectionCoordinate.h>
#include <casacore/coordinates/Coordinates/StokesCoordinate.h>
#include <casacore/coordinates/Coordinates/CoordinateSystem.h>
#include <casacore/measures/Measures/Stokes.h>
#include <casacore/images/Images/PagedImage.h>
#include <casacore/casa/Quanta/Unit.h>
#include <casacore/casa/Quanta/QC.h>

#include <fitting/Params.h>
#include <imageaccess/ImageAccessFactory.h>


#include <string.h>
#include <sys/time.h>

#include <iostream>
#include <string>




ASKAP_LOGGER(logger, ".NESpectralCube");

namespace askap {

    NESpectralCube::NESpectralCube(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
      ASKAPLOG_INFO_STR(logger, "Initialised cube builder - UID is " << raw_app->uid);

      itsChan = NEUtils::getChan(raw_app->uid);


    }


    NESpectralCube::~NESpectralCube() {
    }

    DaliugeApplication::ShPtr NESpectralCube::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return NESpectralCube::ShPtr(new NESpectralCube(raw_app));
    }

    int NESpectralCube::init(const char ***arguments) {

        // Argument parsing is not working as yet

        char *parset_filename = 0;
        while (1) {

            const char **param = *arguments;

            // Sentinel
            if (param == NULL) {
                break;
            }
            // any params I might need go here:
            // filename:
            // no longer required as input comes from daliuge now
            //if (strcmp(param[0], "parset_filename") == 0) {
            //    parset_filename = strdup(param[1]);
            //}

            arguments++;
        }


        return 0;
    }

    int NESpectralCube::run() {


      #ifndef ASKAP_PATCHED
              static std::mutex safety;
      #endif // ASKAP_PATCHED

        // Lets get the key-value-parset
        ASKAP_LOGGER(logger, ".run");
        char buf[64*1024];
        size_t n_read = 0;
        try {
          n_read = input("Config").read(buf, 64*1024);
        }
        catch (std::runtime_error)
        {
          ASKAPLOG_INFO_STR(logger, "No config file available");
          return -1;
        }

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        this->itsParset = parset.makeSubset("Cimager.");

        // we need to fill the local parset with parameters that maybe missing
        //
        try {
#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED
            this->itsParset = NEUtils::addMissingParameters(this->itsParset);
        }
        catch (std::runtime_error)
        {
            return -1;
        }

        this->itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations());

        try {
            NEUtils::receiveNE(itsNe, input("Normal"));
        }
        catch (std::runtime_error) {
            ASKAPLOG_INFO_STR(logger, "Failed to receive NE");
            return -1;
        }


        casacore::Double baseFrequency = NEUtils::getFrequency(itsParset,0);
        casacore::Double chanWidth = NEUtils::getChanWidth(itsParset,0);
        casacore::Int nchanCube = NEUtils::getNChan(itsParset);
        casacore::Double channelFrequency = NEUtils::getFrequency(itsParset,itsChan);

        casacore::Quantity f0(baseFrequency,"Hz");
      /// The width of a channel. THis does <NOT> take account of the variable width
      /// of Barycentric channels
        casacore::Quantity freqinc(chanWidth,"Hz");

        std::vector<std::string> toFitParams = itsNe->unknowns();
        std::vector<std::string>::const_iterator iterCol = toFitParams.begin();

        for (; iterCol != toFitParams.end(); iterCol++) {

            ASKAPLOG_INFO_STR(logger,"Param name: " << *iterCol);
            /// FIXME: eventually I'll put this in a cube ... but for now
            if (itsChan >= 0) {


                string img_name = *iterCol + ".chan." + std::to_string(itsChan);
                string img_name_arr =  *iterCol + ".chan." + std::to_string(itsChan) + ".data";

                ASKAPLOG_INFO_STR(logger,"Image name: " << img_name);
                const scimath::ImagingNormalEquations &other =
                                   dynamic_cast<const scimath::ImagingNormalEquations&>(*itsNe);

                // check dataVector
                if (other.dataVector().find(*iterCol) == other.dataVector().end()) {
                // no new data for this parameter
                  continue;
                }

                // record how data are updated
                enum updateType_t{ overwrite, add, linmos };
                int updateType;

                // check coordinate systems and record how data are updated

                ASKAPDEBUGASSERT(other.dataVector().find(*iterCol) != other.dataVector().end());

                const casacore::Vector<double> &newDataVec = other.dataVector().find(*iterCol)->second;
                const casacore::CoordinateSystem &newCoordSys = other.coordSys().find(*iterCol)->second;
                const casacore::IPosition &newShape = other.shape().find(*iterCol)->second;
                /* for writing out as image */
                casacore::Array<double> newDataArr(newShape,newDataVec.data());

                casacore::write_array(newDataArr,img_name_arr);

                // boost::shared_ptr<accessors::IImageAccess> itsImageAccessor;

                // itsImageAccessor = accessors::imageAccessFactory(parset);

                // itsImageAccessor->create(img_name, newShape, newCoordSys);

                //itsImageAccessor->write(img_name,newDataArr);

            }


//            handleImageParams();
        }




        return 0;
    }


    void NESpectralCube::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void NESpectralCube::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }

    void NESpectralCube::handleImageParams()
    {
      /*
        ASKAPLOG_INFO_STR(logger,"In handleImageParams");

        vector<string> images=itsModel->names();
        try {
          std::smatch m;
          std::regex peak_residual("^peak_residual");
          std::regex residual("^residual");
          std::regex image("^image");
          std::regex psf("^psf");
          std::regex weights("^weights");



        for (vector<string>::const_iterator it=images.begin(); it !=images.end(); it++) {
          ASKAPLOG_INFO_STR(logger, "Will parse for an image name "<< *it);
          if (std::regex_search(*it,m,peak_residual)) {
            continue;
          }


        // Write image
          if (std::regex_search(*it,m,image))
          {
            ASKAPLOG_INFO_STR(logger, "Matched image and writing "<< *it);
            const casacore::Array<double> imagePixels(itsModel->value(*it));
            casacore::Array<float> floatImagePixels(imagePixels.shape());
            casacore::convertArray<float, double>(floatImagePixels, imagePixels);
            itsImageCube->writeSlice(floatImagePixels, itsChan);
          }

        // Write PSF
          if (std::regex_search(*it,m,psf))
          {
            ASKAPLOG_INFO_STR(logger,"Matched PSF and writing " << *it);
            const casacore::Array<double> imagePixels(itsModel->value(*it));
            casacore::Array<float> floatImagePixels(imagePixels.shape());
            casacore::convertArray<float, double>(floatImagePixels, imagePixels);
            itsPSFCube->writeSlice(floatImagePixels, itsChan);
          }

        // Write residual
          if (std::regex_search(*it,m,residual))
          {
            ASKAPLOG_INFO_STR(logger,"Matched residual and writing " << *it);
            const casacore::Array<double> imagePixels(itsModel->value(*it));
            casacore::Array<float> floatImagePixels(imagePixels.shape());
            casacore::convertArray<float, double>(floatImagePixels, imagePixels);
            itsResidualCube->writeSlice(floatImagePixels, itsChan);
          }

        // Write weights
          if (std::regex_search(*it,m,weights))
          {
            ASKAPLOG_INFO_STR(logger,"Matched weights and writing " << *it);
            const casacore::Array<double> imagePixels(itsModel->value(*it));
            casacore::Array<float> floatImagePixels(imagePixels.shape());
            casacore::convertArray<float, double>(floatImagePixels, imagePixels);
            itsWeightsCube->writeSlice(floatImagePixels, itsChan);
          }
          // Write restored
            // if (std::regex_search(*it,restored))
            // {
            //   ASKAPLOG_INFO_STR(logger,"Writing " << *it);
            //   const casacore::Array<double> imagePixels(itsModel->value(*it));
            //   casacore::Array<float> floatImagePixels(imagePixels.shape());
            //   casacore::convertArray<float, double>(floatImagePixels, imagePixels);
            //   itsRestoredCube->writeSlice(floatImagePixels, itsChan);
            // }
        }
      }
      catch (std::regex_error &e) {
        std::cout << "regex_error caught: " << e.what() << '\n';
      }
      catch (...) {
        std::cout << "Unknown exception caught: " << '\n';
      }
        /*
        if (itsParset.getBool("restore", false)) {

            if (itsDoingPreconditioning) {
                // Write preconditioned PSF image
                {
                    ASKAPLOG_INFO_STR(logger,"Writing preconditioned PSF");
                    const casacore::Array<double> imagePixels(params->value("psf.image.slice"));
                    casacore::Array<float> floatImagePixels(imagePixels.shape());
                    casacore::convertArray<float, double>(floatImagePixels, imagePixels);
                    itsPSFimageCube->writeSlice(floatImagePixels, chan);
                }
            // Write Restored image
            {
                ASKAPLOG_INFO_STR(logger,"Writing Restored Image");
                const casacore::Array<double> imagePixels(itsModel->value("image.slice"));
                casacore::Array<float> floatImagePixels(imagePixels.shape());
                casacore::convertArray<float, double>(floatImagePixels, imagePixels);
                itsRestoredCube->writeSlice(floatImagePixels, itsChan);
            }
        }

*/

    }




} // namespace
