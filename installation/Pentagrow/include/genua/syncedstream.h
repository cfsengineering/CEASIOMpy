#ifndef GENUA_SYNCEDSTREAM_H
#define GENUA_SYNCEDSTREAM_H

#include "forward.h"
#include <boost/iostreams/stream.hpp>
#include <boost/iostreams/stream_buffer.hpp>
#include <boost/iostreams/categories.hpp>
#include <boost/iostreams/positioning.hpp>
#include <iosfwd>
#include <mutex>
#include <vector>

namespace boost {
  namespace iostreams {
    struct dual_seekable_device_tag : virtual device_tag, dual_seekable {};
  }
}

/** Synchronized stream device.
  *
  * A lock-protected stream which simply works on a character vector but can be
  * used by multiple threads simultaneously.
  *
  *
  * \ingroup io
  */
class SyncedStreamDevice
{
public:

  typedef char                                        char_type;
  typedef boost::iostreams::dual_seekable_device_tag  category;
  typedef boost::iostreams::stream_offset             stream_offset;

  /// default initialization
  SyncedStreamDevice() = default;

  /// copy the contents and use a new mutex
  SyncedStreamDevice(const SyncedStreamDevice &a);

  /// read from device into s
  std::streamsize read(char* s, std::streamsize n);

  /// write s into device (may reallocate)
  std::streamsize write(const char* s, std::streamsize n);

  /// move position
  stream_offset seek(stream_offset off, std::ios_base::seekdir way,
                     std::ios_base::openmode which);

  /// write contents to file
  void dump(const std::string &fname) const;

  /// return a copy of the contents as a single string
  std::string str() const;

  /// bytes contained
  size_t size() const {return m_contents.size();}

  /// position of read pointer
  size_t rpos() const {return m_rpos;}

  /// position of write pointer
  size_t wpos() const {return m_wpos;}

  /// erase contents, reset position
  void reset();

private:

  /// move position indicator pos
  stream_offset movePos(stream_offset off,
                        std::ios_base::seekdir way, size_t &pos) const;

private:

  /// make sure only one thread accesses device at any one time
  mutable std::mutex m_guard;

  /// character array
  std::vector<char> m_contents;

  /// stream position for reading
  size_t m_rpos = 0;

  /// stream position for writing
  size_t m_wpos = 0;
};

typedef boost::iostreams::stream_buffer<SyncedStreamDevice> SyncedStreamBuffer;
typedef boost::iostreams::stream<SyncedStreamDevice> SyncedStream;

#endif // SYNCEDSTREAM_H
