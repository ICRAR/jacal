/// @file GaussianPB.h

/// @brief Standard Gaussian Primary Beam
/// @details
///

#ifndef ASKAP_FACTORY_EXAMPLE_H
#define ASKAP_FACTORY_EXAMPLE_H

#include <daliuge/DaliugeApplication.h>

#include <boost/shared_ptr.hpp>


#include <casacore/casa/Arrays/Vector.h>
#include <casacore/casa/Arrays/IPosition.h>

namespace askap {
    //! @brief Example class for reference
    class Example : public DaliugeApplication

    {

    public:

        typedef boost::shared_ptr<Example> ShPtr;

        Example(dlg_app_info *raw_app);

        static inline std::string ApplicationName() { return "Example";}

        virtual ~Example();

        static DaliugeApplication::ShPtr createDaliugeApplication(dlg_app_info *raw_app);

        virtual int init(const char ***arguments) override;

        virtual int run() override;

        virtual void data_written(const char *uid, const char *data, size_t n) override;

        virtual void drop_completed(const char *uid, drop_status status) override;

    private:
        bool print_stats;
        unsigned long total;
        unsigned long write_duration;

    };

} // namespace askap


#endif //
