/// @file CubeBuilder.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "CubeBuilder"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_CubeBuilder() {
        return std::string("CubeBuilder; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_CubeBuilder()

#include <vector>
#include <mutex>


#include <daliuge/DaliugeApplication.h>
#include <factory/CubeBuilder.h>
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

// params helpers
#include <measurementequation/SynthesisParamsHelper.h>
#include <measurementequation/ImageParamsHelper.h>
#include <measurementequation/ImageFFTEquation.h>
#include <parallel/GroupVisAggregator.h>


#include <gridding/IVisGridder.h>
#include <gridding/VisGridderFactory.h>


#include <fitting/Params.h>


#include <string.h>
#include <sys/time.h>




namespace askap {

    CubeBuilder::CubeBuilder(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {

    }


    CubeBuilder::~CubeBuilder() {
    }

    DaliugeApplication::ShPtr CubeBuilder::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return CubeBuilder::ShPtr(new CubeBuilder(raw_app));
    }

    int CubeBuilder::init(const char ***arguments) {

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

    int CubeBuilder::run() {


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



        // This is just to test whether this works at all.


        return 0;
    }


    void CubeBuilder::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void CubeBuilder::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }



} // namespace
