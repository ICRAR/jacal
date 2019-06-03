[["python:package:icedefs"]]
#ifndef ASKAP_COMMONTYPES_ICE
#define ASKAP_COMMONTYPES_ICE

module askap
{

module interfaces
{
    /**
     * Base exception from which all ICE exceptions thrown by
     * ASKAPsoft code should derive from. The reason string shall be
     * used to indicate why the exception was thrown
     **/
    exception AskapIceException
    {
        string reason;
    };

    /**
     * This is a common type which can be used as the Ice equivalent of the
     * LOFAR ParameterSet. This contains a map of variable names and maps
     * them to their value.
     **/
    dictionary<string, string> ParameterMap;

    /** A sequence of bools. **/
    sequence<bool> BoolSeq;

    /** A sequence of bytes. **/
    sequence<byte> ByteSeq;

    /** A sequence of shorts. **/
    sequence<short> ShortSeq;

    /** A sequence of ints. **/
    sequence<int> IntSeq;

    /** A sequence of longs. **/
    sequence<long> LongSeq;

    /** A sequence of floats. **/
    sequence<float> FloatSeq;

    /** A sequence of doubles. **/
    sequence<double> DoubleSeq;

    /** A sequence of strings. **/
    sequence<string> StringSeq;

    /**
     * A single-precision complex number.
     **/
    struct FloatComplex{
        float real;
        float imag;
    };

    /**
     * A sequence of single-precision complex numbers.
     **/
    sequence<FloatComplex> FloatComplexSeq;

    /**
     * A double-precision complex number.
     **/
    struct DoubleComplex {
        double real;
        double imag;
    };

    /**
     * A sequence of double-precision complex numbers.
     **/
    sequence<DoubleComplex> DoubleComplexSeq;

    /** Coordinate frame type */
    enum CoordSys {
        J2000,
        AZEL
    };
    /**
     * Astronomical direction (e.g. a casacore measure)
     **/
    struct Direction {
        /** RA/azimuth (in degrees) **/
        double coord1;
        /** Dec/elevation (in degrees) **/
        double coord2;
        /** coordinate frame **/
        CoordSys sys;
    };

    /**
     * A sequence of astronomical directions
     */
    sequence<Direction> DirectionSeq;

};
};

#endif
