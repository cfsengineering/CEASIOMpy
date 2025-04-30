#ifndef GENUA_YAML_H
#define GENUA_YAML_H

#include "yaml-cpp/yaml.h"
#include "svector.h"
#include "smatrix.h"
#include "dvector.h"
#include "point.h"

/** Creates a new YAML document.
 *
 * YamlDoc writes a new document opening mark to the emitter and closes
 * the document on destruction.
 * This class is a very thin wrapper around the yaml-cpp library.
 *
 * \sa YamlMap, YamlSeq
 */
class YamlDoc
{
public:

  /// construct and open document with emitter
  YamlDoc(YAML::Emitter &emt) : m_emt(emt)
  {
    m_emt << YAML::BeginDoc;
  }

  /// close document
  ~YamlDoc() {
    m_emt << YAML::EndDoc;
  }

  /// access emitter
  YAML::Emitter &emitter() {return m_emt;}

private:

  /// emitter to write to
  YAML::Emitter &m_emt;
};

/** Creates a new YAML sequence.
 *
 * YamlDoc begins a new sequence on the stream and terminates it on destruction.
 * This class is a very thin wrapper around the yaml-cpp library.
 *
 * \sa YamlMap, YamlDoc
 */
class YamlSeq
{
public:

  YamlSeq(YAML::Emitter &emt, bool flow = false) : m_emt(emt)
  {
    if (flow)
      m_emt << YAML::Flow;
    m_emt << YAML::BeginSeq;
  }

  ~YamlSeq() {
    m_emt << YAML::EndSeq;
  }

  template <typename T>
  YamlSeq &add(const T& value) {
    m_emt << value;
    return *this;
  }

  template <typename Iterator>
  YamlSeq &add(Iterator first, Iterator last) {
    for (Iterator itr = first; itr != last; ++itr)
      m_emt << *itr;
    return *this;
  }

  /// access emitter
  YAML::Emitter &emitter() {return m_emt;}

private:

  /// emitter to write to
  YAML::Emitter &m_emt;
};

/** Creates a new YAML map.
 *
 * YamlMap begins a new kay-value on the stream and terminates it on destruction.
 * This class is a very thin wrapper around the yaml-cpp library.
 *
 * \sa YamlSeq, YamlDoc
 */
class YamlMap
{
public:

  YamlMap(YAML::Emitter &emt) : m_emt(emt)
  {
    m_emt << YAML::BeginMap;
  }

  ~YamlMap() {
    m_emt << YAML::EndMap;
  }

  YAML::Emitter &operator[](const char *key) {
    m_emt << YAML::Key << key << YAML::Value;
    return m_emt;
  }

  template <typename T>
  YamlMap &add(const char *key, const T& value) {
    m_emt << YAML::Key << key << YAML::Value << value;
    return *this;
  }

  template <typename Iterator>
  YamlMap &add(const char *key, Iterator first, Iterator last, bool flow = false) {
    m_emt << YAML::Key << key << YAML::Value;
    if (flow)
      m_emt << YAML::Flow;
    m_emt << YAML::BeginSeq;
    for (Iterator itr = first; itr != last; ++itr)
      m_emt << *itr;
    m_emt << YAML::EndSeq;
    return *this;
  }

  /// access emitter
  YAML::Emitter &emitter() {return m_emt;}

private:

  /// emitter to write to
  YAML::Emitter &m_emt;
};

// -------------------- overloads -------------------------------------------

template <uint N, typename FloatType>
inline YAML::Emitter& operator << (YAML::Emitter& out,
                                   const SVector<N,FloatType>& v)
{
  out << YAML::Flow;
  out << YAML::BeginSeq;
  for (uint k=0; k<N; ++k)
    out << v[k];
  out << YAML::EndSeq;
  return out;
}

template <uint M, uint N, typename FloatType>
inline YAML::Emitter& operator << (YAML::Emitter& out,
                                   const SMatrix<M,N,FloatType>& v)
{
  out << YAML::BeginSeq;
  for (uint i=0; i<M; ++i) {
    out << YAML::Flow;
    out << YAML::BeginSeq;
    for (uint j=0; j<N; ++j)
      out << v(i,j);
    out << YAML::EndSeq;
  }
  out << YAML::EndSeq;
  return out;
}

template <typename FloatType>
inline YAML::Emitter& operator << (YAML::Emitter& out,
                                   const DVector<FloatType>& v)
{
  out << YAML::Flow;
  out << YAML::BeginSeq;
  const size_t n = v.size();
  for (size_t k=0; k<n; ++k)
    out << v[k];
  out << YAML::EndSeq;
  return out;
}

template <uint N, class FloatType>
inline YAML::Emitter& operator << (YAML::Emitter& out,
                                   const PointList<N,FloatType>& v)
{
  out << YAML::BeginSeq;
  const size_t m = v.size();
  for (size_t i=0; i<m; ++i) {
    out << YAML::Flow;
    out << YAML::BeginSeq;
    for (uint k=0; k<N; ++k)
      out << v[i][k];
    out << YAML::EndSeq;
  }
  out << YAML::EndSeq;
  return out;
}

namespace YAML
{

template <uint N, typename FloatType>
struct convert<SVector<N,FloatType> > {
  static Node encode(const SVector<N,FloatType> &a) {
    Node node;
    node.SetStyle(EmitterStyle::Flow);
    for (uint k=0; k<N; ++k)
      node.push_back(a[k]);
    return node;
  }
  static bool decode(const Node& node, SVector<N,FloatType> &a) {
    if (node.IsSequence() and node.size() == N) {
      for (uint k=0; k<N; ++k)
        a[k] = node[k].as<FloatType>();
      return true;
    }
    return false;
  }
};

template <uint M, uint N, typename FloatType>
struct convert<SMatrix<M,N,FloatType> > {
  static Node encode(const SMatrix<M,N,FloatType> &a) {
    Node node;
    for (uint i=0; i<M; ++i) {
      Node row;
      row.SetStyle(EmitterStyle::Flow);
      for (uint j=0; j<N; ++j)
        row.push_back(a(i,j));
      node.push_back(row);
    }
    return node;
  }
  static bool decode(const Node& node, SMatrix<M,N,FloatType> &a) {
    if (node.IsSequence() and node.size() == M) {
      for (uint i=0; i<M; ++i) {
        Node row = node[i];
        assert(row.IsSequence() and row.size() == N);
        for (uint j=0; j<N; ++j)
          a(i,j) = row[j].as<FloatType>();
      }
      return true;
    }
    return false;
  }
};

template <uint N, typename FloatType>
struct convert<PointList<N,FloatType> > {
  static Node encode(const PointList<N,FloatType> &a) {
    Node node;
    const size_t np = a.size();
    for (size_t i=0; i<np; ++i)
      node.push_back(a[i]);
    return node;
  }
  static bool decode(const Node& node, PointList<N,FloatType> &a) {
    if (node.IsSequence()) {
      const size_t np = node.size();
      a.resize(np);
      for (size_t i=0; i<np; ++i)
        a[i] = node[i].as<SVector<N,FloatType> >();
      return true;
    }
    return false;
  }
};

template <typename FloatType>
struct convert<DVector<FloatType> > {
  static Node encode(const DVector<FloatType> &a) {
    Node node;
    if (a.size() < 16)
      node.SetStyle(EmitterStyle::Flow);
    const uint n = a.size();
    for (uint k=0; k<n; ++k)
      node.push_back(a[k]);
    return node;
  }
  static bool decode(const Node& node, DVector<FloatType> &a) {
    if (node.IsSequence()) {
      const uint n = node.size();
      a.allocate(n);
      for (uint k=0; k<n; ++k)
        a[k] = node[k].as<FloatType>();
      return true;
    }
    return false;
  }
};

template <typename FloatType>
struct convert<DMatrix<FloatType> > {
  static Node encode(const DMatrix<FloatType> &a) {
    Node node;
    size_t m = a.nrows();
    size_t n = a.ncols();
    for (size_t i=0; i<m; ++i) {
      Node row;
      row.SetStyle(EmitterStyle::Flow);
      for (size_t j=0; j<n; ++j)
        row.push_back(a(i,j));
      node.push_back(row);
    }
    return node;
  }
  static bool decode(const Node& node, DMatrix<FloatType> &a) {
    size_t m = a.nrows();
    size_t n = a.ncols();
    if (node.IsSequence() and node.size() == m) {
      for (size_t i=0; i<m; ++i) {
        Node row = node[i];
        assert(row.IsSequence() and row.size() == n);
        for (size_t j=0; j<n; ++j)
          a(i,j) = row[j].as<FloatType>();
      }
      return true;
    }
    return false;
  }
};

}

#endif // YAML_H
