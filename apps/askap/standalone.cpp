//
// Manually running LoadVis to reproduce error
//
// ICRAR - International Centre for Radio Astronomy Research
// (c) UWA - The University of Western Australia, 2017
// Copyright by UWA (in the framework of the ICRAR)
// All rights reserved
//
// This library is free software; you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public
// License as published by the Free Software Foundation; either
// version 2.1 of the License, or (at your option) any later version.
//
// This library is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public
// License along with this library; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston,
// MA 02111-1307  USA
//

#include <fstream>
#include <iostream>
#include <streambuf>
#include <string>
#include <thread>

#include "factory/DaliugeApplicationFactory.h"


namespace askap {

dlg_app_info *dummy_dlg_app(const std::string &input_file) {

	std::ifstream in(input_file);
	auto ss = std::ostringstream{};
	ss << in.rdbuf();
	static thread_local auto contents = ss.str();

	// read method that always returns the contents of input_file
	auto _read = [](char *buf, size_t n) -> size_t {
		if (contents.size() < n) {
			n = contents.size();
		}
		memcpy(buf, contents.c_str(), n);
		return n;
	};

	dlg_input_info *input = new dlg_input_info();
	input->read = _read;
	input->name = new char[7];
	strcpy(input->name, "Parset");
	dlg_app_info *app = new dlg_app_info();
	app->inputs = input;
	app->n_inputs = 1;
	app->uid = new char[4];
	app->oid = new char[4];
	app->appname = new char[8];
	strcpy(app->appname, "LoadVis");
	strcpy(app->uid, "uid");
	strcpy(app->oid, "oid");
	return app;
}

void run_loadvis(const std::string &input_file) {
	const char *arguments[][2] = {{nullptr, nullptr}};
	dlg_app_info *app = dummy_dlg_app(input_file);
	DaliugeApplication::ShPtr load_vis = DaliugeApplicationFactory::make(app);
	load_vis->init((const char ***)arguments);
	load_vis->run();
}

int run(int argc, std::string input1, std::string input2) {
	std::thread t1(run_loadvis, input1);
	std::thread t2(run_loadvis, input2);
	t1.join();
	t2.join();
}

}

int main(int argc, char **argv) {
	if (argc < 3) {
		std::cerr << "Usage: " << argv[0] << " <input0> <input1>" << std::endl;
		return 1;
	}

	return askap::run(argc, argv[1], argv[2]);
}