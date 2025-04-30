/****************************************************************************

 Copyright (C) 2002-2008 Gilles Debunne. All rights reserved.

 This file is part of the QGLViewer library version 2.3.1.

 http://www.libqglviewer.com - contact@libqglviewer.com

 This file may be used under the terms of the GNU General Public License 
 versions 2.0 or 3.0 as published by the Free Software Foundation and
 appearing in the LICENSE file included in the packaging of this file.
 In addition, as a special exception, Gilles Debunne gives you certain 
 additional rights, described in the file GPL_EXCEPTION in this package.

 libQGLViewer uses dual licensing. Commercial/proprietary software must
 purchase a libQGLViewer Commercial License.

 This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

*****************************************************************************/

#ifndef DVONNDRAWER_H
#define DVONNDRAWER_H

#include "game.h"

#include <QGLViewer/vec.h>
#include <qstring.h>
#include <qgl.h>
#include <map>

class QGLViewer;

namespace dvonn
{
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Interface of Drawer
  //++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  class Drawer
  {
  public:
    Drawer();
    virtual ~Drawer();
    void init();
    void toggleTexture(bool);
    void drawPieces(const Board::ConstStackHandle&) const;
    void draw(const Board::ConstStackHandle&) const;
    void drawStatus(const Board::ConstStackHandle&,QGLViewer* v) const;
    void drawComplement(bool showLabels) const;
    void drawWhitePiecePools(const Board&,bool lastTransparent) const;
    void drawBlackPiecePools(const Board&,bool lastTransparent) const;

    void drawTransparentPiece(Color p,const Board::ConstStackHandle& c,float a=0.5f) const;
    void drawTransparentPieces(Stack::const_iterator first,Stack::const_iterator last,const Board::Coord& c,float h=0.0f,float a=0.5f) const;

    void highlight(const Board::ConstStackHandle&) const;
    void highlightPieces(const Board::ConstStackHandle&) const;

    void drawMove(const Board& b,const Game::Move m,float t) const;
    float estimateDrawMoveLength(const Board& b,const Game::Move m) const;

    qglviewer::Vec boardCenter() const;
    qglviewer::Vec boardUpVector() const;
    float boardRadius() const;
    qglviewer::Vec defaultEyePosition() const;
  private:
    void startTexture(const QString& t) const;
    void startTexture(const QString& t,GLuint) const;
    void startTexture() const;
    void endTexture() const;

    std::map<QString,GLuint> textures_;
    std::vector<GLuint>      hLabels_;
    std::vector<GLuint>      vLabels_;
    bool                     showTextures_;
  };
}
#endif // DVONNDRAWER_H
