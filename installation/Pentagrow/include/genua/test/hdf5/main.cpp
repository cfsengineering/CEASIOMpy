
#include <genua/forward.h>
#include <genua/timing.h>
#include <genua/xcept.h>
#include <genua/hdf5file.h>
#include <genua/dmatrix.h>
#include <iostream>

using namespace std;

int test_write()
{
  Hdf5File h5file;
  //bool stat = h5file.create("C:/Users/david/Documents\Develop\src\genua\test\hdf5\simple.h5");
  bool stat = h5file.create("./simple.h5");
  if (not stat) {
    cerr << "Could not create HDF5 file." << endl;
    return EXIT_FAILURE;
  } else
    cout << "File created." << endl;

  Hdf5Group grp = h5file.createGroup("/g1");
  if (grp.valid())
    cout << "Group created." << endl;
  else {
    cerr << "Could not create group." << endl;
    return EXIT_FAILURE;
  }

  int m = 356;
  int n = 6;
  Matrix x(m, n);
  for (int j=0; j<n; ++j)
    for (int i=0; i<m; ++i)
      x(i,j) = 1000*j + i;

  Hdf5Dataset ds = grp.createDataset("mtx", TypeCode::of<double>(),
                                            x.nrows(), x.ncols());
  if (not ds.valid()) {
    cout << "Cout not create dataset" << endl;
    return EXIT_FAILURE;
  }

  stat = ds.write(x.pointer());
  if (not stat) {
    cerr << "Could not write dataset." << endl;
    return EXIT_FAILURE;
  } else
    cout << "Dataset written." << endl;

  //Hdf5Dataset ds = grp.createDataset("mtx", TypeCode::of<double>(),
  //                                   x.nrows(), x.ncols());

  x = 0.0;
  ds.writeColumn(2, x.colpointer(2));

  //h5file.close();

  return EXIT_SUCCESS;
}

int test_read()
{
  Hdf5File h5file;
  bool stat = h5file.open("./simple.h5");
  if (not stat) {
    cerr << "Could not open HDF5 file." << endl;
    return EXIT_FAILURE;
  } else
    cout << "File opened" << endl;

  hsize_t dim[2];
  Hdf5Dataset ds = h5file.openDataset("/g1/mtx");
  int r = ds.dimensions(dim);

  if (r != 2) {
    cout << "Unexpected rank: " << r << endl;
    return EXIT_FAILURE;
  }

  cout << "Dimensions: " << dim[0] << "x" << dim[1] << endl;

  Vector a(dim[0]);
  stat = ds.readColumn(0, a.pointer());
  if (!stat) {
    cout << "Failed to read column." << endl;
    return EXIT_FAILURE;
  }

  cout << "a: " << a << endl;

  return EXIT_SUCCESS;
}

int main(int argc, char *argv[])
{

  try {

    int stat = test_write();
    if (stat == EXIT_FAILURE)
      return EXIT_FAILURE;

    return test_read();

  } catch (std::exception &xcp) {
    cerr << "Exception: " << xcp.what() << endl;
    return EXIT_FAILURE;
  }


  return EXIT_SUCCESS;
}
