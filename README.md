## JACAL
**J**oint **A**stronomy **CAL**ibration and
imaging software

JACAL integrates [ASKAPSoft](https://www.atnf.csiro.au/computing/software/askapsoft/sdp/docs/current/pipelines/introduction.html) and the execution framework [DALiuGE](https://github.com/ICRAR/daliuge). A shared library offers a calling convention supported by DALiuGE and internally links and reuses ASKAPSoft code. JACAL is freely available in this [GitHub repository](https://github.com/ICRAR/jacal) under a variation of the open source 3-Clause BSD License. The repository contains the following:

* The C/C++ code of the shared library libaskapsoft_dlg.so described above
* A standalone utility for library testing independent of DALiuGE.
* A number of high-level functional library tests and associated test data.
* The ingest pipeline code.
* Continuous integration support scripts.
* Utility scripts to deploy the system on a variety of supercomputers.

## Questions?

Feel free to open an issue to discuss any questions not covered so far.
