/// @file SpectralCube.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "SpectralCube"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_SpectralCube() {
        return std::string("SpectralCube; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_SpectralCube()

#include <vector>
#include <mutex>


#include <daliuge/DaliugeApplication.h>
#include <factory/SpectralCube.h>
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



#include <string.h>
#include <sys/time.h>

#include <iostream>
#include <string>




ASKAP_LOGGER(logger, ".SpectralCube");

namespace askap {

    SpectralCube::SpectralCube(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
      ASKAPLOG_INFO_STR(logger, "Initialised cube builder - UID is " << raw_app->uid);

      itsChan = NEUtils::getChan(raw_app->uid);


    }


    SpectralCube::~SpectralCube() {
    }

    DaliugeApplication::ShPtr SpectralCube::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return SpectralCube::ShPtr(new SpectralCube(raw_app));
    }

    int SpectralCube::init(const char ***arguments) {

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

    int SpectralCube::run() {


#ifndef ASKAP_PATCHED
        static std::mutex safety;
#endif // ASKAP_PATCHED

        // Lets get the key-value-parset
        ASKAP_LOGGER(logger, ".run");
        char buf[64*1024];

        size_t n_read = input("Config").read(buf, 64*1024);

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

        // Actually there should be no model on input .... it should always be empty
        // it is my job to fill it.
        this->itsModel.reset(new scimath::Params());
        NEUtils::receiveParams(itsModel, input("Model"));
        //
        vector<string> images=itsModel->names();

        for (vector<string>::const_iterator it=images.begin(); it !=images.end(); it++) {
          ASKAPLOG_INFO_STR(logger, "Model contains "<< *it);


        }
        // sort out the cube ....
        // get this from the parset?
        // essentially need to get the info from some sort of "prepare" functionality
        //

        // FIXME: put prepare functionality either here or in utils ....

        //

        casa::Double baseFrequency = 1E9;
        casa::Double chanWidth = 1E5;
        casa::Int nchanCube = 8;

        casa::Double channelFrequency = baseFrequency + itsChan*chanWidth;



        casa::Quantity f0(baseFrequency,"Hz");
    /// The width of a channel. THis does <NOT> take account of the variable width
    /// of Barycentric channels
        casa::Quantity freqinc(chanWidth,"Hz");



        std::string img_name = "image";
        std::string psf_name = "psf";
        std::string residual_name = "residual";
        std::string weights_name = "weights";

        if (itsChan == 0)  { // only channel 0 builds the cubes
          ASKAPLOG_DEBUG_STR(logger,"Configuring Spectral Cube");
          ASKAPLOG_DEBUG_STR(logger,"nchan: " << nchanCube << " base f0: " << f0.getValue("MHz") << " MHz "
          << " width: " << freqinc.getValue("MHz"));

          itsImageCube.reset(new cp::CubeBuilder(itsParset, nchanCube, f0, freqinc,img_name));
          itsPSFCube.reset(new cp::CubeBuilder(itsParset, nchanCube, f0, freqinc, psf_name));
          itsResidualCube.reset(new cp::CubeBuilder(itsParset, nchanCube, f0, freqinc, residual_name));
          itsWeightsCube.reset(new cp::CubeBuilder(itsParset, nchanCube, f0, freqinc, weights_name));
        }
        else {
          itsImageCube.reset(new cp::CubeBuilder(itsParset, img_name));
          itsPSFCube.reset(new cp::CubeBuilder(itsParset,  psf_name));
          itsResidualCube.reset(new cp::CubeBuilder(itsParset,  residual_name));
          itsWeightsCube.reset(new cp::CubeBuilder(itsParset, weights_name));
        }

        handleImageParams();


        return 0;
    }


    void SpectralCube::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void SpectralCube::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }

    void SpectralCube::handleImageParams()
    {


        // Pre-conditions
        ASKAPCHECK(itsModel->has("image.cont"), "Params are missing model parameter");
        ASKAPCHECK(itsModel->has("psf.cont"), "Params are missing psf parameter");
        ASKAPCHECK(itsModel->has("residual.cont"), "Params are missing residual parameter");
        ASKAPCHECK(itsModel->has("weights.cont"), "Params are missing weights parameter");

/*
        if (itsParset.getBool("restore", false)) {
            // Record the restoring beam
            const askap::scimath::Axes &axes = params->axes("image.slice");
            recordBeam(axes, chan);
            storeBeam(chan);
        }
*/
        // Write image
        {
            ASKAPLOG_INFO_STR(logger,"Writing model for (local) channel " << itsChan);
            const casa::Array<double> imagePixels(itsModel->value("image.cont"));
            casa::Array<float> floatImagePixels(imagePixels.shape());
            casa::convertArray<float, double>(floatImagePixels, imagePixels);
            itsImageCube->writeSlice(floatImagePixels, itsChan);
        }

        // Write PSF
        {
            ASKAPLOG_INFO_STR(logger,"Writing PSF");
            const casa::Array<double> imagePixels(itsModel->value("psf.cont"));
            casa::Array<float> floatImagePixels(imagePixels.shape());
            casa::convertArray<float, double>(floatImagePixels, imagePixels);
            itsPSFCube->writeSlice(floatImagePixels, itsChan);
        }

        // Write residual
        {
            ASKAPLOG_INFO_STR(logger,"Writing Residual");
            const casa::Array<double> imagePixels(itsModel->value("residual.cont"));
            casa::Array<float> floatImagePixels(imagePixels.shape());
            casa::convertArray<float, double>(floatImagePixels, imagePixels);
            itsResidualCube->writeSlice(floatImagePixels, itsChan);
        }

        // Write weights
        {
            ASKAPLOG_INFO_STR(logger,"Writing Weights");
            const casa::Array<double> imagePixels(itsModel->value("weights.cont"));
            casa::Array<float> floatImagePixels(imagePixels.shape());
            casa::convertArray<float, double>(floatImagePixels, imagePixels);
            itsWeightsCube->writeSlice(floatImagePixels, itsChan);
        }

/*
        if (itsParset.getBool("restore", false)) {

            if (itsDoingPreconditioning) {
                // Write preconditioned PSF image
                {
                    ASKAPLOG_INFO_STR(logger,"Writing preconditioned PSF");
                    const casa::Array<double> imagePixels(params->value("psf.image.slice"));
                    casa::Array<float> floatImagePixels(imagePixels.shape());
                    casa::convertArray<float, double>(floatImagePixels, imagePixels);
                    itsPSFimageCube->writeSlice(floatImagePixels, chan);
                }
            // Write Restored image
            {
                ASKAPLOG_INFO_STR(logger,"Writing Restored Image");
                const casa::Array<double> imagePixels(itsModel->value("image.slice"));
                casa::Array<float> floatImagePixels(imagePixels.shape());
                casa::convertArray<float, double>(floatImagePixels, imagePixels);
                itsRestoredCube->writeSlice(floatImagePixels, itsChan);
            }
        }

*/

    }




} // namespace
