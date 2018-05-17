/// @file SoadNE.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// IMplements an ASKAPSoft Restore solver. This essentially takes a NormalEquation and
/// a set of "params" and creates a restored image.
///
// for logging
#define ASKAP_PACKAGE_NAME "RestoreSolver"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_RestoreSolver() {
        return std::string("RestoreSolver");
    }


} // namespace askap

/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_RestoreSolver()

#include <vector>
#include <mutex>



#include <daliuge/DaliugeApplication.h>
#include <factory/RestoreSolver.h>
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
#include <measurementequation/ImageRestoreSolver.h>



#include <fitting/Params.h>
#include <fitting/Solver.h>

#include <string.h>
#include <sys/time.h>




namespace askap {



    RestoreSolver::RestoreSolver(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
    }


    RestoreSolver::~RestoreSolver() {
    }

    DaliugeApplication::ShPtr RestoreSolver::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return RestoreSolver::ShPtr(new RestoreSolver(raw_app));
    }

    int RestoreSolver::init(const char ***arguments) {

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

    int RestoreSolver::run() {

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
            this->itsModel.reset(new scimath::Params());
            try {
              NEUtils::receiveParams(itsModel, input("Solved Model"));
              ASKAPLOG_INFO_STR(logger, "Received model");
            }
            catch (std::runtime_error) {
              ASKAPLOG_WARN_STR(logger," Failed to receive model setting");
              return -1;
            }
        }

        // Now we need to instantiate and initialise the solver from the parset
        this->itsSolver = synthesis::ImageSolverFactory::make(this->itsParset);

        this->itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations());

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

          if (itsParset.getBool("restore", false)) {
            // Now we need to build the restore solver using this as the template_solver
            boost::shared_ptr<synthesis::ImageRestoreSolver>
            ir = synthesis::ImageRestoreSolver::createSolver(itsParset.makeSubset("restore."));
            ASKAPDEBUGASSERT(ir);
            ASKAPDEBUGASSERT(itsSolver);
            // configure restore solver the same way as normal imaging solver
            boost::shared_ptr<synthesis::ImageSolver>
            template_solver = boost::dynamic_pointer_cast<synthesis::ImageSolver>(itsSolver);
            ASKAPDEBUGASSERT(template_solver);
            synthesis::ImageSolverFactory::configurePreconditioners(itsParset, ir);
            ir->configureSolver(*template_solver);
            ir->copyNormalEquations(*template_solver);

            ASKAPLOG_INFO_STR(logger, "(Restoring) Solving Normal Equations");
            askap::scimath::Quality q;


            ir->solveNormalEquations(*itsModel, q);
            vector<string> resultimages=itsModel->names();

            for (vector<string>::const_iterator ci=resultimages.begin(); ci!=resultimages.end(); ++ci) {

              ASKAPLOG_INFO_STR(logger, "Restored image " << *ci);

            }
            ASKAPDEBUGASSERT(itsModel);  
          }
          NEUtils::sendParams(itsModel, output("Restored Model"));
        }

        return 0;
    }


    void RestoreSolver::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void RestoreSolver::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }


} // namespace
