// @file rename.h

/// @brief rename the casa namespace to casacore
/// @details the old askap code uses the casa namespace which has been removed

#ifndef RENAME_H
#define RENAME_H

/**
 * NOTE:
 *
 * the whole purpose of this file is to allow use to use the ASKAP which still uses the casa:: namespace, which no
 * longer exists in casa.
 *
 * The include brings in the casacore namespace and the namespace alias the namespace
 */

#include <casacore/casa/Utilities.h>
namespace casa = casacore;

#endif