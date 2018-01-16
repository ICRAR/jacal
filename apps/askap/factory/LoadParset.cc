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
#include <factory/NEUtils.h>


// LOFAR ParameterSet
#include <Common/ParameterSet.h>

#include <string.h>
#include <sys/time.h>


namespace askap {

    LoadParset::LoadParset(dlg_app_info *raw_app) :
        DaliugeApplication(raw_app)
    {
    }


    LoadParset::~LoadParset() {
    }

    DaliugeApplication::ShPtr LoadParset::createDaliugeApplication(dlg_app_info *raw_app)
    {
        return LoadParset::ShPtr(new LoadParset(raw_app));
    }

    int LoadParset::init(const char ***arguments) {
        // no-op
        return 1;
    }

    int LoadParset::run() {

        // lets open the input and read it
        char buf[64*1024];
        size_t n_read = input(0).read(buf, 64*1024);

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        // write it to the outputs
        for (int i = 0; i < n_outputs(); i++) {
            output(i).write(buf, n_read);
        }

        return 0;
    }


    void LoadParset::data_written(const char *uid, const char *data, size_t n) {
        dlg_app_running();
    }

    void LoadParset::drop_completed(const char *uid, drop_status status) {
        dlg_app_done(APP_FINISHED);
    }


} // namespace
