
/* Copyright (C) 2016 David Eller <david@larosterna.com>
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

#include "rply.h"
#include <genua/trimesh.h>

struct rply_context
{
  TriMesh *pmesh = nullptr;
  Vct3 vtx;
  uint vix[3];
  int tag = 0;

  void storeVertex() {
    assert(pmesh);
    pmesh->addVertex(vtx);
    vtx = 0.0;
  }

  void storeFace() {
    assert(pmesh);
    assert(std::find(vix, vix+3, NotFound) == vix+3);
    pmesh->addFace(vix);
    std::fill(std::begin(vix), std::end(vix), NotFound);
  }
};

static int vertex_cb(p_ply_argument argument)
{
  rply_context *ctx = NULL;
  long cid = 0;
  int stat = ply_get_argument_user_data(argument, (void **) &ctx, &cid);
  if (stat) {
    ctx->vtx[cid] = ply_get_argument_value(argument);
    assert(cid >= 0);
    assert(cid < 3);
    if (cid >= 2)
      ctx->storeVertex();
  }
  return stat;
}

static int face_cb(p_ply_argument argument)
{
  rply_context *ctx = NULL;
  int stat = ply_get_argument_user_data(argument, (void **) &ctx, NULL);
  if (stat == 0 or ctx == NULL)
    return 0;

  long length, value_index;
  stat = ply_get_argument_property(argument, NULL, &length, &value_index);
  if (stat == 0)
    return 0;

  if (value_index >= 0 and value_index < 3) {
    ctx->vix[value_index] = (uint) ply_get_argument_value(argument);
    if (value_index == 2)
      ctx->storeFace();
  }
  return 1;
}

bool TriMesh::fromPLY(const std::string &fname)
{
  size_t nvertices, ntriangles;
  p_ply ply = ply_open(fname.c_str(), NULL, 0, NULL);
  if (!ply)
    return false;
  if (!ply_read_header(ply))
    return false;

  rply_context ctx;
  ctx.pmesh = this;

  nvertices = ply_set_read_cb(ply, "vertex", "x", vertex_cb, &ctx, 0);
  ply_set_read_cb(ply, "vertex", "y", vertex_cb, &ctx, 1);
  ply_set_read_cb(ply, "vertex", "z", vertex_cb, &ctx, 2);
  ntriangles = ply_set_read_cb(ply, "face", "vertex_indices", face_cb, &ctx, 0);

  this->clear();
  this->reserve(nvertices, ntriangles);

  if (!ply_read(ply))
    return false;
  ply_close(ply);
  return true;
}

bool TriMesh::toPLY(const std::string &fname, bool binary)
{
  p_ply ply = ply_create(fname.c_str(),
                         binary ? PLY_DEFAULT : PLY_ASCII,
                         NULL, 0, NULL);
  if (!ply)
    return false;

  // add faces
  if ( !ply_add_element(ply, "vertex", nvertices()) )
    return false;

  // add properties
  if ( !ply_add_scalar_property(ply, "x", PLY_DOUBLE) )
    return false;
  if ( !ply_add_scalar_property(ply, "y", PLY_DOUBLE) )
    return false;
  if ( !ply_add_scalar_property(ply, "z", PLY_DOUBLE) )
    return false;

  bool write_normals = false; // (vtx.size() == nrm.size());
  if (write_normals) {
    if ( !ply_add_scalar_property(ply, "nx", PLY_DOUBLE) )
      return false;
    if ( !ply_add_scalar_property(ply, "ny", PLY_DOUBLE) )
      return false;
    if ( !ply_add_scalar_property(ply, "nz", PLY_DOUBLE) )
      return false;
  }

  // add faces
  if ( !ply_add_element(ply, "face", nfaces()) )
    return false;

  if ( !ply_add_property(ply, "vertex_indices", PLY_LIST, PLY_UCHAR, PLY_UINT) )
    return false;

  // if ( !ply_add_scalar_property(ply, "tag", PLY_INT32) )
  //  return false;

  if ( !ply_write_header(ply) )
    return false;

  // write data - first all vertices, then all faces
  const size_t nv = nvertices();
  for (size_t i=0; i<nv; ++i) {
    for (int k=0; k<3; ++k)
      ply_write(ply, vtx[i][k]);
    if (write_normals) {
      for (int k=0; k<3; ++k)
        ply_write(ply, nrm[i][k]);
    }
  }

  const size_t nf = nfaces();
  for (size_t i=0; i<nf; ++i) {
    ply_write(ply, 3.0);
    const uint *v = face(i).vertices();
    for (int k=0; k<3; ++k)
      ply_write(ply, (double) v[k]);
    // ply_write(ply, (double) face(i).tag());
  }

  ply_close(ply);
  return true;
}

bool TriMesh::isPLY(const std::string &fname)
{
  p_ply ply = ply_open(fname.c_str(), NULL, 0, NULL);
  if (ply == NULL)
    return false;
  int stat = ply_read_header(ply);
  ply_close(ply);
  return (stat != 0);
}
