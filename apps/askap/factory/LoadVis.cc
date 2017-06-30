/// @file LoadVis.cc
///
/// @abstract
/// Derived from DaliugeApplication
/// @ details
/// Implements a test method that uses the contents of the the parset to load
/// in a measurement set and print a summary of its contents
///

#include <iostream>
#include <vector>


#include <daliuge/DaliugeApplication.h>
#include <factory/LoadVis.h>

// LOFAR ParameterSet
#include <Common/ParameterSet.h>

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
        fprintf(stdout,"\t LoadVis -  default contructor\n");
    }


    LoadVis::~LoadVis() {

    }

    DaliugeApplication::ShPtr LoadVis::createDaliugeApplication(const std::string &name)
    {
        fprintf(stdout, "\t createDaliugeApplication - Instantiating LoadVis\n");

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
        const char **param = arguments[0];
        while (1) {

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

            param++;
        }

        app->data = malloc(sizeof(struct app_data));
        if (!app->data) {
            return 1;
        }
        //  FIXME:
        //    This should be here but I could not get a boost smart pointer to work
        //    to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));
        //
        return 0;
    }

    int LoadVis::run(dlg_app_info *app) {

        // load the parset and print it out to the screen
        // std::cerr << "Hello World from run method" << std::endl;
    //    std::cout << *to_app_data(app)->parset << std::endl;

    // lets open the input and read it - get the parset - maybe this should be
    // in init

        char buf[64*1024];
        size_t n_read = app->inputs[0].read(buf, 64*1024);

        to_app_data(app)->parset = new LOFAR::ParameterSet(true);
        to_app_data(app)->parset->adoptBuffer(buf);
        std::vector<std::string> datasets(1,"hello");
        // std::vector<std::string> datasets = to_app_data(app)->parset->getStringVector("dataset", true);
        std::vector<std::string>::const_iterator iter = datasets.begin();
        for (; iter != datasets.end(); iter++) {
            std::cout << *iter << std::endl;
        }



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


} // namespace
