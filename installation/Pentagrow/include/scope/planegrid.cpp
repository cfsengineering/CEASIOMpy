//
// project:      scope
// file:         planegrid.cpp
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Draw reference grid overlay

#include <iostream>

#include "planegrid.h"
#include "glew.h"

using namespace std;

void PlaneGrid::create(const Vct3f & pn, float offs,
                       const Vct3f & clo, const Vct3f & chi)
{
  fOffset = offs;
  vNormal = pn;

  // project corner points onto plane
  Vct3f plo = clo - (dot(clo,pn) - offs)*pn;
  Vct3f phi = chi - (dot(chi,pn) - offs)*pn;

  // determine axes
  Vct3f Su, Sv;
  float anx = fabs(pn[0]);
  float any = fabs(pn[1]);
  float anz = fabs(pn[2]);
  if (anx > any and anx > anz)
    Su[1] = Sv[2] = 1.0;
  else if (any > anx and any > anz)
    Su[0] = Sv[2] = 1.0;
  else
    Su[0] = Sv[1] = 1.0;

  // grid lengths
  float Lu = fabs(dot(Su, phi-plo));
  float Lv = fabs(dot(Sv, phi-plo));

  if (Lu == 0)
    Lu = 1.0f;
  if (Lv == 0)
    Lv = 1.0f;

  // slice the shorter length into 20 tiles
  float l = std::min(Lu,Lv) / 20.0f;
  int nvu = int( 1.25*Lu/l ) + 1;
  int nvv = int( 1.25*Lv/l ) + 1;

  // use uneven number of vertices
  nvu += (nvu & 1) ? 0 : 1;
  nvv += (nvv & 1) ? 0 : 1;

  // create grid vertices
  Vct3f ctr = 0.5f*plo + 0.5f*phi;
  nstrip = nvv - 1;
  vtx.resize(nvu*nvv);
  for (int j=0; j<nvv; ++j) {
    float dj = l*(j - nvv/2);
    for (int i=0; i<nvu; ++i) {
      float di = l*(i - nvu/2);
      vtx[j*nvu+i] = ctr + di*Su + dj*Sv;
    }
  }
}

void PlaneGrid::rescale(const Vct3f & clo, const Vct3f & chi)
{
  if (norm(vNormal) > 0.0)
    create(vNormal, fOffset, clo, chi);
}

void PlaneGrid::glDraw() const
{
  if (not bVisible)
    return;

  // number of quads per strip
  const int nquad = vtx.size() / (nstrip +1) - 1;
  const int nv = nquad + 1;

  glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
  for (uint j=0; j<nstrip; ++j) {
    const int iLeft = j*nv;
    const int iRight = (j+1)*nv;
    glBegin(GL_QUAD_STRIP);
    glColor3f(0.7f, 0.7f, 0.7f);
    glNormal3fv(vNormal.pointer());
    for (int i=1; i<nquad; ++i) {
      glVertex3fv( vtx[iLeft+i].pointer() );
      glVertex3fv( vtx[iRight+i].pointer() );
    }
    glEnd();
  }
  glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
}
