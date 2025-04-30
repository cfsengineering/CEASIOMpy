
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
 
#include "splitter.h"
#include <QPainter>

#ifdef Q_OS_MAC

// Not compiled unless on Mac OS X

SplitterHandle::SplitterHandle(Qt::Orientation orientation, QSplitter *parent)
  : QSplitterHandle(orientation, parent) {   }

// Paint the horizontal handle as a gradient, paint
// the vertical handle as a line.
void SplitterHandle::paintEvent(QPaintEvent *)
{
  QPainter painter(this);

  QColor topColor(145, 145, 145);
  QColor bottomColor(142, 142, 142);
  QColor gradientStart(252, 252, 252);
  QColor gradientStop(223, 223, 223);

  if (orientation() == Qt::Vertical) {
    painter.setPen(topColor);
    painter.drawLine(0, 0, width(), 0);
    painter.setPen(bottomColor);
    painter.drawLine(0, height() - 1, width(), height() - 1);

    QLinearGradient linearGrad(QPointF(0, 0), QPointF(0, height() -3));
    linearGrad.setColorAt(0, gradientStart);
    linearGrad.setColorAt(1, gradientStop);
    painter.fillRect(QRect(QPoint(0,1), size() - QSize(0, 2)), QBrush(linearGrad));
  } else {
    painter.setPen(topColor);
    painter.drawLine(0, 0, 0, height());
  }
}

QSize SplitterHandle::sizeHint() const
{
  QSize parent = QSplitterHandle::sizeHint();
  if (orientation() == Qt::Vertical) {
    return parent + QSize(0, 3);
  } else {
    return QSize(1, parent.height());
  }
}

QSplitterHandle *Splitter::createHandle()
{
  return new SplitterHandle(orientation(), this);
}

Splitter::Splitter(Qt::Orientation orientation, QWidget *parent)
    : QSplitter(orientation, parent) {}

#endif


