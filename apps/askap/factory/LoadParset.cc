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
        short print_stats;
        unsigned long total;
        unsigned long write_duration;
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

        short print_stats = 0;
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
        to_app_data(app)->total = 0;
        to_app_data(app)->write_duration = 0;
        return 0;
    }

    int LoadParset::run(dlg_app_info *app) {

        char buf[64*1024];
        unsigned int total = 0, i;
        unsigned long read_duration = 0, write_duration = 0;
        struct timeval start, end;

        if (to_app_data(app)->print_stats) {
            printf("running / done methods addresses are %p / %p\n", app->running, app->done);
        }

        while (1) {

            gettimeofday(&start, NULL);
            size_t n_read = app->inputs[0].read(buf, 64*1024);
            gettimeofday(&end, NULL);
            read_duration += usecs(&start, &end);
            if (!n_read) {
                break;
            }

            gettimeofday(&start, NULL);
            for (i = 0; i < app->n_outputs; i++) {
                app->outputs[i].write(buf, n_read);
            }
            gettimeofday(&end, NULL);
            write_duration += usecs(&start, &end);
            total += n_read;
        }

        double duration = (read_duration + write_duration) / 1000000.;
        double total_mb = total / 1024. / 1024.;

        if (to_app_data(app)->print_stats) {
            printf("Read %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / (read_duration / 1000000.));
            printf("Wrote %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / (write_duration / 1000000.));
            printf("Copied %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / duration);
        }

        return 0;
    }

    void LoadParset::data_written(dlg_app_info *app, const char *uid,
        const char *data, size_t n) {
            unsigned int i;
            struct timeval start, end;

            app->running();
            gettimeofday(&start, NULL);
            for (i = 0; i < app->n_outputs; i++) {
                app->outputs[i].write(data, n);
            }
            gettimeofday(&end, NULL);

            to_app_data(app)->total += n;
            to_app_data(app)->write_duration += usecs(&start, &end);
    }

    void LoadParset::drop_completed(dlg_app_info *app, const char *uid,
            drop_status status) {
                /* We only have one output so we're finished */
                double total_mb = (to_app_data(app)->total / 1024. / 1024.);
                if (to_app_data(app)->print_stats) {
                    printf("Wrote %.3f [MB] of data to %u outputs in %.3f [ms] at %.3f [MB/s]\n",
                    total_mb, app->n_outputs,
                    to_app_data(app)->write_duration / 1000.,
                    total_mb / (to_app_data(app)->write_duration / 1000000.));
                }
                app->done(APP_FINISHED);
                free(app->data);
    }


} // namespace
