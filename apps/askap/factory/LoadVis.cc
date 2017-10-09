/// @file LoadVis.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///
// for logging
#define ASKAP_PACKAGE_NAME "LoadVis"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_LoadVis();
    std::string getAskapPackageVersion_synthesis() {
        return std::string("LoadVis; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_LoadVis()

#include <iostream>
#include <vector>



#include <daliuge/DaliugeApplication.h>
#include <factory/LoadVis.h>
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


    struct app_data {
        LOFAR::ParameterSet *parset;
    };

    static inline
    struct app_data *to_app_data(dlg_app_info *app)
    {
        return (struct app_data *)app->data;
    }

    static inline
    unsigned long usecs(struct timeval *start, struct timeval *end)
    {
        return (end->tv_sec - start->tv_sec) * 1000000 + (end->tv_usec - start->tv_usec);
    }


    LoadVis::LoadVis() {
        //ASKAP_LOGGER(locallogger,"\t LoadVis -  default contructor\n");
        std::cout << "LoadVis -  default constructor" << std::endl;
        this->itsModel.reset(new scimath::Params());
    }


    LoadVis::~LoadVis() {
        //ASKAP_LOGGER(locallogger,"\t LoadVis -  default destructor\n");
        std::cout << "LoadVis -  default destructor" << std::endl;
    }

    DaliugeApplication::ShPtr LoadVis::createDaliugeApplication(const std::string &name)
    {
        // ASKAP_LOGGER(locallogger, ".create");
        fprintf(stdout, "\tcreateDaliugeApplication - Instantiating LoadVis\n");
        // ASKAPLOG_INFO_STR(locallogger,"createDaliugeApplication - Instantiating LoadVis");
        LoadVis::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new LoadVis());

        fprintf(stdout,"\t createDaliugeApplication - Created LoadVis DaliugeApplication instance\n");
        return ptr;

    }
    int LoadVis::init(dlg_app_info *app, const char ***arguments) {

        // std::cerr << "Hello World from init method" << std::endl;

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

        app->data = malloc(sizeof(struct app_data));
        if (!app->data) {
            return 1;
        }
        //  FIXME:
        //    This should be here but I could not get a boost smart pointer to work
        //    to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));
        //

        // FIXME:
        // Arbitrarily setting frequency selection to 1
        this->freqInterval = casa::IPosition(2,0);
        this->timeInterval = casa::IPosition(2,0);

        this->freqInterval[0] = 0;
        this->freqInterval[1] = 1;

        return 0;
    }

    int LoadVis::run(dlg_app_info *app) {

        // Lets get the key-value-parset
        ASKAPLOG_INIT("");
        ASKAP_LOGGER(logger, ".run");
        char buf[64*1024];
        size_t n_read = app->inputs[0].read(buf, 64*1024);

        to_app_data(app)->parset = new LOFAR::ParameterSet(true);
        to_app_data(app)->parset->adoptBuffer(buf);

        this->itsParset = to_app_data(app)->parset->makeSubset("Cimager.");

        // we need to fill the local parset with parameters that maybe missing
        //
        try {
            this->itsParset = addMissingParameters(this->itsParset);
        }
        catch (std::runtime_error)
        {
            return -1;
        }
        const string colName = this->itsParset.getString("datacolumn", "DATA");
        vector<std::string> ms = this->getDatasets(this->itsParset);

        // Lets look at the model

        ASKAPLOG_INFO_STR(logger, "Initializing the model images");

            /// Create the specified images from the definition in the
            /// parameter set. We can solve for any number of images
            /// at once (but you may/will run out of memory!)
        askap::synthesis::SynthesisParamsHelper::setUpImages(itsModel,
                                  this->itsParset.makeSubset("Images."));


        ASKAPLOG_INFO_STR(logger, "Current model held by the drop: "<<*itsModel);

        // lets build a gridder

        askap::synthesis::IVisGridder::ShPtr itsGridder = askap::synthesis::VisGridderFactory::make(this->itsParset);

        // NE
        askap::scimath::ImagingNormalEquations::ShPtr itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations(*itsModel));




        // I cant make the gridder smart funciton a member funtion as I cannot instantiate it until I have a parset.

        std::vector<std::string>::const_iterator iter = ms.begin();

        for (; iter != ms.end(); iter++) {

            std::cout << "Processing " << *iter << std::endl;

            accessors::TableDataSource ds(*iter, accessors::TableDataSource::DEFAULT, colName);

            // this is the data selector for the measurement set
            accessors::IDataSelectorPtr sel = ds.createSelector();

            sel->chooseCrossCorrelations();
            sel->chooseChannels(1, 0);

            accessors::IDataConverterPtr conv = ds.createConverter();
            conv->setFrequencyFrame(casa::MFrequency::Ref(casa::MFrequency::TOPO), "Hz");
            conv->setDirectionFrame(casa::MDirection::Ref(casa::MDirection::J2000));
            conv->setEpochFrame();

            accessors::IDataSharedIter it = ds.createIterator(sel, conv);

            // need to define an empty model (or pick one up from the parset)


            ASKAPLOG_INFO_STR(logger,"Not applying calibration");
            ASKAPLOG_INFO_STR(logger,"building FFT/measurement equation");
            boost::shared_ptr<askap::synthesis::ImageFFTEquation> fftEquation(new askap::synthesis::ImageFFTEquation (*itsModel, it, itsGridder));
            ASKAPDEBUGASSERT(fftEquation);
            fftEquation->useAlternativePSF(itsParset);
            //
            // Set this to an empty pointer - no aggregation across groups for this
            //fftEquation->setVisUpdateObject(boost::shared_ptr<askap::synthesis::GroupVisAggregator>());
            ASKAPLOG_INFO_STR(logger,"calculating Imaging Normal Equations");

            // Equation
            askap::scimath::Equation::ShPtr itsEquation = fftEquation;
            itsEquation->calcEquations(*itsNe);

            // lets dump out some images
            NEUtils::sendNE(itsNe, app);

        }

        // I am going to assume a single Ne output - even though I am not
        // merging in the above loop - I should tho.

        // This is just to test whether this works at all.



        return 0;
    }


    void LoadVis::data_written(dlg_app_info *app, const char *uid,
        const char *data, size_t n) {

        app->running();

    }

    void LoadVis::drop_completed(dlg_app_info *app, const char *uid,
            drop_status status) {

        app->done(APP_FINISHED);
        delete(to_app_data(app)->parset);
    }
    std::vector<std::string> LoadVis::getDatasets(const LOFAR::ParameterSet& parset)
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

    LOFAR::ParameterSet LoadVis::addMissingParameters(LOFAR::ParameterSet& parset) {

        ASKAP_LOGGER(logger, ".addMissingParameters");

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

            ASKAPLOG_WARN_STR(logger,"Param not found: " << param);
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
            ASKAPLOG_INFO_STR(logger, "  Advising on parameter " << param << ": " << pstr.str().c_str());
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
                     ASKAPLOG_INFO_STR(logger, "  Advising on parameter " << param <<": " << pstr.str().c_str());
                     parset.add(param, pstr.str().c_str());
                 }
            }
            param = "Images."+imageNames[img]+".shape";
            if ( !parset.isDefined(param) ) shapeNeeded = true;

            param = "Images."+imageNames[img]+".frequency";

            if ( !parset.isDefined(param) ) {
                ASKAPLOG_WARN_STR(logger,"Param not found: " << param);
                ASKAPTHROW(std::runtime_error,"Frequency not in parset");

            }
            param ="Images."+imageNames[img]+".direction";
            if ( !parset.isDefined(param) && directionNeeded) {
                ASKAPLOG_WARN_STR(logger,"Param not found: " << param);
                ASKAPTHROW(std::runtime_error,"direction not in parset");
            }
            else if (!parset.isDefined(param) && !directionNeeded) {
                ASKAPLOG_INFO_STR(logger,"Root direction specified but no image direction. Assuming they are the same");
                const vector<string> directionVector = parset.getStringVector("Images.direction");

                std::ostringstream pstr;
                pstr<<"["<< directionVector[0].c_str() <<","<<directionVector[1].c_str() <<"," << directionVector[2].c_str() << "]";
                const string key="Images."+imageNames[img]+".direction";
                ASKAPLOG_INFO_STR(logger, "  Advising on parameter " << param <<": " << pstr.str().c_str());

                parset.add(param, pstr.str().c_str());


            }
            param = "Images."+imageNames[img]+".nterms"; // if nterms is set, store it for later
            if (parset.isDefined(param)) {
                if ((nTerms>1) && (nTerms!=parset.getInt(param))) {
                    ASKAPLOG_WARN_STR(logger, "  Imaging with different nterms may not work");
                }
                nTerms = parset.getInt(param);
            }

            if ( !parset.isDefined("Images."+imageNames[img]+".nchan") ) {
                ASKAPLOG_WARN_STR(logger,"Param not found: " << param);
            }
        }

        if (nTerms > 1) { // check required MFS parameters
            param = "visweights"; // set to "MFS" if unset and nTerms > 1
            if (!parset.isDefined(param)) {
                std::ostringstream pstr;
                pstr<<"MFS";
                ASKAPLOG_DEBUG_STR(logger, "  Advising on parameter " << param <<": " << pstr.str().c_str());
                parset.add(param, pstr.str().c_str());
            }

            param = "visweights.MFS.reffreq"; // set to average frequency if unset and nTerms > 1
            if ((parset.getString("visweights")=="MFS")) {
                if (!parset.isDefined(param)) {
                    ASKAPLOG_WARN_STR(logger,"Param not found: " << param);
                    ASKAPTHROW(std::runtime_error,"MFS reference frequency not in parset");
                }

            }
        }

        // test for general missing parameters:
        if ( cellsizeNeeded && !parset.isDefined("nUVWMachines") ) {

        } else if ( cellsizeNeeded && !parset.isDefined("Images.cellsize") ) {

        } else if ( shapeNeeded && !parset.isDefined("Images.shape") ) {

        }
        ASKAPLOG_INFO_STR(logger,"Done adding missing params ");

        return parset;
    }

} // namespace
