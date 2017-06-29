/// @file GaussianPB.cc
///
/// @abstract
/// Derived from PrimaryBeams this is the Gaussian beam as already implemented
/// @ details
/// Implements the methods that evaluate the primary beam gain ain the case of a
/// Gaussian
///


#include <daliuge/DaliugeApplication.h>
#include <factory/LoadParset.h>
// ASKAP Logging etc
#include <askap/AskapError.h>
#include <askap/AskapLogging.h>
// LOFAR ParameterSet
#include <Common/ParameterSet.h>

#include <string.h>
#include <sys/time.h>

ASKAP_LOGGER(logger, ".daliuge.factory");
namespace askap {


    struct app_data {

        boost::shared_ptr<LOFAR::ParameterSet> parset;
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


    LoadParset::LoadParset() {
        ASKAPLOG_DEBUG_STR(logger,"LoadParset default contructor");
    }


    LoadParset::~LoadParset() {

    }

    DaliugeApplication::ShPtr LoadParset::createDaliugeApplication(const std::string &name)
    {
        ASKAPLOG_DEBUG_STR(logger, "createDaliugeApplication for LoadParset ");

        LoadParset::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new LoadParset());

        ASKAPLOG_DEBUG_STR(logger,"Created LoadParset DaliugeApplication instance");
        return ptr;

    }
    int LoadParset::init(dlg_app_info *app, const char ***arguments) {


        char *parset_filename = 0;
        const char **param = arguments[0];
        while (1) {

            // Sentinel
            if (*param == NULL) {
                break;
            }
            // any params I might need go here
            if (strcmp(param[0], "parset_filename") == 0) {
                parset_filename = strdup(param[1]);
            }

            param++;
        }

        to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));

        return 0;
    }

    int LoadParset::run(dlg_app_info *app) {

        // load the parset and print it out to the screen

        std::cout << *to_app_data(app)->parset << std::endl;


        // write it to the outputs

        return 0;
    }


    void LoadParset::data_written(dlg_app_info *app, const char *uid,
        const char *data, size_t n) {

        app->running();

    }

    void LoadParset::drop_completed(dlg_app_info *app, const char *uid,
            drop_status status) {

        app->done(APP_FINISHED);

    }


} // namespace
