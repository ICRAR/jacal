/// @file GaussianPB.cc
///
/// @abstract
/// Derived from PrimaryBeams this is the Gaussian beam as already implemented
/// @ details
/// Implements the methods that evaluate the primary beam gain ain the case of a
/// Gaussian
///

#include <daliuge/DaliugeApplication.h>
#include <factory/Example.h>
#include <askap/AskapError.h>

#include <Common/ParameterSet.h>

#include <string.h>
#include <sys/time.h>


namespace askap {


    static inline
    unsigned long usecs(struct timeval *start, struct timeval *end)
    {
        return (end->tv_sec - start->tv_sec) * 1000000 + (end->tv_usec - start->tv_usec);
    }


    Example::Example(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app),
        print_stats(false),
        total(0), write_duration(0)
    {
        fprintf(stdout,"Example contructor");
    }


    Example::~Example() {

    }

    DaliugeApplication::ShPtr Example::createDaliugeApplication(dlg_app_info *raw_app)
    {
        fprintf(stdout, "createDaliugeApplication for Example ");

        Example::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new Example(raw_app));

        fprintf(stdout,"Created Example DaliugeApplication instance");
        return ptr;

    }

    int Example::init(const char ***arguments) {

        while (1) {

            const char **param = *arguments;

            // Sentinel
            if (param == NULL) {
                break;
            }

            if (strcmp(param[0], "print_stats") == 0) {
            	print_stats = strcmp(param[1], "1") == 0 || strcmp(param[1], "true") == 0;
                break;
            }

            arguments++;
        }

        return 0;
    }

    int Example::run() {

        char buf[64*1024];
        unsigned int total = 0, i;
        unsigned long read_duration = 0, write_duration = 0;
        struct timeval start, end;

        while (1) {

            gettimeofday(&start, NULL);
            size_t n_read = input(0).read(buf, 64*1024);
            gettimeofday(&end, NULL);
            read_duration += usecs(&start, &end);
            if (!n_read) {
                break;
            }

            gettimeofday(&start, NULL);
            for (i = 0; i < n_outputs(); i++) {
                output(i).write(buf, n_read);
            }
            gettimeofday(&end, NULL);
            write_duration += usecs(&start, &end);
            total += n_read;
        }

        double duration = (read_duration + write_duration) / 1000000.;
        double total_mb = total / 1024. / 1024.;

        if (print_stats) {
            printf("Read %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / (read_duration / 1000000.));
            printf("Wrote %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / (write_duration / 1000000.));
            printf("Copied %.3f [MB] of data at %.3f [MB/s]\n", total_mb, total_mb / duration);
        }

        return 0;
    }

    void Example::data_written(const char *uid, const char *data, size_t n) {
            unsigned int i;
            struct timeval start, end;

            dlg_app_running();
            gettimeofday(&start, NULL);
            for (i = 0; i < n_outputs(); i++) {
                output(i).write(data, n);
            }
            gettimeofday(&end, NULL);

            total += n;
            write_duration += usecs(&start, &end);
    }

    void Example::drop_completed(const char *uid, drop_status status) {
                /* We only have one output so we're finished */
                double total_mb = (total / 1024. / 1024.);
                if (print_stats) {
                    printf("Wrote %.3f [MB] of data to %u outputs in %.3f [ms] at %.3f [MB/s]\n",
                    total_mb, n_outputs(),
                    write_duration / 1000.,
                    total_mb / (write_duration / 1000000.));
                }
                dlg_app_done(APP_FINISHED);
    }


} // namespace
