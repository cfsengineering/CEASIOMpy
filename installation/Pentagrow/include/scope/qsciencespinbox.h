
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
 
#ifndef __QScienceSpinBox_H__
#define __QScienceSpinBox_H__

#include <QDoubleSpinBox>
#include <QDoubleValidator>
#include <QLineEdit>
#include <QVariant>
#include <QDebug>
#include <QString>

/** Spin box using scientific notation.

Code written by Mattias Pospiech and released under GPL on

http://www.matthiaspospiech.de/blog/2009/01/03/qt-spinbox-widget-with-scientific-notation/

Since I started using Qt over a year ago I have been asking and looking for a
Qt widget that can handle numbers in a scientific notation. Unfortunately Qt
Software does not offer such a solution nor is it trivial to implement. With
the hints I got in some public web forums I implementet the solution provided
here.

This widget is derived from QDoubleSpinBox. It uses a decimal value of 1000
(that is more decimal points than a double can handle) and implements a new
decimal value for the presentation in scientific notation. The Validator is
realised by setting the LineEdit to a QDoubleValidator::ScientificNotation.
However the most important part is the reimplementation of textFromValue and
valueFromText. This unfortunately requires to copy the whole validation code of
QDoubleSpinBox, which can not be borrowed and represents the major part of the
code.

If someone can show a shrinked but still functional equivalent version that
would be great. In the end I think that it would be better if such a solution
would be included into a Qt release, especially because in its current form I
use so much of their code.

  */
class QScienceSpinBox : public QDoubleSpinBox
{
  Q_OBJECT
public:
  QScienceSpinBox(QWidget * parent = 0);

	int decimals() const;
	void setDecimals(int value);

  QString textFromValue ( double value ) const;
  double valueFromText ( const QString & text ) const;

private:
	int dispDecimals;
  QChar delimiter, thousand;
	QDoubleValidator * v;


private:
	void initLocalValues(QWidget *parent);
  bool isIntermediateValue(const QString &str) const;
  QVariant validateAndInterpret(QString &input, int &pos,
                                QValidator::State &state) const;
	QValidator::State validate(QString &text, int &pos) const;
	void fixup(QString &input) const;
	QString stripped(const QString &t, int *pos) const;
	double round(double value) const;
	void stepBy(int steps);

public slots:
	void stepDown();
	void stepUp();

};

#endif
