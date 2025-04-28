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

#include <iostream>

#include <qpoint.h>

class Case
{
public:
	Case() {};
	
	void initFrom(int binary);
	operator int() const;

	int nbTop() const { return nbTop_; }
	int nbBottom() const { return nbBottom_; }
	bool topIsBlack() const { return topIsBlack_; }
	int topAltitude() const { return altitude_ + nbBottom_ + nbTop_; }

	friend std::ostream & operator<<(std::ostream& out, const Case& c);
	friend std::istream & operator>>(std::istream& in, Case& c);

	void draw(const QPoint& pos) const;
	void drawTop(const QPoint& pos) const;
	void drawTopPiece(const QPoint& pos) const;
	void drawTopPieceTop(const QPoint& pos) const;
	void drawPieces(const QPoint& pos) const;

	void removePiece();
	void addPiece(bool under, bool black);

private:
	static void drawParallelepiped(float size, float height);
	static void drawSquare(float size);
	void drawBasis(const QPoint& pos) const;
	void drawPiece(const QPoint& pos, int altitude, bool black) const;
    void checkForRevolution();

	int altitude_;
	bool topIsBlack_;
	int nbTop_, nbBottom_;

	int value;
};
