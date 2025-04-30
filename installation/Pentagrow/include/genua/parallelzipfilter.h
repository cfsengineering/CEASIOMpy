
/* Copyright (C) 2017 David Eller <david@larosterna.com>
 *
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */

#ifndef GENUA_PARALLELZIPFILTER_H
#define GENUA_PARALLELZIPFILTER_H

#include "forward.h"
#include "parallelfilter.h"
#include "propmacro.h"

class ParallelDeflateFilter : public ParallelFilter
{
public:

  /// initialize
  ParallelDeflateFilter();

  /// compress a single chunk
  void process(ParallelFilter::Chunk &c);

private:

  /// zip compression level
  GENUA_PROP_INI(int, level, 1)
};

class ParallelInflateFilter : public ParallelFilter
{
public:

  /// initialize
  ParallelInflateFilter();

  /// retrieve a chunk
  Chunk nextChunk(std::istream &in);

  /// retrieve a chunk
  Chunk nextChunk(ParallelFilter::ConstBlob &b);

  /// compress a single chunk
  void process(ParallelFilter::Chunk &c);
};

#endif // PARALLELZIPFILTER_H
