#include <iostream>
#include <eeigen/Core>
#include <eeigen/Dense>
#include <eeigen/IterativeLinearSolvers>
#include <unsupported/eeigen/IterativeSolvers>

class MatrixReplacement;
using eeigen::SparseMatrix;

namespace eeigen {
namespace internal {
  // MatrixReplacement looks-like a SparseMatrix, so let's inherits its traits:
  template<>
  struct traits<MatrixReplacement> :  public eeigen::internal::traits<eeigen::SparseMatrix<double> >
  {};
}
}

// Example of a matrix-free wrapper from a user type to eeigen's compatible type
// For the sake of simplicity, this example simply wrap a eeigen::SparseMatrix.
class MatrixReplacement : public eeigen::EigenBase<MatrixReplacement> {
public:
  // Required typedefs, constants, and method:
  typedef double Scalar;
  typedef double RealScalar;
  typedef int StorageIndex;
  enum {
    ColsAtCompileTime = eeigen::Dynamic,
    MaxColsAtCompileTime = eeigen::Dynamic,
    IsRowMajor = false
  };

  Index rows() const { return mp_mat->rows(); }
  Index cols() const { return mp_mat->cols(); }

  template<typename Rhs>
  eeigen::Product<MatrixReplacement,Rhs,eeigen::AliasFreeProduct> operator*(const eeigen::MatrixBase<Rhs>& x) const {
    return eeigen::Product<MatrixReplacement,Rhs,eeigen::AliasFreeProduct>(*this, x.derived());
  }

  // Custom API:
  MatrixReplacement() : mp_mat(0) {}

  void attachMyMatrix(const SparseMatrix<double> &mat) {
    mp_mat = &mat;
  }
  const SparseMatrix<double> my_matrix() const { return *mp_mat; }

private:
  const SparseMatrix<double> *mp_mat;
};


// Implementation of MatrixReplacement * eeigen::DenseVector though a specialization of internal::generic_product_impl:
namespace eeigen {
namespace internal {

  template<typename Rhs>
  struct generic_product_impl<MatrixReplacement, Rhs, SparseShape, DenseShape, GemvProduct> // GEMV stands for matrix-vector
  : generic_product_impl_base<MatrixReplacement,Rhs,generic_product_impl<MatrixReplacement,Rhs> >
  {
    typedef typename Product<MatrixReplacement,Rhs>::Scalar Scalar;

    template<typename Dest>
    static void scaleAndAddTo(Dest& dst, const MatrixReplacement& lhs, const Rhs& rhs, const Scalar& alpha)
    {
      // This method should implement "dst += alpha * lhs * rhs" inplace,
      // however, for iterative solvers, alpha is always equal to 1, so let's not bother about it.
      assert(alpha==Scalar(1) && "scaling is not implemented");
      EIGEN_ONLY_USED_FOR_DEBUG(alpha);

      // Here we could simply call dst.noalias() += lhs.my_matrix() * rhs,
      // but let's do something fancier (and less efficient):
      for(Index i=0; i<lhs.cols(); ++i)
        dst += rhs(i) * lhs.my_matrix().col(i);
    }
  };

}
}

int main()
{
  int n = 10;
  eeigen::SparseMatrix<double> S = eeigen::MatrixXd::Random(n,n).sparseView(0.5,1);
  S = S.transpose()*S;

  MatrixReplacement A;
  A.attachMyMatrix(S);

  eeigen::VectorXd b(n), x;
  b.setRandom();

  // Solve Ax = b using various iterative solver with matrix-free version:
  {
    eeigen::ConjugateGradient<MatrixReplacement, eeigen::Lower|eeigen::Upper, eeigen::IdentityPreconditioner> cg;
    cg.compute(A);
    x = cg.solve(b);
    std::cout << "CG:       #iterations: " << cg.iterations() << ", estimated error: " << cg.error() << std::endl;
  }

  {
    eeigen::BiCGSTAB<MatrixReplacement, eeigen::IdentityPreconditioner> bicg;
    bicg.compute(A);
    x = bicg.solve(b);
    std::cout << "BiCGSTAB: #iterations: " << bicg.iterations() << ", estimated error: " << bicg.error() << std::endl;
  }

  {
    eeigen::GMRES<MatrixReplacement, eeigen::IdentityPreconditioner> gmres;
    gmres.compute(A);
    x = gmres.solve(b);
    std::cout << "GMRES:    #iterations: " << gmres.iterations() << ", estimated error: " << gmres.error() << std::endl;
  }

  {
    eeigen::DGMRES<MatrixReplacement, eeigen::IdentityPreconditioner> gmres;
    gmres.compute(A);
    x = gmres.solve(b);
    std::cout << "DGMRES:   #iterations: " << gmres.iterations() << ", estimated error: " << gmres.error() << std::endl;
  }

  {
    eeigen::MINRES<MatrixReplacement, eeigen::Lower|eeigen::Upper, eeigen::IdentityPreconditioner> minres;
    minres.compute(A);
    x = minres.solve(b);
    std::cout << "MINRES:   #iterations: " << minres.iterations() << ", estimated error: " << minres.error() << std::endl;
  }
}
