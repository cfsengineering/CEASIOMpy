
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
 
#ifndef SPLITTER_H
#define SPLITTER_H

#include <QSplitter>

#ifdef Q_OS_MAC

// This is a very simple adapter for the QSplitter class. It makes the
// splitter and its handle look like expected for main window splitters
// of Mac OS X applications. The class Splitter is just typedefed to
// QSplitter everywhere else.

#include <QSplitterHandle>

class SplitterHandle : public QSplitterHandle
{
  Q_OBJECT
public:
  SplitterHandle(Qt::Orientation orientation, QSplitter *parent);
  void paintEvent(QPaintEvent *);
  QSize sizeHint() const;
};

class Splitter : public QSplitter
{
  Q_OBJECT
public:
  Splitter(Qt::Orientation orientation, QWidget *parent);

  virtual ~Splitter() {}
  QSplitterHandle *createHandle();
};

#else

#undef Splitter
#define Splitter QSplitter

#endif


#endif // SPLITTER_H
