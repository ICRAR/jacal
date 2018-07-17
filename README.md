## JACAL
**J**oint **A**stronomy **CAL**ibration and
imaging software

The JACAL software project aims to integrate the [ASKAPSoft](https://www.atnf.csiro.au/computing/software/askapsoft/sdp/docs/current/pipelines/introduction.html) software package and the [DALiuGE](https://github.com/ICRAR/daliuge) execution framework in preparation for the SKA pre-construction. To integrate ASKAPSoft into DALiuGE we create a shared library with multiple applications contained within. The shared library offers a calling convention that DALiuGE understands, while internally it links and reuses the ASKAPSoft code to implement the functionality of the applications.

Jacal is freely available in this [GitHub repository](https://github.com/ICRAR/jacal) under a variation of the BSD/MIT License. The repository contains the following:

* The C/C++ code that implements the shared library described above (called libaskapsoft_dlg.so)
* A utility test application called standalone, which provides a mock DALiuGE context and is therefore useful to test the library contents outside DALiuGE.
* A series of high-level functional tests, together with their associated data, to ensure the dynamic library is working as expected.
* The ingest pipeline code.
* Continuous integration support scripts.
* Utility scripts to deploy the system in a variety of supercomputers.

## Questions?

Feel free to open an issue to discuss any questions not covered so far.
