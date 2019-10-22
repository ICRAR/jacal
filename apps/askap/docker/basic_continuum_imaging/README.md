### Basic Continuum Imaging Tutorial of Yandasoft Wrapped in Docker for DALiuGE Integration
The implementation process refers to [this link](https://www.atnf.csiro.au/computing/software/askapsoft/sdp/docs/current/tutorials/basiccontinuum.html).

The codes is related to [the ticket](https://jira.skatelescope.org/browse/YAN-159).

Assuming that you clone this repository to /opt/jacal. 

You can download test measurement sets at https://github.com/SKA-ScienceDataProcessor/algorithm-reference-library/tree/master/data/vis. and then copy ASKAP_example.ms to /opt/jacal/apps/askap/docker/basic_continuum_imaging/ms

The file `calibrator.in`, `mssplit.in`,`dirty.in` is the demo configuration file of `ccalibrator`, `mssplit` and `cimager` respectively,

The logical graph is given by `yanda.json`. If you clone this repository in different directory. You should modify volume mapping part in `yanda.json` accordingly.
