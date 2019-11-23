/// @file SoadNE.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// IMplements an ASKAPSoft solver. This essentially takes a NormalEquation and generates a
/// a set of "params" usually via a minor cycle deconvolution.
///
// for logging
#define ASKAP_PACKAGE_NAME "SolveNE"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_SolveNE() {
        return std::string("SolveNE");
    }


} // namespace askap

/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_SolveNE()

#include <vector>
#include <mutex>



#include <daliuge/DaliugeApplication.h>
#include <factory/SolveNE.h>
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

// Solver stuff

#include <measurementequation/ImageSolverFactory.h>



#include <fitting/Params.h>
#include <fitting/Solver.h>

#include <string.h>
#include <sys/time.h>




namespace askap {



    SolveNE::SolveNE(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
    }


    SolveNE::~SolveNE() {
    }

    DaliugeApplication::ShPtr SolveNE::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return SolveNE::ShPtr(new SolveNE(raw_app));
    }

    int SolveNE::init(const char ***arguments) {

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

    int SolveNE::run() {

#ifndef ASKAP_PATCHED
        static std::mutex safety;
#endif // ASKAP_PATCHED

        // Lets get the key-value-parset
        ASKAP_LOGGER(logger, ".run");

        // lets open the input and read it
        char buf[64*1024];
        size_t n_read = input("Config").read(buf, 64*1024);

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        this->itsParset = parset.makeSubset("Cimager.");

        try {
            this->itsParset = NEUtils::addMissingParameters(this->itsParset);
        }
        catch (std::runtime_error)
        {
            return -1;
        }

        // Actually there should be no model on input .... it should always be empty
        // it is my job to fill it.

        this->itsModel.reset(new scimath::Params());
        {

#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED

            askap::synthesis::SynthesisParamsHelper::setUpImages(itsModel,
                                  this->itsParset.makeSubset("Images."));

            // Now we need to instantiate and initialise the solver from the parset
            this->itsSolver = synthesis::ImageSolverFactory::make(this->itsParset);

            this->itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations());
        }


        NEUtils::receiveNE(itsNe, input("Normal"));

        std::vector<std::string> toFitParams = itsNe->unknowns();
        std::vector<std::string>::const_iterator iter2 = toFitParams.begin();

        for (; iter2 != toFitParams.end(); iter2++) {

            ASKAPLOG_INFO_STR(logger,"Param name: " << *iter2);

        }

        // Now we need to instantiate and initialise the solver
        {
#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED

            itsSolver->init();
            itsSolver->addNormalEquations(*itsNe);

            ASKAPLOG_INFO_STR(logger, "Solving Normal Equations");
            askap::scimath::Quality q;

            ASKAPDEBUGASSERT(itsModel);
            itsSolver->solveNormalEquations(*itsModel, q);
            ASKAPLOG_INFO_STR(logger, "Solved normal equations");
            // need to increment a solverCount so anything outside the loop
            // knows what majorCycle iteration this comes from
            if (itsModel->has("iteration")) {
                int iteration = itsModel->scalarValue("iteration");
                iteration++;
                itsModel->update("iteration",iteration);
            }
            else {
              int iteration = 1;
              itsModel->add("iteration",iteration);
            }
            ASKAPLOG_INFO_STR(logger, "Sending data to port 'Model'");
            NEUtils::sendParams(itsModel, output("Model"));
        }

        return 0;
    }


    void SolveNE::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void SolveNE::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }


} // namespace
