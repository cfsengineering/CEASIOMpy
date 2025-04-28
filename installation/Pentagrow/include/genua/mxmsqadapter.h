
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
 
#ifndef MXMSQADAPTER_H
#define MXMSQADAPTER_H

#include "forward.h"
#include <MeshInterface.hpp>
#include <MeshImplTags.hpp>
#include <ParallelMeshInterface.hpp>
#include <ArrayMesh.hpp>

using namespace Mesquite;

/** Mesquite interface adapter for a single section.
 *
 *
 * \sa MxMsqAdapter
 */
class MxMsqSectionAdapter : public ArrayMesh
{
public:

  /// create a Mesquite::ArrayMesh from a single mesh section
  MxMsqSectionAdapter(MxMeshPtr pmx, uint isec);

  /// assign a mesh section
  void assign(MxMeshPtr pmx, uint isec);

private:

  /// kept to keep reference count up
  MxMeshPtr m_pmx;

  /// stores a flag which indicates whether a vertex is fixed
  std::vector<int> m_fixed;
};

/** Mesquite adapter for the entire mesh.
 *
 *
 */
class MxMsqAdapter : public Mesh
{
public:

  /// create adaptor for pmx
  MxMsqAdapter(MxMeshPtr pmx = MxMeshPtr());

  /// delete adapter
  virtual ~MxMsqAdapter();

  /// assign a new mesh to adapt
  void assign(MxMeshPtr pmx);

  /// mark all surface vertices as fixed (default)
  void fix_surface_vertices();

  /// always 3D
  int get_geometric_dimension(MsqError &err) {err.clear(); return 3;}

  /// contiguous list of vertex handles
  void get_all_vertices(std::vector<VertexHandle> &vertices, MsqError &err);

  /// contiguous list of element handles
  void get_all_elements(std::vector<ElementHandle> &elements, MsqError &err);

  /// test whether referenced vertices are flagged as fixed
  void vertices_get_fixed_flag(const VertexHandle vert_array[],
                               std::vector<bool> &fixed_flag_array,
                               size_t num_vtx, MsqError &err);

  /// test whether referenced vertices are flagged as slaved
  void vertices_get_slaved_flag(const VertexHandle vert_array[],
                                std::vector<bool> &slaved_flag_array,
                                size_t num_vtx, MsqError &err);

  /// access vertex coordinates
  void vertices_get_coordinates(const VertexHandle vert_array[],
                                MsqVertex *coordinates,
                                size_t num_vtx, MsqError &err);

  /// access vertex coordinates
  void vertex_set_coordinates(VertexHandle vertex, const Vector3D &coordinates,
                              MsqError &err);

  /// set vertex byte
  void vertex_set_byte(VertexHandle vertex, unsigned char byte, MsqError &err) {
    err.clear();
    size_t idx = reinterpret_cast<size_t>( vertex );
    assert(idx < m_vbyte.size());
    m_vbyte[idx] = byte;
  }

  /// set vertex bytes
  void vertices_set_byte(const VertexHandle *vert_array,
                         const unsigned char *byte_array,
                         size_t array_size, MsqError &err);

  /// access vertex byte
  void vertex_get_byte(const VertexHandle vertex, unsigned char *byte,
                       MsqError &err) {
    err.clear();
    size_t idx = reinterpret_cast<size_t>( vertex );
    assert(idx < m_vbyte.size());
    *byte = m_vbyte[idx];
  }

  /// access vertex bytes
  void vertices_get_byte(const VertexHandle *vertex, unsigned char *byte_array,
                         size_t array_size, MsqError &err);

  /// retrieve elements attached to given vertex
  void vertices_get_attached_elements(const VertexHandle *vert_array,
                                      size_t num_vtx,
                                      std::vector<ElementHandle> &elements,
                                      std::vector<size_t> &offsets,
                                      MsqError &err);

  /// retrieve vertices attached to element
  void elements_get_attached_vertices(const ElementHandle *elem_handles,
                                      size_t num_elems,
                                      std::vector<VertexHandle> &vert_handles,
                                      std::vector<size_t> &offsets,
                                      MsqError &err);

  /// identify element types
  void elements_get_topologies(const ElementHandle *elem_handles,
                               EntityTopology *elem_topos,
                               size_t num_elems, MsqError &err);

  /// dummy memory management
  void release_entity_handles(const EntityHandle *handle_array,
                              size_t num_handles, MsqError &err);

  /// dummy memory management
  void release();

  /// clear mesh and tags
  void clear();

  // parallel mesh interface

  void vertices_get_global_id(const VertexHandle vert_array[],
                              size_t global_id[], size_t num_vtx,
                              MsqError &err);

  void vertices_get_processor_id(const VertexHandle vert_array[],
                                 int proc_id[], size_t num_vtx,
                                 MsqError &err);

  void set_parallel_helper(ParallelHelper *helper) {
    m_helper = helper;
  }

  ParallelHelper *get_parallel_helper() {
    return m_helper;
  }

  // tag handling uses implementation from mesquite

  TagHandle tag_create(const std::string& tag_name,
                       TagType type, unsigned length,
                       const void* default_value,
                       MsqError &err);

  void tag_delete(TagHandle handle, MsqError& err);

  TagHandle tag_get(const std::string& name, MsqError& err);

  void tag_properties(TagHandle handle, std::string& name_out,
                      TagType& type_out, unsigned& length_out,
                      MsqError& err);

  void tag_set_element_data(TagHandle handle, size_t num_elems,
                            const ElementHandle* elem_array,
                            const void* tag_data, MsqError& err);

  void tag_set_vertex_data(TagHandle handle, size_t num_elems,
                           const VertexHandle* node_array,
                           const void* tag_data, MsqError& err);

  void tag_get_element_data(TagHandle handle, size_t num_elems,
                            const ElementHandle* elem_array,
                            void* tag_data, MsqError& err);

  void tag_get_vertex_data(TagHandle handle, size_t num_elems,
                           const VertexHandle* node_array,
                           void* tag_data,MsqError& err);

protected:

  /// smart pointer to MxMesh object to adapt
  MxMeshPtr m_pmx;

  /// vertex flag bytes used by mesquite
  std::vector<unsigned char> m_vbyte;

  /// array indicating which whether a vertex is fixed
  std::vector<bool> m_vfixed;

  /// array indicating which whether a vertex is slaved
  std::vector<bool> m_vslaved;

  /// tag handling from mesquite MeshImpl
  MeshImplTags *m_tags;

  /// for parallel mesh interface
  ParallelHelper *m_helper;
};

#endif // MXMSQADAPTER_H
