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
    std::string getAskapPackageVersion_() {
        return std::string("SolveNE");
    }


} // namespace askap

/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_SolveNE()

#include <iostream>
#include <vector>



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



    SolveNE::SolveNE() {
        //ASKAP_LOGGER(locallogger,"\t SolveNE -  default contructor\n");
        std::cout << "SolveNE -  default constructor" << std::endl;

    }


    SolveNE::~SolveNE() {
        //ASKAP_LOGGER(locallogger,"\t SolveNE -  default destructor\n");
        std::cout << "SolveNE -  default destructor" << std::endl;
    }

    DaliugeApplication::ShPtr SolveNE::createDaliugeApplication(const std::string &name)
    {
        // ASKAP_LOGGER(locallogger, ".create");
        std::cout << "createDaliugeApplication - Instantiating SolveNE" << std::endl;
        // ASKAPLOG_INFO_STR(locallogger,"createDaliugeApplication - Instantiating SolveNE");
        SolveNE::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new SolveNE());

        std::cout << "createDaliugeApplication - Created SolveNE DaliugeApplication instance " << std::endl;
        return ptr;

    }
    int SolveNE::init(dlg_app_info *app, const char ***arguments) {


        while (1) {

            const char **param = *arguments;

            // Sentinel
            if (param == NULL) {
                break;
            }

            arguments++;
        }

        app->data = malloc(sizeof(struct app_data));
        if (!app->data) {
            return 1;
        }


        return 0;
    }

    int SolveNE::run(dlg_app_info *app) {

        // Lets get the key-value-parset
        ASKAPLOG_INIT("");
        ASKAP_LOGGER(logger, ".run");

        // lets open the input and read it
        char buf[64*1024];
        size_t n_read = app->inputs[0].read(buf, 64*1024);

        to_app_data(app)->parset = new LOFAR::ParameterSet(true);
        to_app_data(app)->parset->adoptBuffer(buf);

        this->itsParset = to_app_data(app)->parset->makeSubset("Cimager.");

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

        askap::synthesis::SynthesisParamsHelper::setUpImages(itsModel,
                                  this->itsParset.makeSubset("Images."));

        // Now we need to instantiate and initialise the solver from the parset
        this->itsSolver = synthesis::ImageSolverFactory::make(this->itsParset);

        this->itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations());

        NEUtils::receiveNE(itsNe, app, 1);

        std::vector<std::string> toFitParams = itsNe->unknowns();
        std::vector<std::string>::const_iterator iter2 = toFitParams.begin();

        for (; iter2 != toFitParams.end(); iter2++) {

            ASKAPLOG_INFO_STR(logger,"Param name: " << *iter2);

        }

        // Now we need to instantiate and initialise the solver
        itsSolver->init();
        itsSolver->addNormalEquations(*itsNe);

        ASKAPLOG_INFO_STR(logger, "Solving Normal Equations");
        askap::scimath::Quality q;

        ASKAPDEBUGASSERT(itsModel);
        itsSolver->solveNormalEquations(*itsModel, q);
        ASKAPLOG_INFO_STR(logger, "Solved normal equations");


        return 0;
    }


    void SolveNE::data_written(dlg_app_info *app, const char *uid,
        const char *data, size_t n) {

        app->running();

    }

    void SolveNE::drop_completed(dlg_app_info *app, const char *uid,
            drop_status status) {

        app->done(APP_FINISHED);
        delete(to_app_data(app)->parset);
    }


} // namespace
