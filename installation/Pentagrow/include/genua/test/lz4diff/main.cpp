
#include "lz4.h"
#include <genua/xcept.h>
#include <genua/rng.h>
#include <iostream>
#include <fstream>
#include <cstdint>

using namespace std;

// number of packets compressed in delta form
constexpr int delta_length = 32;

double a[18];
double w[18];
double phi[18];

struct Packet
{
  uint64_t timestamp;
  int16_t payload[6*3];

  // substract baseline packet
  void operator-= (const Packet &b) {
    timestamp -= b.timestamp;
    for (int k=0; k<18; ++k)
      payload[k] -= b.payload[k];
  }

  // generate pseudo-data
  void generate(double t) {
    timestamp = 4295*t;
    for (int k=0; k<18; ++k)
      payload[k] = a[k]*sin(w[k]*t + phi[k]);
  }
} __attribute__ ((packed));

void transpose_block(const char *x, char *xt)
{
  constexpr int pb = sizeof(Packet);
  for (int i=0; i<delta_length; ++i) {
    for (int j=0; j<pb; ++j)
      xt[j*delta_length+i] = x[i*pb+j];
  }
}

int main(int argc, char *argv[])
{
  FloatRng rng(0.0, 1.0);
  for (int k=0; k<18; ++k) {
    w[k] = 100.0 *2*M_PI * rng();
    a[k] = (rng() - 0.5) * INT16_MAX;
    phi[k] = rng() * 2*M_PI;
  }

  size_t bbytes = delta_length*sizeof(Packet);
  size_t nbwork = LZ4_compressBound(bbytes);
  vector<char> work(nbwork), twork(bbytes);

  try {

    size_t n = 1024;
    double dt = 1.0/4000;
    std::vector<Packet> packets(n);
    for (size_t i=0; i<n; ++i)
      packets[i].generate( dt*i );

    cout << "Delta block length: " << delta_length << endl;
    cout << "Block size: " << bbytes << endl;
    cout << "Input size: " << n*sizeof(Packet) << endl;

    // write binray block for testing
    {
      ofstream os("rawblock.dat", ios_base::binary);
      os.write((const char *) &packets[0], bbytes);
      os.close();
    }

    vector<char> out1;
    out1.reserve(n*sizeof(Packet));
    size_t nb = n/delta_length;
    for (size_t ib=0; ib<nb; ++ib) {
      const char *src = (const char *) &packets[delta_length*ib];
      transpose_block( src, (char *) &twork[0] );
      int nc = LZ4_compress_default((const char *) &twork[0], &work[0],
          bbytes, work.capacity());
      cout << "Block " << ib << " compressed: " << nc << endl;
      const char *p = (const char *) &nc;
      out1.insert(out1.end(), p, p+4);
      out1.insert(out1.end(), &work[0], &work[nc]);
    }

    cout << "Compressed size: " << out1.size() << endl;

    // transform to delta form
    vector<Packet> pdelta(n);
    for (size_t ib=0; ib<nb; ++ib) {
      size_t offs = delta_length*ib;
      pdelta[offs] = packets[offs];
      for (int j=1; j<delta_length; ++j) {
        pdelta[offs+j] = packets[offs+j];
        pdelta[offs+j] -= packets[offs+j-1];
      }
    }

    // write binray block for testing
    {
      ofstream os("deltablock.dat", ios_base::binary);
      os.write((const char *) &pdelta[0], bbytes);
      os.close();
    }

    out1.clear();
    out1.reserve(n*sizeof(Packet));
    for (size_t ib=0; ib<nb; ++ib) {
      const char *src = (const char *) &pdelta[delta_length*ib];
      transpose_block( src, (char *) &twork[0] );
      int nc = LZ4_compress_default((const char *) &twork[0], &work[0],
          bbytes, work.capacity());
      // cout << "Block " << ib << " compressed: " << nc << endl;
      const char *p = (const char *) &nc;
      out1.insert(out1.end(), p, p+4);
      out1.insert(out1.end(), &work[0], &work[nc]);
    }

    cout << "Delta-compressed size: " << out1.size() << endl;



  } catch (std::exception &xcp) {
    cerr << "Exception: " << xcp.what() << endl;
    return EXIT_FAILURE;
  }


  return EXIT_SUCCESS;
}
