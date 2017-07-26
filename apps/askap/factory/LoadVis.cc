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

#include <iostream>
#include <vector>


#include <daliuge/DaliugeApplication.h>
#include <factory/LoadVis.h>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>
// ASKAP Logger

#include <askap/AskapLogging.h>
#include <askap/AskapError.h>

#include <string.h>
#include <sys/time.h>

ASKAP_LOGGER(logger, ".run");

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
        fprintf(stdout,"\t LoadVis -  default contructor\n");
    }


    LoadVis::~LoadVis() {

    }

    DaliugeApplication::ShPtr LoadVis::createDaliugeApplication(const std::string &name)
    {
        ASKAP_LOGGER(locallogger, ".create");
        //fprintf(stdout, "\t createDaliugeApplication - Instantiating LoadVis\n");
        ASKAPLOG_INFO_STR(locallogger,"createDaliugeApplication - Instantiating LoadVis");
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

        // load the parset and print it out to the screen
        // std::cerr << "Hello World from run method" << std::endl;
    //    std::cout << *to_app_data(app)->parset << std::endl;

    // lets open the input and read it - get the parset - maybe this should be
    // in init


    ///  int i = 1;
    ///  ASKAP_LOGGER(locallog, ".test");
    ///
    ///  ASKAPLOG_WARN(locallog,"Warning. This is a warning.");
    ///  ASKAPLOG_INFO(locallog,"This is an automatic (subpackage) log");
    ///  ASKAPLOG_INFO_STR(locallog,"This is " << i << " log stream test.");
    ///


        char buf[64*1024];
        size_t n_read = app->inputs[0].read(buf, 64*1024);

        to_app_data(app)->parset = new LOFAR::ParameterSet(true);
        to_app_data(app)->parset->adoptBuffer(buf);

        this->itsParset = to_app_data(app)->parset->makeSubset("Cimager.");
        const string colName = this->itsParset.getString("datacolumn", "DATA");
        vector<std::string> ms = this->getDatasets();

        std::vector<std::string>::const_iterator iter = ms.begin();

        for (; iter != ms.end(); iter++) {
            accessors::TableDataSource ds(*iter, accessors::TableDataSource::DEFAULT, colName);

            // this is the data selector for the measurement set
            accessors::IDataSelectorPtr sel = ds.createSelector();

            sel->chooseCrossCorrelations();
            sel->chooseChannels(1, this->freqInterval[0]);

            accessors::IDataConverterPtr conv = ds.createConverter();
            conv->setFrequencyFrame(casa::MFrequency::Ref(casa::MFrequency::TOPO), "Hz");
            conv->setDirectionFrame(casa::MDirection::Ref(casa::MDirection::J2000));
            conv->setEpochFrame();


        }

        // need to select the part of the vis that I want to process
        // need a time and frequency selection

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
    std::vector<std::string> LoadVis::getDatasets()
    {
        if (itsParset.isDefined("dataset") && itsParset.isDefined("dataset0")) {
            ASKAPTHROW(std::runtime_error,
                "Both dataset and dataset0 are specified in the parset");
        }

        // First look for "dataset" and if that does not exist try "dataset0"
        vector<string> ms;
        if (itsParset.isDefined("dataset")) {
            ms = itsParset.getStringVector("dataset", true);
        } else {
            string key = "dataset0";   // First key to look for
            long idx = 0;
            while (itsParset.isDefined(key)) {
                const string value = itsParset.getString(key);
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
