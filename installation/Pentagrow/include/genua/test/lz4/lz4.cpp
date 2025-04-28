#include <genua/lz4stream.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/timing.h>

#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc != 3) {
      cout << "Usage: " << argv[0] << " input output" << endl;
      return EXIT_FAILURE;
    }

    const size_t bufSize = 16*1024*1024;
    std::vector<char> buffer( bufSize );

    ifstream in;
    ofstream os;

    in.open(argv[1], std::ios::in | std::ios::binary );
    os.open(argv[2], std::ios::out | std::ios::binary );

    if (not in) {
      cout << "Could not open input: " << argv[1] << endl;
      return EXIT_FAILURE;
    }

    if (not os) {
      cout << "Could not open output: " << argv[2] << endl;
      return EXIT_FAILURE;
    }

    Lz4Stream lzs;

    string call(argv[0]);
    if ( call.find("lz4compress") != string::npos ) {

      lzs.openWrite(os);
      size_t bytesRead = 0;
      do {
        in.read(&buffer[0], bufSize);
        bytesRead = in.gcount();
        cout << "Read: " << bytesRead << " eof: " << in.eof() << " ok: " << (bool(in)) << endl;
        lzs.write( os, &buffer[0], bytesRead );
      } while (bytesRead > 0);
      lzs.closeWrite(os);

    } else if (call.find("lz4decompress") != string::npos) {

      if (not lzs.openRead(in)) {
        cout << argv[1] << " not an LZ4 stream." << endl;
        return EXIT_FAILURE;
      }

      size_t blockSize(0);
      do {
        blockSize = lzs.readBlock(in, &buffer[0]);
        if (blockSize > 0)
          os.write(&buffer[0], blockSize);
      } while (blockSize > 0);

      if (not lzs.closeRead(in)) {
        cout << "Checksum mismatch - corrupt file." << endl;
        return EXIT_FAILURE;
      }

    } else {
      cout << "Command not recognized." << endl;
      return EXIT_FAILURE;
    }

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
