/// @file SpectralCube.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "InitSpectralCube"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_InitSpectralCube() {
        return std::string("InitSpectralCube; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_InitSpectralCube()

#include <vector>
#include <mutex>


#include <daliuge/DaliugeApplication.h>
#include <factory/InitSpectralCube.h>
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




ASKAP_LOGGER(logger, ".InitSpectralCube");

namespace askap {

    InitSpectralCube::InitSpectralCube(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
      ASKAPLOG_INFO_STR(logger, "Initialised cube builder - UID is " << raw_app->uid);



    }


    InitSpectralCube::~InitSpectralCube() {
    }

    DaliugeApplication::ShPtr InitSpectralCube::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return InitSpectralCube::ShPtr(new InitSpectralCube(raw_app));
    }

    int InitSpectralCube::init(const char ***arguments) {

        // Argument parsing is not working as yet

        char *parset_filename = 0;
        while (1) {

            const char **param = *arguments;

            // Sentinel
            if (param == NULL) {
                break;
            }

            arguments++;
        }


        return 0;
    }

    int InitSpectralCube::run() {


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
            ASKAPLOG_INFO_STR(logger, "Exception thrown in addMissingParameters");
            return -1;
        }
        ASKAPLOG_INFO_STR(logger, "Getting base frequency");
        casacore::Double baseFrequency = NEUtils::getFrequency(itsParset,0);
        ASKAPLOG_INFO_STR(logger, "Getting chanwidth");
        casacore::Double chanWidth = NEUtils::getChanWidth(itsParset,0);
        ASKAPLOG_INFO_STR(logger, "Getting nchan");
        casacore::Int nchanCube = NEUtils::getNChan(itsParset);


        casacore::Quantity f0(baseFrequency,"Hz");
    /// The width of a channel. THis does <NOT> take account of the variable width
    /// of Barycentric channels
        casacore::Quantity freqinc(chanWidth,"Hz");

    /// these names need to match the spectral cube names - maybe put them in a header?

        std::string img_name = "image";
        std::string psf_name = "psf";
        std::string residual_name = "residual";
        std::string weights_name = "weights";
        std::string restored_name = "restored";


        ASKAPLOG_INFO_STR(logger,"Configuring Spectral Cube");
        ASKAPLOG_INFO_STR(logger,"nchan: " << nchanCube << " base f0: " << f0.getValue("MHz") << " MHz "
        << " width: " << freqinc.getValue("MHz"));

        itsImageCube.reset(new cp::CubeBuilder<casacore::Float> (itsParset, nchanCube, f0, freqinc,img_name));
        itsPSFCube.reset(new cp::CubeBuilder<casacore::Float> (itsParset, nchanCube, f0, freqinc, psf_name));
        itsResidualCube.reset(new cp::CubeBuilder<casacore::Float> (itsParset, nchanCube, f0, freqinc, residual_name));
        itsWeightsCube.reset(new cp::CubeBuilder<casacore::Float> (itsParset, nchanCube, f0, freqinc, weights_name));

// Need to add the restore cube test and build here

        if (itsParset.getBool("restore", false)) {
          itsRestoredCube.reset(new cp::CubeBuilder<casacore::Float> (itsParset, nchanCube, f0, freqinc, restored_name));
        }

        return 0;
    }


    void InitSpectralCube::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void InitSpectralCube::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }





} // namespace
