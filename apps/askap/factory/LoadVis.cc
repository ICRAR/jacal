/// @file LoadVis.cc
///
/// @abstract
/// Loads a visibility set grids it onto the UV plane and FFTs the grid
/// @ details
///
///
// for logging
#define ASKAP_PACKAGE_NAME "LoadVis"
#include <string>
/// askap namespace
namespace askap {
/// @return version of the package
    std::string getAskapPackageVersion_LoadVis() {
        return std::string("LoadVis; ASKAPsoft==Unknown");

    }
}
/// The version of the package
#define ASKAP_PACKAGE_VERSION askap::getAskapPackageVersion_LoadVis()

#include <vector>
#include <mutex>



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


#include <mutex>
#include <string.h>
#include <sys/time.h>




namespace askap {

    LoadVis::LoadVis(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
        this->itsModel.reset(new scimath::Params());
        this->itsChan = NEUtils::getChan(raw_app->uid);
        if (this->itsChan < 0) {
          this->itsChan = 0;
        }
    }

    LoadVis::~LoadVis() {
    }

    DaliugeApplication::ShPtr LoadVis::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return LoadVis::ShPtr(new LoadVis(raw_app));
    }

    int LoadVis::init(const char ***arguments) {

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

        //  FIXME:
        //    This should be here but I could not get a boost smart pointer to work
        //    to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));
        //

        // FIXME:
        // Arbitrarily setting frequency selection to 1


        this->freqInterval = casacore::IPosition(2,0);
        this->timeInterval = casacore::IPosition(2,0);

        this->freqInterval[0] = this->itsChan;
        this->freqInterval[1] = this->itsChan+1;

        return 0;
    }

    int LoadVis::run() {

#ifndef ASKAP_PATCHED
        static std::mutex safety;
#endif // ASKAP_PATCHED

        // Lets get the key-value-parset
        ASKAP_LOGGER(logger, ".run");
        char buf[64*1024];
        size_t n_read = input("Config").read(buf, 64*1024);
        if (n_read == 64*1024) {
            n_read--;
        }
        buf[n_read] = 0;

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        this->itsParset = parset.makeSubset("Cimager.");

        // we need to fill the local parset with parameters that maybe missing
        //
        try {
            this->itsParset = NEUtils::addMissingParameters(this->itsParset, this->itsChan);
        }
        catch (std::runtime_error)
        {
            return -1;
        }
        const string colName = this->itsParset.getString("datacolumn", "DATA");
        vector<std::string> ms = this->getDatasets(this->itsParset);

        // Lets look at the model
        askap::scimath::ImagingNormalEquations::ShPtr itsNe;
        askap::synthesis::IVisGridder::ShPtr itsGridder;
        {
#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED

            ASKAPLOG_INFO_STR(logger, "Initializing the model images");

            /// Create the specified images from the definition in the
            /// parameter set. We can solve for any number of images
            /// at once (but you may/will run out of memory!)
            this->itsModel.reset(new scimath::Params());
            try {
              NEUtils::receiveParams(itsModel, input("Model"));
            }
            catch (std::runtime_error) {
              ASKAPLOG_INFO_STR(logger, "Failed to receive model setting up empty one");
              askap::synthesis::SynthesisParamsHelper::setUpImages(itsModel,
                                        this->itsParset.makeSubset("Images."));
            }


            ASKAPLOG_INFO_STR(logger, "Current model held by the drop: "<<*itsModel);

            // lets build a gridder
            itsGridder = askap::synthesis::VisGridderFactory::make(this->itsParset);

            // NE
            itsNe = askap::scimath::ImagingNormalEquations::ShPtr(new askap::scimath::ImagingNormalEquations(*itsModel));

        }

        // I cant make the gridder smart funciton a member funtion as I cannot instantiate it until I have a parset.

        std::vector<std::string>::const_iterator iter = ms.begin();

        for (; iter != ms.end(); iter++) {

#ifndef ASKAP_PATCHED
            std::lock_guard<std::mutex> guard(safety);
#endif // ASKAP_PATCHED

            ASKAPLOG_INFO_STR(logger, "Processing " << *iter);

            accessors::TableDataSource ds(*iter, accessors::TableDataSource::DEFAULT, colName);

            // this is the data selector for the measurement set
            accessors::IDataSelectorPtr sel = ds.createSelector();

            sel->chooseCrossCorrelations();
            sel->chooseChannels(1, this->freqInterval[0]);

            // FIXME: Use time interval and perhaps beam?

            accessors::IDataConverterPtr conv = ds.createConverter();
            conv->setFrequencyFrame(casacore::MFrequency::Ref(casacore::MFrequency::TOPO), "Hz");
            conv->setDirectionFrame(casacore::MDirection::Ref(casacore::MDirection::J2000));
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
            NEUtils::sendNE(itsNe, output("Normal"));
        }

        // I am going to assume a single Ne output - even though I am not
        // merging in the above loop - I should tho.

        // This is just to test whether this works at all.



        return 0;
    }


    void LoadVis::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void LoadVis::drop_completed(const char *uid, drop_status status) {

        dlg_app_done(APP_FINISHED);
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


} // namespace
