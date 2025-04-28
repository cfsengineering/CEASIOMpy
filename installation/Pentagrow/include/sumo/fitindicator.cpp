
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
 
#include "fitindicator.h"
#include "wingskeleton.h"
#include "wingsection.h"
#include "assembly.h"
#include "glew.h"
#include <genua/transformation.h>

FitIndicator::~FitIndicator() {}

void FitIndicator::markWingSection(uint iwing, uint isection,
                                   Real rChord, Real rThick)
{
  if (not pasy)
    return;

  if (iwing == NotFound) {
    for (uint i=0; i<pasy->nwings(); ++i)
      markWingSection(i, NotFound, rChord, rThick);
    return;
  }

  WingSkeletonPtr wng = pasy->wing(iwing);
  if (not wng)
    return;

  // transformation for the wing itself
  Trafo3d wingTrafo;
  wingTrafo.rotate( wng->rotation() );
  wingTrafo.translate( wng->origin() );

  Mtx44 wingTfm;
  wingTrafo.matrix(wingTfm);

  if ( isection < wng->nsections() ) {

    WingSectionPtr sec = wng->section(isection);
    Vct3 po, pu, pv, pn;
    sec->captureRectangle( wingTfm, rChord, rThick, po, pu, pv, pn );
    rects.push_back( Vct3f( po - pu - pv ) );
    rects.push_back( Vct3f( po + pu - pv ) );
    rects.push_back( Vct3f( po + pu + pv ) );
    rects.push_back( Vct3f( po - pu + pv ) );

  } else {

    for (uint i=0; i<wng->nsections(); ++i) {
      WingSectionPtr sec = wng->section(i);
      Vct3 po, pu, pv, pn;
      sec->captureRectangle( wingTfm, rChord, rThick, po, pu, pv, pn );
      rects.push_back( Vct3f( po - pu - pv ) );
      rects.push_back( Vct3f( po + pu - pv ) );
      rects.push_back( Vct3f( po + pu + pv ) );
      rects.push_back( Vct3f( po - pu + pv ) );
    }

  }
}

void FitIndicator::clear()
{
  rects.clear();
}

void FitIndicator::draw() const
{
  if (rects.empty())
    return;

  glPolygonMode( GL_FRONT_AND_BACK, GL_FILL );
  glColor4ubv( clr.pointer() ) ;
  drawQuads();
  glPolygonMode( GL_FRONT_AND_BACK, GL_LINE );
  glColor3f( 0.0f, 0.0f, 0.0f );
  drawQuads();
  glPolygonMode( GL_FRONT_AND_BACK, GL_FILL );
}

void FitIndicator::drawQuads() const
{
  // these are so few polygons that it is probably
  // ok to draw in immediate mode
  const int nq = rects.size() / 4;
  glBegin(GL_QUADS);
  for (int i=0; i<nq; ++i) {
    const Vct3f & p1( rects[4*i+0] );
    const Vct3f & p2( rects[4*i+1] );
    const Vct3f & p3( rects[4*i+2] );
    const Vct3f & p4( rects[4*i+3] );
    Vct3f fn = cross(p3-p1, p4-p2).normalized();
    glNormal3fv( fn.pointer() );
    glVertex3fv( p1.pointer() );
    glVertex3fv( p2.pointer() );
    glVertex3fv( p3.pointer() );
    glVertex3fv( p4.pointer() );
  }
  glEnd();
}

