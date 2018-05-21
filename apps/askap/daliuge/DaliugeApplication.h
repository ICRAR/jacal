/// @file DaliugeApplication.h
/// @brief Base class for Daliuge applications
/// @details All jacal functions inherit from this base class. It exposes the methods that the Daliuge
///         pipeline is expecting
///
/// @copyright (c) 2017 CSIRO
/// Australia Telescope National Facility (ATNF)
/// Commonwealth Scientific and Industrial Research Organisation (CSIRO)
/// PO Box 76, Epping NSW 1710, Australia
/// atnf-enquiries@csiro.au
///
/// This file is part of the ASKAP software distribution.
///
/// The ASKAP software distribution is free software: you can redistribute it
/// and/or modify it under the terms of the GNU General Public License as
/// published by the Free Software Foundation; either version 2 of the License,
/// or (at your option) any later version.
///
/// This program is distributed in the hope that it will be useful,
/// but WITHOUT ANY WARRANTY; without even the implied warranty of
/// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
/// GNU General Public License for more details.
///
/// You should have received a copy of the GNU General Public License
/// along with this program; if not, write to the Free Software
/// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
///
/// @author Stephen Ord <stephen.ord@csiro.au>

#ifndef ASKAP_DALIUGE_APPLICATION_H
#define ASKAP_DALIUGE_APPLICATION_H

// System includes
#include <string>
#include <sstream>
#include <stdexcept>

//ASKAPSoft includes
#include <boost/shared_ptr.hpp>
#include <boost/regex.hpp>
// daliugue includes
#include "dlg_app.h"

namespace askap {

    /// @brief Daliuge application class.
    /// @details This class encapsulates the functions required of a daliuge application
    /// as specified in dlg_app.h then exposes them as C functions


    class DaliugeApplication {
        public:

            /// The application name
            /// Not sure this will work - but we can try.
            // I think I need this because I need to know which app to instantiate
            // the app has no persistence between calls .... maybe it should


            /// Shared pointer definition
            typedef boost::shared_ptr<DaliugeApplication> ShPtr;

            /// Constructor
            DaliugeApplication(dlg_app_info *app) :
                raw_dlg_app(app) {}

            /// Destructor
            virtual ~DaliugeApplication() {};

            /// This has to be static as we need to access it in the register even
            /// if there is not instantiated class.

            static ShPtr createDaliugeApplication(dlg_app_info *app);

            // To be implemented by sub-classes
            /// This function is implemented by sub-classes. i.e. The users of
            /// this class.

            virtual int init(const char ***arguments) = 0;

            virtual int run() = 0;

            virtual void data_written(const char *uid, const char *data, size_t n) = 0;

            virtual void drop_completed(const char *uid, drop_status status) = 0;

        protected:

            void dlg_app_running() {
                raw_dlg_app->running();
            }

            void dlg_app_done(app_status status) {
                raw_dlg_app->done(status);
            }

            dlg_output_info &output(size_t i) {
                return raw_dlg_app->outputs[i];
            }

            dlg_output_info &output(const std::string &tag) {

                boost::regex exp1(tag);
                boost::cmatch what;

                for (auto i = 0; i < raw_dlg_app->n_outputs; i++) {
                    if (boost::regex_search(raw_dlg_app->outputs[i].name, what, exp1)) {
                        return raw_dlg_app->outputs[i];
                    }
                }

                std::ostringstream os;
                os << "No such output: " << tag;
                throw std::runtime_error(os.str());
            }

            bool has_output(const std::string &tag) {

                boost::regex exp1(tag);
                boost::cmatch what;

                for (auto i = 0; i < raw_dlg_app->n_outputs; i++) {
                    if (boost::regex_search(raw_dlg_app->outputs[i].name, what, exp1)) {
                        return true;
                    }
                }

                return false;
            }

            std::vector<int> get_inputs(const std::string &tag) {

              boost::regex exp1(tag);
              boost::cmatch what;
              std::vector<int> the_inputs;
              for (int i = 0; i < raw_dlg_app->n_inputs; i++) {
                  if (boost::regex_search(raw_dlg_app->inputs[i].name, what, exp1)) {
                      the_inputs.push_back(i);
                  }
              }
              return the_inputs;

            }

            dlg_input_info &input(size_t i) {
                return raw_dlg_app->inputs[i];
            }

            dlg_input_info &input(const std::string &tag) {

                boost::regex exp1(tag);
                boost::cmatch what;

                for (auto i = 0; i < raw_dlg_app->n_inputs; i++) {
                    if (boost::regex_search(raw_dlg_app->inputs[i].name, what, exp1)) {
                        return raw_dlg_app->inputs[i];
                    }
                }

                std::ostringstream os;
                os << "No such input: " << tag;
                throw std::runtime_error(os.str());
            }

            bool has_input(const std::string &tag) {

                boost::regex exp1(tag);
                boost::cmatch what;

                for (auto i = 0; i < raw_dlg_app->n_inputs; i++) {
                    if (boost::regex_search(raw_dlg_app->inputs[i].name, what, exp1)) {
                        return true;
                    }
                }

                return false;
            }

            unsigned int n_outputs() {
                return raw_dlg_app->n_outputs;
            }

            unsigned int n_inputs() {
                return raw_dlg_app->n_inputs;
            }

        private:
            dlg_app_info *raw_dlg_app;
    };



} // End namespace askap



#endif
