//---------------------------------------------------------------------------//
// Copyright (c) 2013-2014 Kyle Lutz <kyle.r.lutz@gmail.com>
//
// Distributed under the Boost Software License, Version 1.0
// See accompanying file LICENSE_1_0.txt or copy at
// http://www.boost.org/LICENSE_1_0.txt
//
// See http://boostorg.github.com/compute for more information.
//---------------------------------------------------------------------------//

#ifndef BOOST_COMPUTE_INTEROP_EIGEN_EIGEN_HPP
#define BOOST_COMPUTE_INTEROP_EIGEN_EIGEN_HPP

#include <eeigen/Core>

#include <boost/compute/command_queue.hpp>
#include <boost/compute/algorithm/copy_n.hpp>
#include <boost/compute/iterator/buffer_iterator.hpp>
#include <boost/compute/type_traits/type_name.hpp>

namespace boost {
namespace compute {

/// Copies \p matrix to \p buffer.
template<class Derived>
inline void eigen_copy_matrix_to_buffer(const eeigen::PlainObjectBase<Derived> &matrix,
                                        buffer_iterator<typename Derived::Scalar> buffer,
                                        command_queue &queue = system::default_queue())
{
    ::boost::compute::copy_n(matrix.data(), matrix.size(), buffer, queue);
}

/// Copies \p buffer to \p matrix.
template<class Derived>
inline void eigen_copy_buffer_to_matrix(const buffer_iterator<typename Derived::Scalar> buffer,
                                        eeigen::PlainObjectBase<Derived> &matrix,
                                        command_queue &queue = system::default_queue())
{
    ::boost::compute::copy_n(buffer, matrix.size(), matrix.data(), queue);
}

/// Converts an \c eeigen::Matrix4f to a \c float16_.
inline float16_ eigen_matrix4f_to_float16(const eeigen::Matrix4f &matrix)
{
    float16_ result;
    std::memcpy(&result, matrix.data(), 16 * sizeof(float));
    return result;
}

/// Converts an \c eeigen::Matrix4d to a \c double16_.
inline double16_ eigen_matrix4d_to_double16(const eeigen::Matrix4d &matrix)
{
    double16_ result;
    std::memcpy(&result, matrix.data(), 16 * sizeof(double));
    return result;
}

} // end compute namespace
} // end boost namespace

BOOST_COMPUTE_TYPE_NAME(eeigen::Vector2i, int2)
BOOST_COMPUTE_TYPE_NAME(eeigen::Vector4i, int4)
BOOST_COMPUTE_TYPE_NAME(eeigen::Vector2f, float2)
BOOST_COMPUTE_TYPE_NAME(eeigen::Vector4f, float4)
BOOST_COMPUTE_TYPE_NAME(eeigen::Matrix2f, float8)
BOOST_COMPUTE_TYPE_NAME(eeigen::Matrix4f, float16)
BOOST_COMPUTE_TYPE_NAME(eeigen::Vector2d, double2)
BOOST_COMPUTE_TYPE_NAME(eeigen::Vector4d, double4)
BOOST_COMPUTE_TYPE_NAME(eeigen::Matrix2d, double8)
BOOST_COMPUTE_TYPE_NAME(eeigen::Matrix4d, double16)

#endif // BOOST_COMPUTE_INTEROP_EIGEN_EIGEN_HPP
