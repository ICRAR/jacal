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
        std::cout << "LoadParset -  contructor" << std::endl;
    }


    LoadParset::~LoadParset() {
        std::cout << "LoadParset -  default destructor" << std::endl;
    }

    DaliugeApplication::ShPtr LoadParset::createDaliugeApplication(dlg_app_info *raw_app)
    {
        std::cout << "createDaliugeApplication - Instantiating LoadParset" << std::endl;

        LoadParset::ShPtr ptr;

        // We need to pull all the parameters out of the parset - and set
        // all the private variables required to define the beam


        ptr.reset( new LoadParset(raw_app));

        std::cout << "createDaliugeApplication - Created LoadParset DaliugeApplication instance" << std::endl;
        return ptr;

    }

    int LoadParset::init(const char ***arguments) {
        // no-op
    }

    int LoadParset::run() {

        // load the parset and print it out to the screen
        // std::cerr << "Hello World from run method" << std::endl;
    //    std::cout << *to_app_data(app)->parset << std::endl;

    // lets open the input and read it
        char buf[64*1024];
        size_t n_read = input(0).read(buf, 64*1024);

        LOFAR::ParameterSet parset(true);
        parset.adoptBuffer(buf);

        // write it to the outputs
        std::cout << parset << std::endl;

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
