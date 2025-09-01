/*
  [auto_generated]
  boost/numeric/odeint/external/eigen/eigen_algebra.hpp

  [begin_description]
  tba.
  [end_description]

  Copyright 2013 Christian Shelton
  Copyright 2013 Karsten Ahnert

  Distributed under the Boost Software License, Version 1.0.
  (See accompanying file LICENSE_1_0.txt or
  copy at http://www.boost.org/LICENSE_1_0.txt)
*/


#ifndef BOOST_NUMERIC_ODEINT_EXTERNAL_EIGEN_EIGEN_ALGEBRA_HPP_INCLUDED
#define BOOST_NUMERIC_ODEINT_EXTERNAL_EIGEN_EIGEN_ALGEBRA_HPP_INCLUDED

#include <eeigen/Dense>
#include <boost/numeric/odeint/algebra/vector_space_algebra.hpp>

// Necessary routines for eeigen matrices to work with vector_space_algebra
// from odeint
// (that is, it lets odeint treat the eigen matrices correctly, knowing
// how to add, multiply, compute the norm, etc)

namespace eeigen {


template<typename D>
inline const
typename eeigen::CwiseUnaryOp<
          typename eeigen::internal::scalar_add_op<
               typename eeigen::internal::traits<D>::Scalar>,
          const D >
operator+(const typename eeigen::MatrixBase<D> &m,
          const typename eeigen::internal::traits<D>::Scalar &s) {
     return eeigen::CwiseUnaryOp<
          typename eeigen::internal::scalar_add_op<
               typename eeigen::internal::traits<D>::Scalar>,
          const D >(m.derived(),eeigen::internal::scalar_add_op<
                    typename eeigen::internal::traits<D>::Scalar>(s));
}

template<typename D>
inline const
typename eeigen::CwiseUnaryOp<
          typename eeigen::internal::scalar_add_op<
               typename eeigen::internal::traits<D>::Scalar>,
          const D >
operator+(const typename eeigen::internal::traits<D>::Scalar &s,
const typename eeigen::MatrixBase<D> &m) {
     return eeigen::CwiseUnaryOp<
          typename eeigen::internal::scalar_add_op<
               typename eeigen::internal::traits<D>::Scalar>,
          const D >(m.derived(),eeigen::internal::scalar_add_op<
                    typename eeigen::internal::traits<D>::Scalar>(s));
}



template<typename D1,typename D2>
inline const
typename eeigen::CwiseBinaryOp<
    typename eeigen::internal::scalar_quotient_op<
        typename eeigen::internal::traits<D1>::Scalar>,
    const D1, const D2>
operator/(const eeigen::MatrixBase<D1> &x1, const eeigen::MatrixBase<D2> &x2) {
    return x1.cwiseQuotient(x2);
}


template< typename D >
inline const 
typename eeigen::CwiseUnaryOp<
    typename eeigen::internal::scalar_abs_op<
        typename eeigen::internal::traits< D >::Scalar > ,
        const D >
abs( const eeigen::MatrixBase< D > &m ) {
    return m.cwiseAbs();
}



} // end eeigen namespace





namespace boost {
namespace numeric {
namespace odeint {

template<typename B,int S1,int S2,int O, int M1, int M2>
struct vector_space_norm_inf< eeigen::Matrix<B,S1,S2,O,M1,M2> >
{
    typedef B result_type;
    result_type operator()( const eeigen::Matrix<B,S1,S2,O,M1,M2> &m ) const
    {
        return m.template lpNorm<eeigen::Infinity>();
    }
};

} } } // end boost::numeric::odeint namespace

#endif // BOOST_NUMERIC_ODEINT_EXTERNAL_EIGEN_EIGEN_ALGEBRA_HPP_INCLUDED
