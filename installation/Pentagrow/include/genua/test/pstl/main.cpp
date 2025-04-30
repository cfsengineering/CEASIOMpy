
#include <genua/forward.h>
#include <genua/pstl.h>
#include <genua/basicedge.h>
#include <genua/rng.h>
#include <genua/timing.h>

#include <iostream>

using namespace std;

int main(int argc, char *argv[])
{
  Wallclock clk;

  cout << "Generating test problem..." << endl;

  size_t nv = 200000;
  if (argc > 1)
    nv = stoul(argv[1]);

  size_t ne = 3*nv;
  IntRng rng(0, nv-1);
  BasicEdgeArray edges(ne);
  for (size_t i=0; i<ne; ++i) {
    uint src = rng();
    uint trg = rng();

    // generate some duplicates
    if (src%3 == 0 and src < i) {
      edges[i] = edges[src];
    } else {
      edges[i].assign(src, trg);
    }
  }

  BasicEdgeArray e1(edges), e2(edges);
  BasicEdgeArray t1(ne), t2(ne);

  cout << "Serial execution: ";
  clk.start();
  sort(e1.begin(), e1.end());
  e1.erase( unique(e1.begin(), e1.end()), e1.end() );
  double etserial = clk.stop();
  cout << etserial << "s." << endl;
  cout << "Result: " << e1.size() << endl;

  auto policy = std::execution::par;

  cout << "Parallel execution: ";
  clk.start();
  sort( policy, e2.begin(), e2.end());
  auto last = unique_copy( policy, e2.begin(), e2.end(),
                           t1.begin() );
  size_t neds = std::distance(t1.begin(), last);
  copy( policy, t1.begin(), last, e2.begin() );
  e2.erase( e2.begin(), e2.begin() + neds );
  double etpar = clk.stop();
  cout << etpar << "s." << endl;
  cout << "Result: " << neds << endl;

  cout << "Speed-up: " << etserial/etpar << endl;

  return EXIT_SUCCESS;
}
