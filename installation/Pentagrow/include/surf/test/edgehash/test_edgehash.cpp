/** \file test_edgehash.cpp
 *
 *  \brief Time set implementations to index DcEdge.
 *
 *  This test exercises different hash set implementations on a workload
 *  which is derived from Delaunay mesh generation process, with repeated
 *  insert, lookup and (few) erasure operations.
 *
 *  Preliminary result: DcEdgeTable is between 1.5x and 2x faster than
 *  boost::has_set for this particular workload.
 **/

#include <iostream>
#include <surf/dcedgetable.h>
#include <genua/timing.h>
#include <genua/rng.h>

using namespace std;

std::vector<DcEdge> edges;

const size_t step = 21;
const size_t nlook = 37;
const size_t nerase = 5;

template <class Table>
size_t exercise_table(Table &map)
{
  size_t nfound = 0;
  size_t nadd = 0;
  while (nadd+step < edges.size()) {

    for (size_t i=0; i<step; ++i)
      map.insert( &edges[nadd+i] );
    nadd += step;

    IntRng rng(0, nadd);
    for (size_t i=0; i<nlook; ++i) {
      const DcEdge & e( edges[rng()] );
      DcEdge *pe = map.find(e.source(), e.target());
      nfound += (pe != nullptr);
    }

    for (size_t i=0; i<nerase; ++i) {
      const DcEdge &e1( edges[rng()] );
      map.erase( e1.source(), e1.target() );
    }
  }

  // traverse the map once
  typename Table::Iterator itr( map.begin() );
  typename Table::Iterator last( map.end() );
  for (; itr != last; ++itr) {
    DcEdge *pe = *itr;
    if (pe->source() == 937)
      ++nfound;
  }

  return nfound;
}

template <class Table>
void check_table(Table &tab)
{
  const size_t n = 100;
  for (size_t i=0; i<n; ++i)
    tab.insert( &edges[i] );

  size_t found = 0;
  for (size_t i=0; i<n; ++i)
    found += (tab.find(edges[i].source(), edges[i].target()) != nullptr);

  if (found == n)
    cout << "OK: Found all inserted edges." << endl;
  else
    cout << "F!: Found " << found << "/" << n << endl;

  for (size_t i=0; i<n; i+=2)
    tab.erase(edges[i].source(), edges[i].target());

  if (tab.size() != n/2)
    cout << "Size mismatch after erase: " << tab.size() << " != " << n/2 << endl;

  found = 0;
  for (size_t i=0; i<n; ++i) {
    DcEdge *pe = tab.find(edges[i].source(), edges[i].target());
    found += (pe == nullptr) ^ (i & 0x1);
  }

  if (found == n)
    cout << "OK: All lookup results correct after erase." << endl;
  else
    cout << "F!: " << found << "/" << n << " lookups correct." << endl;
}

int main(int argc, char *argv[])
{
  size_t workingSet = 5850000;
  size_t maxVertexIndex = workingSet / 3;

  Wallclock clk;

  clk.start();
  IntRng rng(0, maxVertexIndex);
  edges.reserve(4096);
  for (size_t i=0; i<workingSet; ++i)
    edges.emplace_back( rng(), rng() );
  float oht = clk.stop();
  cout << "Edge creation: " << workingSet/clk.elapsed() << " edges/s" << endl;

  {
    cout << "DcEdgeOpenTable:" << endl;
    DcEdgeOpenTable ctab;
    check_table(ctab);
  }

  {
    cout << "DcEdgeHashTable:" << endl;
    DcEdgeHashTable ctab;
    check_table(ctab);
  }

  // based on integer map
  clk.start();
  DcEdgeOpenTable table( 4096 );
  exercise_table(table);
  clk.stop();

  cout << "DcEdgeTable : " << workingSet / (clk.elapsed() - oht)
       << " edges/s" << endl;

  // a boost::unordered_set
  clk.start();
  DcEdgeHashTable hash( 4096 );
  exercise_table(hash);
  clk.stop();

  cout << "boost::unordered_set : " << workingSet / (clk.elapsed() - oht)
       << " edges/s" << endl;

  return 0;
}
