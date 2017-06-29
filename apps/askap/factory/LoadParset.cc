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


    LoadParset::LoadParset() {
        fprintf(stdout,"LoadParset default contructor");
    }


    LoadParset::~LoadParset() {

    }

    DaliugeApplication::ShPtr LoadParset::createDaliugeApplication(const std::string &name)
    {
        fprintf(stdout, "createDaliugeApplication for LoadParset ");

        LoadParset::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new LoadParset());

        fprintf(stdout,"Created LoadParset DaliugeApplication instance");
        return ptr;

    }
    int LoadParset::init(dlg_app_info *app, const char ***arguments) {

        std::cerr << "Hello World from init method" << std::endl;

        // Argument parsing is not working as yet
#if 0

        char *parset_filename = 0;
        const char **param = arguments[0];
        while (1) {

            // Sentinel
            if (param == NULL) {
                break;
            }
            // any params I might need go here
            if (strcmp(param[0], "parset_filename") == 0) {
                parset_filename = strdup(param[1]);
            }

            param++;
        }

    //    to_app_data(app)->parset.reset( new LOFAR::ParameterSet(parset_filename));
#endif
        app->data = malloc(sizeof(struct app_data));
        if (!app->data) {
            return 1;
        }

        return 0;
    }

    int LoadParset::run(dlg_app_info *app) {

        // load the parset and print it out to the screen
        std::cerr << "Hello World from run method" << std::endl;
    //    std::cout << *to_app_data(app)->parset << std::endl;

    // lets open the input and read it
        char buf[64*1024];
        size_t n_read = app->inputs[0].read(buf, 64*1024);
        // fprintf(stderr,"%s",buf);
        to_app_data(app)->parset = new LOFAR::ParameterSet(true);
        to_app_data(app)->parset->adoptBuffer(buf);

        std::cout << *(to_app_data(app)->parset) << std::endl;
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
