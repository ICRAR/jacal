## JACAL
**J**oint **A**stronomy **CAL**ibration and
imaging software

JACAL integrates [ASKAPSoft](https://www.atnf.csiro.au/computing/software/askapsoft/sdp/docs/current/pipelines/introduction.html) and the execution framework [DALiuGE](https://github.com/ICRAR/daliuge). A shared library offers a calling convention supported by DALiuGE and internally links and reuses ASKAPSoft code. JACAL is freely available in this [GitHub repository](https://github.com/ICRAR/jacal) under a variation of the open source BSD 3-Clause [License](LICENSE). The repository contains the following:

* The C/C++ code of the shared library libaskapsoft_dlg.so described above
* A standalone utility for library testing independent of DALiuGE.
* A number of high-level functional library tests and associated test data.
* The ingest pipeline code.
* Continuous integration support scripts.
* Utility scripts to deploy the system on a variety of supercomputers.

## Acknowledgement

The development of JACAL was jointly initiated by [ICRAR](https://www.icrar.org/) and [CSIRO](https://www.csiro.au/) during the SKA pre-construction phase. The work was supported by the Australian Government through the Department of Industry, Innovation and Science under the Round 2 SKA Pre-construction Grants Programme and more recently by the SKA Bridging Grant SKA75656.


## Questions?

Feel free to open an issue to discuss any questions not covered so far.
