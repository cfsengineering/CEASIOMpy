
#include <genua/packetstream.h>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <fstream>

using namespace std;

#define PACKETSIZE 512

class StreamEvent : public StreamPacket<PACKETSIZE>
{
public:

  enum { Text = 1,
         Coordinates };

  StreamEvent() : StreamPacket<PACKETSIZE>() {}
  StreamEvent(uint64_t type, uint64_t size, const char *content)
    : StreamPacket<PACKETSIZE>(type, size, content) {}

};

class TextEvent : public StreamEvent
{
public:
  TextEvent(const std::string &s) : StreamEvent(StreamEvent::Text,
                                                s.size(), &s[0])
  {
    assert(s.size() <= capacity());
  }
};

class CoordEvent : public StreamEvent
{
public:
  CoordEvent(int n, const float x[]) : StreamEvent(StreamEvent::Coordinates,
                                                   n*sizeof(float),
                                                   (const char *) x)
  {
    assert(n*sizeof(float) <= capacity());
  }
};

int main(int argc, char *argv[])
{

  typedef PacketBuffer<PACKETSIZE> BufferType;

  try {

    Wallclock clk;

    if (argc < 2) {

      int npack = 200000;

      clk.start();

      ofstream out("packets.dat");
      BufferType buffer(&out, 1024);
      for (int i=0; i<npack; ++i) {
        if (i%34 == 0) {
          buffer << TextEvent("Text event "+str(i/34+1));
        } else {
          float x[16];
          for (int k=0; k<16; ++k)
            x[k] = 100*i + k;
          buffer << CoordEvent(16, x);
        }
      }
      buffer.sync();

      clk.stop();

      cout << "Write speed: " << npack / clk.elapsed()
           << " packets/second." << endl;

    } else {

      float t(0.0f);

      ifstream in(argv[1]);
      BufferType buffer(&in, 1024);

      StreamEvent event;
      buffer >> event;
      size_t n(0);
      while (event.valid()) {
        if (n < 1000) {
          if (event.type() == StreamEvent::Text) {
            string s( event.pointer(), event.payload() );
            cout << n << " text event, content: " << s << endl;
          } else if (event.type() == StreamEvent::Coordinates) {
            float x[4];
            memcpy(x, event.pointer(), sizeof(x));
            cout << n << " coord event, content: ";
            for (int k=0; k<4; ++k)
              cout << x[k] << ' ';
            cout << endl;
          }
        }
        clk.start();
        buffer >> event;
        t += clk.stop();
        ++n;
      }

      clk.stop();

      cout << "Read speed: " << n / t
           << " packets/second." << endl;

    }

  } catch (Error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
