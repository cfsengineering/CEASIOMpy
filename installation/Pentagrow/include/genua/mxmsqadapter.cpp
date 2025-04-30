
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "mxmsqadapter.h"
#include "mxmesh.h"

using namespace Mesquite;

// --------------------- MxMsqSectionAdapter -------------------------------

MxMsqSectionAdapter::MxMsqSectionAdapter(MxMeshPtr pmx, uint isec)
  : ArrayMesh(), m_pmx(pmx)
{
  assign(pmx, isec);
}

void MxMsqSectionAdapter::assign(MxMeshPtr pmx, uint isec)
{
  m_pmx = pmx;
  m_fixed.clear();
  m_fixed.resize(m_pmx->nnodes(), 0);

  // mark vertex as fixed if it is part of any other section
  for (uint js=0; js<m_pmx->nsections(); ++js) {
    if (js == isec)
      continue;

    const MxMeshSection &scj( m_pmx->section(js) );
    const uint *v = scj.element(0);
    const size_t nsn = scj.nelements() * scj.nElementNodes();
    for (size_t i=0; i<nsn; ++i)
      m_fixed[v[i]] = 1;
  }

  MxMeshSection &sec( m_pmx->section(isec) );
  double *pvx = m_pmx->nodes().pointer();

  EntityTopology topo;
  switch ( sec.elementType() ) {
  case Mx::Tri3:
  case Mx::Tri6:
    topo = TRIANGLE;
    break;
  case Mx::Quad4:
  case Mx::Quad8:
  case Mx::Quad9:
    topo = QUADRILATERAL;
    break;
  case Mx::Tet4:
  case Mx::Tet10:
    topo = TETRAHEDRON;
    break;
  case Mx::Hex8:
  case Mx::Hex20:
  case Mx::Hex27:
    topo = HEXAHEDRON;
    break;
  case Mx::Penta6:
  case Mx::Penta15:
  case Mx::Penta18:
    topo = PRISM;
    break;
  case Mx::Pyra5:
  case Mx::Pyra14:
    topo = PYRAMID;
    break;
  default:
    topo = POLYHEDRON;
  }

  ArrayMesh::set_mesh( 3, (ulong) m_pmx->nnodes(),
                       pvx, (const int *) &m_fixed[0],
                       (ulong) sec.nelements(),
                       topo,
                       (const ulong *) sec.element(0),
                       false, 0u, (const int *) 0);
}

// --------------------- MxMsqAdapter --------------------------------------

MxMsqAdapter::MxMsqAdapter(MxMeshPtr pmx) : Mesh(), m_helper(0)
{
  m_tags = new MeshImplTags;
  assign(pmx);
}

MxMsqAdapter::~MxMsqAdapter()
{
  delete m_tags;
}

void MxMsqAdapter::assign(MxMeshPtr pmx)
{
  m_pmx = pmx;
  m_vfixed.clear();
  m_vslaved.clear();
  m_vbyte.clear();
  if (not m_pmx)
    return;

  const size_t nn = m_pmx->nnodes();
  m_vfixed.resize(nn, false);
  m_vslaved.resize(nn, false);
  m_vbyte.resize(nn, (unsigned char) 0);

  if ( m_pmx->v2eMap().size() != nn )
    m_pmx->fixate();

//  // create dummy tag for ParallelMesh interface
//  MsqError err;
//  TagHandle lid = tag_create("LOCAL_ID", INT, 1, (const void *) 0, err);
//  MSQ_CHKERR(err);

//  std::vector<int> local_id(nn);
//  std::vector<VertexHandle> vert_array(nn);
//  for (size_t i=0; i<nn; ++i) {
//    local_id[i] = i;
//    vert_array[i] = reinterpret_cast<VertexHandle>( size_t(i) );
//  }
//  tag_set_vertex_data(lid, nn, &vert_array[0],
//                      (const void *) &local_id[0], err);
//  MSQ_CHKERR(err);

  fix_surface_vertices();
}

void MxMsqAdapter::fix_surface_vertices()
{
  const int ns = m_pmx->nsections();
  for (int j=0; j<ns; ++j) {
    const MxMeshSection &sec( m_pmx->section(j) );
    if (not sec.surfaceElements())
      continue;
    Indices uv;
    sec.usedNodes(uv);
    const size_t nsv = uv.size();
    for (size_t i=0; i<nsv; ++i)
      m_vfixed[uv[i]] = true;
  }
}

void MxMsqAdapter::get_all_elements(std::vector<ElementHandle> &elements,
                                    MsqError &err)
{
  err.clear();
  elements.clear();
  if (not m_pmx)
    return;

  const size_t ne = m_pmx->nelements();
  elements.resize(ne);
  for (size_t i=0; i<ne; ++i)
    elements[i] = reinterpret_cast<ElementHandle>( i );
}

void MxMsqAdapter::get_all_vertices(std::vector<VertexHandle> &vertices,
                                    MsqError &err)
{
  err.clear();
  vertices.clear();
  if (not m_pmx)
    return;

  const size_t nn = m_pmx->nnodes();
  vertices.resize(nn);
  for (size_t i=0; i<nn; ++i)
    vertices[i] = reinterpret_cast<VertexHandle>( i );
}

void MxMsqAdapter::vertices_get_fixed_flag(const VertexHandle vert_array[],
                                           std::vector<bool> &fixed_flag_array,
                                           size_t num_vtx, MsqError &err)
{
  err.clear();
  fixed_flag_array.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  fixed_flag_array.resize(num_vtx);
  for (size_t i=0; i<num_vtx; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < m_pmx->nnodes());
    fixed_flag_array[i] = m_vfixed[idx];
  }
}

void MxMsqAdapter::vertices_get_slaved_flag(const VertexHandle vert_array[],
                                            std::vector<bool> &slaved_flag_array,
                                            size_t num_vtx, MsqError &err)
{
  err.clear();
  slaved_flag_array.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  slaved_flag_array.resize(num_vtx);
  for (size_t i=0; i<num_vtx; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < m_pmx->nnodes());
    slaved_flag_array[i] = m_vslaved[idx];
  }
}

void MxMsqAdapter::vertices_get_coordinates(const VertexHandle vert_array[],
                                            MsqVertex *coordinates,
                                            size_t num_vtx, MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<num_vtx; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < m_pmx->nnodes());
    const Vct3 & p( m_pmx->node(idx) );
    coordinates[i] = MsqVertex(p[0], p[1], p[2]);
    if (m_vfixed[idx])
      coordinates[i].set_hard_fixed_flag();
  }
}

void MxMsqAdapter::vertex_set_coordinates(VertexHandle vertex,
                                          const Vector3D &coordinates,
                                          MsqError &err)
{
  err.clear();
  assert(m_pmx);
  size_t idx = reinterpret_cast<size_t>( vertex );

  Vct3 & p( m_pmx->node(idx) );
  for (int k=0; k<3; ++k)
    p[k] = coordinates[k];
}

void MxMsqAdapter::vertices_set_byte(const VertexHandle *vert_array,
                                     const unsigned char *byte_array,
                                     size_t array_size, MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (array_size > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<array_size; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < m_vbyte.size());
    m_vbyte[idx] = byte_array[i];
  }
}

void MxMsqAdapter::vertices_get_byte(const VertexHandle *vert_array,
                                     unsigned char *byte_array,
                                     size_t array_size, MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (array_size > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<array_size; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < m_vbyte.size());
    byte_array[i] = m_vbyte[idx];
  }
}

void MxMsqAdapter::vertices_get_attached_elements(const VertexHandle *vert_array,
                                                  size_t num_vtx,
                                                  std::vector<ElementHandle> &elements,
                                                  std::vector<size_t> &offsets,
                                                  MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  elements.clear();
  offsets.clear();

  // reserve space for efficiency
  elements.reserve( num_vtx*16 );
  offsets.resize(num_vtx + 1);
  offsets[0] = 0;

  size_t pos = 0;
  const ConnectMap &v2e( m_pmx->v2eMap() );
  for (size_t i=0; i<num_vtx; ++i) {
    size_t idx = reinterpret_cast<size_t>( vert_array[i] );
    assert(idx < v2e.size());
    const size_t ne = v2e.size(idx);
    const uint *nbe = v2e.first(idx);
    for (size_t j=0; j<ne; ++j)
      elements.push_back( reinterpret_cast<ElementHandle>( size_t(nbe[j]) ) );
    pos += ne;
    offsets[i+1] = pos;
  }
}

void MxMsqAdapter::elements_get_attached_vertices(const ElementHandle *elem_handles,
                                                  size_t num_elems,
                                                  std::vector<VertexHandle> &vert_handles,
                                                  std::vector<size_t> &offsets,
                                                  MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_elems > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  vert_handles.clear();
  offsets.clear();

  vert_handles.reserve( 4*num_elems );
  offsets.resize(  num_elems + 1 );
  offsets[0] = 0;

  size_t pos = 0;
  for (size_t i=0; i<num_elems; ++i) {
    size_t idx = reinterpret_cast<size_t>( elem_handles[i] );
    uint nv, isec;
    const uint *vi = m_pmx->globalElement(idx, nv, isec);
    assert(vi != 0);
    for (uint j=0; j<nv; ++j)
      vert_handles.push_back( reinterpret_cast<VertexHandle>(size_t(vi[j])) );
    pos += nv;
    offsets[i+1] = pos;
  }
}

void MxMsqAdapter::elements_get_topologies(const ElementHandle *elem_handles,
                                           EntityTopology *elem_topos,
                                           size_t num_elems, MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_elems > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<num_elems; ++i) {
    size_t idx = reinterpret_cast<size_t>( elem_handles[i] );
    uint nv, isec;
    m_pmx->globalElement(idx, nv, isec);
    assert(isec != NotFound);
    switch ( m_pmx->section(isec).elementType() ) {
    case Mx::Tri3:
    case Mx::Tri6:
      elem_topos[i] = TRIANGLE;
      break;
    case Mx::Quad4:
    case Mx::Quad8:
    case Mx::Quad9:
      elem_topos[i] = QUADRILATERAL;
      break;
    case Mx::Tet4:
    case Mx::Tet10:
      elem_topos[i] = TETRAHEDRON;
      break;
    case Mx::Hex8:
    case Mx::Hex20:
    case Mx::Hex27:
      elem_topos[i] = HEXAHEDRON;
      break;
    case Mx::Penta6:
    case Mx::Penta15:
    case Mx::Penta18:
      elem_topos[i] = PRISM;
      break;
    case Mx::Pyra5:
    case Mx::Pyra14:
      elem_topos[i] = PYRAMID;
      break;
    default:
      elem_topos[i] = POLYHEDRON;
    }
  }
}

void MxMsqAdapter::release_entity_handles(const EntityHandle *,
                                          size_t,MsqError &err)
{
  err.clear();
}

void MxMsqAdapter::release() {}

void MxMsqAdapter::clear()
{
  assign( MxMeshPtr() );
  m_tags->clear();
}

void MxMsqAdapter::vertices_get_global_id(const VertexHandle vert_array[],
                                          size_t global_id[], size_t num_vtx,
                                          MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<num_vtx; ++i) {
    global_id[i] = reinterpret_cast<size_t>( vert_array[i] );
  }
}

void MxMsqAdapter::vertices_get_processor_id(const VertexHandle[],
                                             int proc_id[], size_t num_vtx,
                                             MsqError &err)
{
  err.clear();
  if (not m_pmx) {
    if (num_vtx > 0)
      err.set_error( MsqError::NOT_INITIALIZED );
    return;
  }

  for (size_t i=0; i<num_vtx; ++i)
    proc_id[i] = 0;
}

// tag handling directly from Mesquite::MeshImpl

const char* MESQUITE_FIELD_TAG = "MesquiteTags";

TagHandle MxMsqAdapter::tag_create( const std::string& name,
                                    TagType type,
                                    unsigned length,
                                    const void* defval,
                                    MsqError& err )
{
  TagDescription::VtkType vtype;
  std::string field;
  switch( length )
  {
  case 1:  vtype = TagDescription::SCALAR; break;
  case 3:  vtype = TagDescription::VECTOR; break;
  case 9:  vtype = TagDescription::TENSOR; break;
  default: vtype = TagDescription::FIELD;
    field = MESQUITE_FIELD_TAG;     break;
  }

  // If tag name contains a space, assume the tag name
  // is a concatenation of the VTK field and member names.
  if (vtype != TagDescription::FIELD &&
      name.find(" ") != std::string::npos)
    vtype = TagDescription::FIELD;

  size_t size = MeshImplTags::size_from_tag_type( type );
  TagDescription desc( name, type, vtype, length*size, field );
  size_t index = m_tags->create( desc, defval, err );
  MSQ_ERRZERO(err);
  return (TagHandle)index;
}

void MxMsqAdapter::tag_delete( TagHandle handle, MsqError& err )
{
  m_tags->destroy( (size_t)handle, err );
  MSQ_CHKERR(err);
}

TagHandle MxMsqAdapter::tag_get( const std::string& name, MsqError& err )
{
  size_t index = m_tags->handle( name, err );
  MSQ_ERRZERO(err);
  if (!index)
    MSQ_SETERR(err)( MsqError::TAG_NOT_FOUND, "could not find tag \"%s\"", name.c_str() );
  return (TagHandle)index;
}

void MxMsqAdapter::tag_properties( TagHandle handle,
                                   std::string& name,
                                   TagType& type,
                                   unsigned& length,
                                   MsqError& err )
{
  const TagDescription& desc = m_tags->properties( (size_t)handle, err );
  MSQ_ERRRTN(err);

  name = desc.name;
  type = desc.type;
  length = (unsigned)(desc.size / MeshImplTags::size_from_tag_type( desc.type ));
}


void MxMsqAdapter::tag_set_element_data( TagHandle handle,
                                         size_t num_elems,
                                         const ElementHandle* elem_array,
                                         const void* values,
                                         MsqError& err )
{
  m_tags->set_element_data( (size_t)handle,
                            num_elems,
                            (const size_t*)elem_array,
                            values,
                            err );
  MSQ_CHKERR(err);
}

void MxMsqAdapter::tag_get_element_data( TagHandle handle,
                                         size_t num_elems,
                                         const ElementHandle* elem_array,
                                         void* values,
                                         MsqError& err )
{
  m_tags->get_element_data( (size_t)handle,
                            num_elems,
                            (const size_t*)elem_array,
                            values,
                            err );
  MSQ_CHKERR(err);
}

void MxMsqAdapter::tag_set_vertex_data(  TagHandle handle,
                                         size_t num_elems,
                                         const VertexHandle* elem_array,
                                         const void* values,
                                         MsqError& err )
{
  m_tags->set_vertex_data( (size_t)handle,
                           num_elems,
                           (const size_t*)elem_array,
                           values,
                           err );
  MSQ_CHKERR(err);
}

void MxMsqAdapter::tag_get_vertex_data(  TagHandle handle,
                                         size_t num_elems,
                                         const VertexHandle* elem_array,
                                         void* values,
                                         MsqError& err )
{
  m_tags->get_vertex_data( (size_t)handle,
                           num_elems,
                           (const size_t*)elem_array,
                           values,
                           err );
  MSQ_CHKERR(err);
}


