/***************************************************************************
**                                                                        **
**  QCustomPlot, a simple to use, modern plotting widget for Qt           **
**  Copyright (C) 2012 Emanuel Eichhammer                                 **
**                                                                        **
**  This program is free software: you can redistribute it and/or modify  **
**  it under the terms of the GNU General Public License as published by  **
**  the Free Software Foundation, either version 3 of the License, or     **
**  (at your option) any later version.                                   **
**                                                                        **
**  This program is distributed in the hope that it will be useful,       **
**  but WITHOUT ANY WARRANTY; without even the implied warranty of        **
**  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         **
**  GNU General Public License for more details.                          **
**                                                                        **
**  You should have received a copy of the GNU General Public License     **
**  along with this program.  If not, see http://www.gnu.org/licenses/.   **
**                                                                        **
****************************************************************************
**           Author: Emanuel Eichhammer                                   **
**  Website/Contact: http://www.WorksLikeClockwork.com/                   **
**             Date: 31.03.12                                             **
****************************************************************************/

/*! \file */

#ifndef QCUSTOMPLOT_H
#define QCUSTOMPLOT_H

#include <QObject>
#include <QWidget>
#include <QPainter>
#include <QPaintEvent>
#include <QPixmap>
#include <QVector>
#include <QString>
#include <QPrinter>
#include <QDateTime>
#include <QMultiMap>
#include <QFlags>
#include <QDebug>
#include <QVector2D>

// define FUNCNAME macro to mean the function name for debug output on different compilers:
#if defined(Q_CC_GNU)
#  define FUNCNAME __PRETTY_FUNCTION__
#elif defined(Q_CC_MSVC)
#  define FUNCNAME __FUNCSIG__
#else
#  define FUNCNAME __func__
#endif
// fix MSVC lack of pi:
#ifndef M_PI
#  define M_PI 3.14159265358979323846
#endif

class QCustomPlot;
class QCPLegend;
class QCPRange;
class QCPAxis;
class QCPData;

class QCPData
{
public:
  QCPData();
  double key, value;
  double keyErrorPlus, keyErrorMinus;
  double valueErrorPlus, valueErrorMinus;
};

/*! \typedef QCPDataMap
  Container for storing QCPData items in a sorted fashion. The key of the map
  is the key member of the QCPData instance.
  \see QCPData, QCPGraph::setData
*/
typedef QMap<double, QCPData> QCPDataMap;
typedef QMapIterator<double, QCPData> QCPDataMapIterator;
typedef QMutableMapIterator<double, QCPData> QCPDataMutableMapIterator;

class QCPCurveData
{
public:
  QCPCurveData();
  double t, key, value;
};

/*! \typedef QCPCurveDataMap
  Container for storing QCPCurveData items in a sorted fashion. The key of the map
  is the t member of the QCPCurveData instance.
  \see QCPCurveData, QCPCurve::setData
*/

typedef QMap<double, QCPCurveData> QCPCurveDataMap;
typedef QMapIterator<double, QCPCurveData> QCPCurveDataMapIterator;
typedef QMutableMapIterator<double, QCPCurveData> QCPCurveDataMutableMapIterator;

class QCPBarData
{
public:
  QCPBarData();
  double key, value;
};

/*! \typedef QCPBarDataMap
  Container for storing QCPBarData items in a sorted fashion. The key of the map
  is the key member of the QCPBarData instance.
  \see QCPBarData, QCPBars::setData
*/
typedef QMap<double, QCPBarData> QCPBarDataMap;
typedef QMapIterator<double, QCPBarData> QCPBarDataMapIterator;
typedef QMutableMapIterator<double, QCPBarData> QCPBarDataMutableMapIterator;

class QCPAbstractPlottable : public QObject
{
  Q_OBJECT
public:
  QCPAbstractPlottable(QCPAxis *keyAxis, QCPAxis *valueAxis);
  virtual ~QCPAbstractPlottable() {}
  
  // getters:
  QCustomPlot *parentPlot() const { return mParentPlot; }
  QString name() const { return mName; }
  bool visible() const { return mVisible; }
  QPen pen() const { return mPen; }
  QPen selectedPen() const { return mSelectedPen; }
  QBrush brush() const { return mBrush; }
  QBrush selectedBrush() const { return mSelectedBrush; }
  QCPAxis *keyAxis() const { return mKeyAxis; }
  QCPAxis *valueAxis() const { return mValueAxis; }
  bool selectable() const { return mSelectable; }
  bool selected() const { return mSelected; }
  
  // setters:
  void setName(const QString &name);
  void setVisible(bool visible);
  void setPen(const QPen &pen);
  void setSelectedPen(const QPen &pen);
  void setBrush(const QBrush &brush);
  void setSelectedBrush(const QBrush &brush);
  void setKeyAxis(QCPAxis *axis);
  void setValueAxis(QCPAxis *axis);
  void setSelectable(bool selectable);
  void setSelected(bool selected);

  // non-property methods:
  void rescaleAxes(bool onlyEnlarge=false) const;
  void rescaleKeyAxis(bool onlyEnlarge=false) const;
  void rescaleValueAxis(bool onlyEnlarge=false) const;
  virtual void clearData() = 0;
  virtual double selectTest(double key, double value) const = 0;
  virtual bool addToLegend();
  virtual bool removeFromLegend() const;
  
signals:
  void selectionChanged(bool selected);
  
protected:
  /*!
    Represents negative and positive sign domain for passing to \ref getKeyRange and \ref getValueRange.
  */
  enum SignDomain { sdNegative  ///< The negative sign domain, i.e. numbers smaller than zero
                   ,sdBoth      ///< Both sign domains, including zero, i.e. all (rational) numbers
                   ,sdPositive  ///< The positive sign domain, i.e. numbers greater than zero
                  };
  QCustomPlot *mParentPlot;
  QString mName;
  bool mVisible;
  QPen mPen, mSelectedPen;
  QBrush mBrush, mSelectedBrush;
  QCPAxis *mKeyAxis, *mValueAxis;
  bool mSelected, mSelectable;
  
  virtual void draw(QPainter *painter) const = 0;
  virtual void drawLegendIcon(QPainter *painter, const QRect &rect) const = 0;
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const = 0;
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const = 0;
  void coordsToPixels(double key, double value, double &x, double &y) const;
  const QPointF coordsToPixels(double key, double value) const;
  void pixelsToCoords(double x, double y, double &key, double &value) const;
  void pixelsToCoords(const QPointF &pixelPos, double &key, double &value) const;
  QPen mainPen() const;
  QBrush mainBrush() const;
  
  friend class QCustomPlot;
  friend class QCPPlottableLegendItem;
};

class QCPGraph : public QCPAbstractPlottable
{
  Q_OBJECT
public:
  /*!
    Defines how the graph's line is represented visually in the plot. The line is drawn with the
    current pen of the graph (\ref setPen).
    \see setLineStyle
  */
  enum LineStyle { lsNone        ///< data points are not connected with any lines (e.g. data only represented
                                 ///< with symbols according to the scatter style, see \ref setScatterStyle)
                  ,lsLine        ///< data points are connected by a straight line
                  ,lsStepLeft    ///< line is drawn as steps where the step height is the value of the left data point
                  ,lsStepRight   ///< line is drawn as steps where the step height is the value of the right data point
                  ,lsStepCenter  ///< line is drawn as steps where the step is in between two data points
                  ,lsImpulse     ///< data points are represented by a straight line parallel to the value axis, which ranges down/up to the key axis
                 };
  Q_ENUMS(LineStyle)
  /*!
    This defines the visual appearance of the points, which are all drawn with the pen of the graph
    (\ref setPen). The sizes of these visualizations (with exception of \ref ssDot and \ref ssPixmap) can be
    set with \ref setScatterSize.
    \see setScatterStyle
  */
  enum ScatterStyle { ssNone      ///< no scatter symbols are drawn (e.g. data only represented with lines, see \ref setLineStyle)
                     ,ssDot       ///< a single pixel, \ref setScatterSize has no influence on its size.
                     ,ssCross     ///< a cross (x)
                     ,ssPlus      ///< a plus (+)
                     ,ssCircle    ///< a circle which is not filled
                     ,ssDisc      ///< a circle which is filled with the color of the graph's pen (not the brush!)
                     ,ssSquare    ///< a square which is not filled
                     ,ssStar      ///< a star with eight arms, i.e. a combination of cross and plus
                     ,ssTriangle  ///< an equilateral triangle which is not filled, standing on baseline
                     ,ssTriangleInverted ///< an equilateral triangle which is not filled, standing on corner
                     ,ssCrossSquare      ///< a square which is not filled, with a cross inside
                     ,ssPlusSquare       ///< a square which is not filled, with a plus inside
                     ,ssCrossCircle      ///< a circle which is not filled, with a cross inside
                     ,ssPlusCircle       ///< a circle which is not filled, with a plus inside
                     ,ssPeace     ///< a circle which is not filled, with one vertical and two downward diagonal lines
                     ,ssPixmap    ///< a custom pixmap specified by setScatterPixmap, centered on the data point coordinates. \ref setScatterSize has no influence on its size.
                    };
  Q_ENUMS(ScatterStyle)
  /*!
    Defines what kind of error bars are drawn for each data point
  */
  enum ErrorType { etNone   ///< No error bars are shown
                  ,etKey    ///< Error bars for the key dimension of the data point are shown
                  ,etValue  ///< Error bars for the value dimension of the data point are shown
                  ,etBoth   ///< Error bars for both key and value dimensions of the data point are shown
                 };
  Q_ENUMS(ErrorType)
  
  explicit QCPGraph(QCPAxis *keyAxis, QCPAxis *valueAxis);
  virtual ~QCPGraph();
  
  // getters:
  const QCPDataMap *data() const { return mData; }
  LineStyle lineStyle() const { return mLineStyle; }
  ScatterStyle scatterStyle() const { return mScatterStyle; }
  double scatterSize() const { return mScatterSize; }
  const QPixmap scatterPixmap() const { return mScatterPixmap; }
  ErrorType errorType() const { return mErrorType; }
  QPen errorPen() const { return mErrorPen; }
  double errorBarSize() const { return mErrorBarSize; }
  bool errorBarSkipSymbol() const { return mErrorBarSkipSymbol; }
  QCPGraph *channelFillGraph() const { return mChannelFillGraph; }
  
  // setters:
  void setData(QCPDataMap *data, bool copy=false);
  void setData(const QVector<double> &key, const QVector<double> &value);
  void setDataKeyError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &keyError);
  void setDataKeyError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &keyErrorMinus, const QVector<double> &keyErrorPlus);
  void setDataValueError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &valueError);
  void setDataValueError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &valueErrorMinus, const QVector<double> &valueErrorPlus);
  void setDataBothError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &keyError, const QVector<double> &valueError);
  void setDataBothError(const QVector<double> &key, const QVector<double> &value, const QVector<double> &keyErrorMinus, const QVector<double> &keyErrorPlus, const QVector<double> &valueErrorMinus, const QVector<double> &valueErrorPlus);
  void setLineStyle(LineStyle ls);
  void setScatterStyle(ScatterStyle ss);
  void setScatterSize(double size);
  void setScatterPixmap(const QPixmap &pixmap);
  void setErrorType(ErrorType errorType);
  void setErrorPen(const QPen &pen);
  void setErrorBarSize(double size);
  void setErrorBarSkipSymbol(bool enabled);
  void setChannelFillGraph(QCPGraph *targetGraph);
  
  // non-property methods:
  void addData(const QCPDataMap &dataMap);
  void addData(const QCPData &data);
  void addData(double key, double value);
  void addData(const QVector<double> &keys, const QVector<double> &values);
  void removeDataBefore(double key);
  void removeDataAfter(double key);
  void removeData(double fromKey, double toKey);
  void removeData(double key);
  virtual void clearData();
  virtual double selectTest(double key, double value) const;
  using QCPAbstractPlottable::rescaleAxes;
  using QCPAbstractPlottable::rescaleKeyAxis;
  using QCPAbstractPlottable::rescaleValueAxis;
  virtual void rescaleAxes(bool onlyEnlarge, bool includeErrorBars) const; // overloads base class interface
  virtual void rescaleKeyAxis(bool onlyEnlarge, bool includeErrorBars) const; // overloads base class interface
  virtual void rescaleValueAxis(bool onlyEnlarge, bool includeErrorBars) const; // overloads base class interface
  
protected:
  QCPDataMap *mData;
  QPen mErrorPen;
  LineStyle mLineStyle;
  ScatterStyle mScatterStyle;
  double mScatterSize;
  QPixmap mScatterPixmap;
  ErrorType mErrorType;
  double mErrorBarSize;
  bool mErrorBarSkipSymbol;
  QCPGraph *mChannelFillGraph;

  virtual void draw(QPainter *painter) const;
  virtual void drawLegendIcon(QPainter *painter, const QRect &rect) const;

  // functions to generate plot data points in pixel coordinates:
  void getPlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  // plot style specific functions to generate plot data, used by getPlotData:
  void getScatterPlotData(QVector<QCPData> *pointData) const;
  void getLinePlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  void getStepLeftPlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  void getStepRightPlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  void getStepCenterPlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  void getImpulsePlotData(QVector<QPointF> *lineData, QVector<QCPData> *pointData) const;
  
  // helper functions for drawing:
  void drawFill(QPainter *painter, QVector<QPointF> *lineData) const;
  void drawScatterPlot(QPainter *painter, QVector<QCPData> *pointData) const;
  void drawLinePlot(QPainter *painter, QVector<QPointF> *lineData) const;
  void drawImpulsePlot(QPainter *painter, QVector<QPointF> *lineData) const;
  void drawScatter(QPainter *painter, double x, double y, ScatterStyle style) const;
  void drawError(QPainter *painter, double x, double y, const QCPData &data) const;
  
  // helper functions:
  void getVisibleDataBounds(QCPDataMap::const_iterator &lower, QCPDataMap::const_iterator &upper, int &count) const;
  void addFillBasePoints(QVector<QPointF> *lineData) const;
  void removeFillBasePoints(QVector<QPointF> *lineData) const;
  QPointF lowerFillBasePoint(double lowerKey) const;
  QPointF upperFillBasePoint(double upperKey) const;
  const QPolygonF getChannelFillPolygon(const QVector<QPointF> *lineData) const;
  int findIndexBelowX(const QVector<QPointF> *data, double x) const;
  int findIndexAboveX(const QVector<QPointF> *data, double x) const;
  int findIndexBelowY(const QVector<QPointF> *data, double y) const;
  int findIndexAboveY(const QVector<QPointF> *data, double y) const;
  double pointDistance(const QPointF &pixelPoint) const;
  double distSqrToLine(QPointF ptA, QPointF ptB, QPointF point) const;
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain, bool includeErrors) const; // overloads base class interface
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain, bool includeErrors) const; // overloads base class interface
  
  friend class QCustomPlot;
  friend class QCPLegend;
};

class QCPCurve : public QCPAbstractPlottable
{
  Q_OBJECT
public:
  explicit QCPCurve(QCPAxis *keyAxis, QCPAxis *valueAxis);
  virtual ~QCPCurve();
  
  // getters:
  const QCPCurveDataMap *data() const { return mData; }
  
  // setters:
  void setData(QCPCurveDataMap *data, bool copy=false);
  void setData(const QVector<double> &t, const QVector<double> &key, const QVector<double> &value);
  void setData(const QVector<double> &key, const QVector<double> &value);
  
  // non-property methods:
  void addData(const QCPCurveDataMap &dataMap);
  void addData(const QCPCurveData &data);
  void addData(double t, double key, double value);
  void addData(double key, double value);
  void addData(const QVector<double> &ts, const QVector<double> &keys, const QVector<double> &values);
  void removeDataBefore(double t);
  void removeDataAfter(double t);
  void removeData(double fromt, double tot);
  void removeData(double t);
  virtual void clearData();
  virtual double selectTest(double key, double value) const;
  
protected:
  QCPCurveDataMap *mData;
  
  virtual void draw(QPainter *painter) const;
  virtual void drawLegendIcon(QPainter *painter, const QRect &rect) const;
  
  void getCurveData(QVector<QPointF> *lineData) const;
  double pointDistance(const QPointF &pixelPoint) const;
  double distSqrToLine(QPointF ptA, QPointF ptB, QPointF point) const;

  QPointF outsideCoordsToPixels(double key, double value, int region) const;
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  
  friend class QCustomPlot;
  friend class QCPLegend;
};

class QCPBars : public QCPAbstractPlottable
{
  Q_OBJECT
public:
  explicit QCPBars(QCPAxis *keyAxis, QCPAxis *valueAxis);
  virtual ~QCPBars();
  
  // getters:
  double width() const { return mWidth; }
  QCPBars *barBelow() const { return mBarBelow; }
  QCPBars *barAbove() const { return mBarAbove; }
  const QCPBarDataMap *data() const { return mData; }
  
  // setters:
  void setWidth(double width);
  void setData(QCPBarDataMap *data, bool copy=false);
  void setData(const QVector<double> &key, const QVector<double> &value);
  
  // non-property methods:
  void moveBelow(QCPBars *bars);
  void moveAbove(QCPBars *bars);
  void addData(const QCPBarDataMap &dataMap);
  void addData(const QCPBarData &data);
  void addData(double key, double value);
  void addData(const QVector<double> &keys, const QVector<double> &values);
  void removeDataBefore(double key);
  void removeDataAfter(double key);
  void removeData(double fromKey, double toKey);
  void removeData(double key);
  virtual void clearData();
  virtual double selectTest(double key, double value) const;
  
protected:
  QCPBarDataMap *mData;
  double mWidth;
  QCPBars *mBarBelow, *mBarAbove;
  
  virtual void draw(QPainter *painter) const;
  virtual void drawLegendIcon(QPainter *painter, const QRect &rect) const;
  
  QPolygonF getBarPolygon(double key, double value) const;
  double getBaseValue(double key, bool positive) const;
  static void connectBars(QCPBars* lower, QCPBars* upper);
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  
  friend class QCustomPlot;
  friend class QCPLegend;
};

class QCPStatisticalBox : public QCPAbstractPlottable
{
  Q_OBJECT
public:
  explicit QCPStatisticalBox(QCPAxis *keyAxis, QCPAxis *valueAxis);
  virtual ~QCPStatisticalBox();
  
  // getters:
  double key() const { return mKey; }
  double minimum() const { return mMinimum; }
  double lowerQuartile() const { return mLowerQuartile; }
  double median() const { return mMedian; }
  double upperQuartile() const { return mUpperQuartile; }
  double maximum() const { return mMaximum; }
  QVector<double> outliers() const { return mOutliers; }
  double width() const { return mWidth; }
  double whiskerWidth() const { return mWhiskerWidth; }
  QPen whiskerPen() const { return mWhiskerPen; }
  QPen whiskerBarPen() const { return mWhiskerBarPen; }
  QPen medianPen() const { return mMedianPen; }
  double outlierSize() const { return mOutlierSize; }
  QPen outlierPen() const { return mOutlierPen; }
  QBrush outlierBrush() const { return mOutlierBrush; }

  // setters:
  void setKey(double key);
  void setMinimum(double value);
  void setLowerQuartile(double value);
  void setMedian(double value);
  void setUpperQuartile(double value);
  void setMaximum(double value);
  void setOutliers(const QVector<double> &values);
  void setData(double key, double minimum, double lowerQuartile, double median, double upperQuartile, double maximum);
  void setWidth(double width);
  void setWhiskerWidth(double width);
  void setWhiskerPen(const QPen &pen);
  void setWhiskerBarPen(const QPen &pen);
  void setMedianPen(const QPen &pen);
  void setOutlierSize(double pixels);
  void setOutlierPen(const QPen &pen);
  void setOutlierBrush(const QBrush &brush);
  
  // non-property methods:
  virtual void clearData();
  virtual double selectTest(double key, double value) const;
  
protected:
  QVector<double> mOutliers;
  double mKey, mMinimum, mLowerQuartile, mMedian, mUpperQuartile, mMaximum;
  double mWidth;
  double mWhiskerWidth;
  double mOutlierSize;
  QPen mWhiskerPen, mWhiskerBarPen, mOutlierPen, mMedianPen;
  QBrush mOutlierBrush;
  
  virtual void draw(QPainter *painter) const;
  virtual void drawLegendIcon(QPainter *painter, const QRect &rect) const;
  
  virtual void drawQuartileBox(QPainter *painter) const;
  virtual void drawMedian(QPainter *painter) const;
  virtual void drawWhiskers(QPainter *painter) const;
  virtual void drawOutliers(QPainter *painter) const;
  virtual QCPRange getKeyRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  virtual QCPRange getValueRange(bool &validRange, SignDomain inSignDomain=sdBoth) const;
  
  friend class QCustomPlot;
  friend class QCPLegend;
};

class QCPRange
{
public:
  double lower, upper;
  QCPRange();
  QCPRange(double lower, double upper);
  double size() const;
  double center() const;
  void normalize();
  QCPRange sanitizedForLogScale() const;
  QCPRange sanitizedForLinScale() const;
  bool contains(double value) const;
  
  static bool validRange(double lower, double upper);
  static bool validRange(const QCPRange &range);
  static const double minRange; //1e-280;
  static const double maxRange; //1e280;
};

class QCPAbstractLegendItem : public QObject
{
  Q_OBJECT
public:
  QCPAbstractLegendItem(QCPLegend *parent);
  virtual ~QCPAbstractLegendItem() {}
  // getters:
  QFont font() const { return mFont; }
  QColor textColor() const { return mTextColor; }
  QFont selectedFont() const { return mSelectedFont; }
  QColor selectedTextColor() const { return mSelectedTextColor; }
  bool selectable() const { return mSelectable; }
  bool selected() const { return mSelected; }
  
  // setters:
  void setFont(const QFont &font);
  void setTextColor(const QColor &color);
  void setSelectedFont(const QFont &font);
  void setSelectedTextColor(const QColor &color);
  void setSelectable(bool selectable);
  void setSelected(bool selected);
  
signals:
  void selectionChanged(bool selected);
  
protected:
  QCPLegend *mParentLegend;
  QFont mFont;
  QColor mTextColor;
  QFont mSelectedFont;
  QColor mSelectedTextColor;
  bool mSelectable, mSelected;
  
  virtual void draw(QPainter *painter, const QRect &rect) const = 0;
  virtual QSize size(const QSize &targetSize) const = 0;
  
  friend class QCPLegend;
};

class QCPPlottableLegendItem : public QCPAbstractLegendItem
{
  Q_OBJECT
public:
  QCPPlottableLegendItem(QCPLegend *parent, QCPAbstractPlottable *plottable);
  virtual ~QCPPlottableLegendItem() {}
  QCPAbstractPlottable *plottable() { return mPlottable; }
  void setTextWrap(bool wrap);
  bool textWrap() const { return mTextWrap; }
  
protected:
  QCPAbstractPlottable *mPlottable;
  bool mTextWrap;
  
  QPen getIconBorderPen() const;
  QColor getTextColor() const;
  QFont getFont() const;
  virtual void draw(QPainter *painter, const QRect &rect) const;
  virtual QSize size(const QSize &targetSize) const;
};

class QCPLegend : public QObject
{
  Q_OBJECT
public:
  /*!
    Defines where the legend is positioned inside the QCustomPlot axis rect.
  */
  enum PositionStyle { psManual       ///< Position is not changed automatically. Set manually via \ref setPosition
                      ,psTopLeft      ///< Legend is positioned in the top left corner of the axis rect with distance to the border corresponding to the currently set top and left margins
                      ,psTop          ///< Legend is horizontally centered at the top of the axis rect with distance to the border corresponding to the currently set top margin
                      ,psTopRight     ///< Legend is positioned in the top right corner of the axis rect with distance to the border corresponding to the currently set top and right margins
                      ,psRight        ///< Legend is vertically centered at the right of the axis rect with distance to the border corresponding to the currently set right margin
                      ,psBottomRight  ///< Legend is positioned in the bottom right corner of the axis rect with distance to the border corresponding to the currently set bottom and right margins
                      ,psBottom       ///< Legend is horizontally centered at the bottom of the axis rect with distance to the border corresponding to the currently set bottom margin
                      ,psBottomLeft   ///< Legend is positioned in the bottom left corner of the axis rect with distance to the border corresponding to the currently set bottom and left margins
                      ,psLeft         ///< Legend is vertically centered at the left of the axis rect with distance to the border corresponding to the currently set left margin
                     };
  Q_ENUMS(PositionStyle)
  
  /*!
    Defines the selectable parts of a legend
  */
  enum SelectablePart { spNone       = 0      ///< None
                       ,spLegendBox  = 0x001  ///< The legend box as a whole
                       ,spItems      = 0x002  ///< Each legend item individually
                      };
  Q_ENUMS(SelectablePart)
  Q_DECLARE_FLAGS(SelectableParts, SelectablePart)
  
  explicit QCPLegend(QCustomPlot *parentPlot);
  virtual ~QCPLegend();
  
  // getters:
  QPen borderPen() const { return mBorderPen; }
  QBrush brush() const { return mBrush; }
  QFont font() const { return mFont; }
  QColor textColor() const { return mTextColor; }
  PositionStyle positionStyle() const { return mPositionStyle; }
  QPoint position() const { return mPosition; }
  bool autoSize() const { return mAutoSize; }
  QSize size() const { return mSize; }
  QSize minimumSize() const { return mMinimumSize; }
  bool visible() const { return mVisible; }
  int paddingLeft() const { return mPaddingLeft; }
  int paddingRight() const { return mPaddingRight; }
  int paddingTop() const { return mPaddingTop; }
  int paddingBottom() const { return mPaddingBottom; }
  int marginLeft() const { return mMarginLeft; }
  int marginRight() const { return mMarginRight; }
  int marginTop() const { return mMarginTop; }
  int marginBottom() const { return mMarginBottom; }
  int itemSpacing() const { return mItemSpacing; }
  QSize iconSize() const { return mIconSize; }
  int iconTextPadding() const { return mIconTextPadding; }
  QPen iconBorderPen() const { return mIconBorderPen; }
  SelectableParts selectable() const { return mSelectable; }
  SelectableParts selected() const { return mSelected; }
  QPen selectedBorderPen() const { return mSelectedBorderPen; }
  QPen selectedIconBorderPen() const { return mSelectedIconBorderPen; }
  QBrush selectedBrush() const { return mSelectedBrush; }
  QFont selectedFont() const { return mSelectedFont; }
  QColor selectedTextColor() const { return mSelectedTextColor; }
  
  // setters:
  void setBorderPen(const QPen &pen);
  void setBrush(const QBrush &brush);
  void setFont(const QFont &font);
  void setTextColor(const QColor &color);
  void setPositionStyle(PositionStyle legendPositionStyle);
  void setPosition(const QPoint &pixelPosition);
  void setAutoSize(bool on);
  void setSize(const QSize &size);
  void setSize(int width, int height);
  void setMinimumSize(const QSize &size);
  void setMinimumSize(int width, int height);
  void setVisible(bool on);
  void setPaddingLeft(int padding);
  void setPaddingRight(int padding);
  void setPaddingTop(int padding);
  void setPaddingBottom(int padding);
  void setPadding(int left, int right, int top, int bottom);
  void setMarginLeft(int margin);
  void setMarginRight(int margin);
  void setMarginTop(int margin);
  void setMarginBottom(int margin);
  void setMargin(int left, int right, int top, int bottom);
  void setItemSpacing(int spacing);
  void setIconSize(const QSize &size);
  void setIconSize(int width, int height);
  void setIconTextPadding(int padding);
  void setIconBorderPen(const QPen &pen);
  void setSelectable(const SelectableParts &selectable);
  void setSelected(const SelectableParts &selected);
  void setSelectedBorderPen(const QPen &pen);
  void setSelectedIconBorderPen(const QPen &pen);
  void setSelectedBrush(const QBrush &brush);
  void setSelectedFont(const QFont &font);
  void setSelectedTextColor(const QColor &color);

  // non-property methods:
  QCPAbstractLegendItem *item(int index) const;
  QCPPlottableLegendItem *itemWithPlottable(const QCPAbstractPlottable *plottable) const;
  int itemCount() const;
  bool hasItem(QCPAbstractLegendItem *item) const;
  bool hasItemWithPlottable(const QCPAbstractPlottable *plottable) const;
  bool addItem(QCPAbstractLegendItem *item);
  bool removeItem(int index);
  bool removeItem(QCPAbstractLegendItem *item);
  void clearItems();
  QList<QCPAbstractLegendItem*> selectedItems() const;
  void reArrange();
  
  bool selectTestLegend(const QPoint pos) const;
  QCPAbstractLegendItem *selectTestItem(const QPoint pos) const;
  
signals:
  void selectionChanged(QCPLegend::SelectableParts selection);
  
protected:
  // simple properties with getters and setters:
  QPen mBorderPen, mIconBorderPen;
  QBrush mBrush;
  QFont mFont;
  QColor mTextColor;
  QPoint mPosition;
  QSize mSize, mMinimumSize, mIconSize;
  PositionStyle mPositionStyle;
  bool mAutoSize, mVisible;
  int mPaddingLeft, mPaddingRight, mPaddingTop, mPaddingBottom;
  int mMarginLeft, mMarginRight, mMarginTop, mMarginBottom;
  int mItemSpacing, mIconTextPadding;
  SelectableParts mSelected, mSelectable;
  QPen mSelectedBorderPen, mSelectedIconBorderPen;
  QBrush mSelectedBrush;
  QFont mSelectedFont;
  QColor mSelectedTextColor;
  
  // internal or not explicitly exposed properties:
  QCustomPlot *mParentPlot;
  QList<QCPAbstractLegendItem*> mItems;
  QMap<QCPAbstractLegendItem*, QRect> mItemBoundingBoxes;
  
  virtual void updateSelectionState();
  virtual bool handleLegendSelection(QMouseEvent *event, bool additiveSelection, bool &modified);
  QPen getBorderPen() const;
  QBrush getBrush() const;
  // introduced methods:
  virtual void draw(QPainter *painter);
  virtual void calculateAutoSize();
  virtual void calculateAutoPosition();
  
  friend class QCustomPlot;
  friend class QCPAbstractLegendItem;
};
Q_DECLARE_OPERATORS_FOR_FLAGS(QCPLegend::SelectableParts)

class QCPAxis : public QObject
{
  Q_OBJECT
  /// \cond INCLUDE_QPROPERTIES
  Q_PROPERTY(AxisType axisType READ axisType WRITE setAxisType)
  Q_PROPERTY(ScaleType scaleType READ scaleType WRITE setScaleType)
  Q_PROPERTY(double scaleLogBase READ scaleLogBase WRITE setScaleLogBase)
  Q_PROPERTY(QRect axisRect READ axisRect WRITE setAxisRect)
  Q_PROPERTY(QCPRange range READ range WRITE setRange)
  Q_PROPERTY(bool visible READ visible WRITE setVisible)
  Q_PROPERTY(bool grid READ grid WRITE setGrid)
  Q_PROPERTY(bool subGrid READ subGrid WRITE setSubGrid)
  Q_PROPERTY(bool autoTicks READ autoTicks WRITE setAutoTicks)
  Q_PROPERTY(int autoTickCount READ autoTickCount WRITE setAutoTickCount)
  Q_PROPERTY(bool autoTickLabels READ autoTickLabels WRITE setAutoTickLabels)
  Q_PROPERTY(bool autoTickStep READ autoTickStep WRITE setAutoTickStep)
  Q_PROPERTY(bool autoSubTicks READ autoSubTicks WRITE setAutoSubTicks)
  Q_PROPERTY(bool ticks READ ticks WRITE setTicks)
  Q_PROPERTY(bool tickLabels READ tickLabels WRITE setTickLabels)
  Q_PROPERTY(int tickLabelPadding READ tickLabelPadding WRITE setTickLabelPadding)
  Q_PROPERTY(LabelType tickLabelType READ tickLabelType WRITE setTickLabelType)
  Q_PROPERTY(QFont tickLabelFont READ tickLabelFont WRITE setTickLabelFont)
  Q_PROPERTY(double tickLabelRotation READ tickLabelRotation WRITE setTickLabelRotation)
  Q_PROPERTY(QString dateTimeFormat READ dateTimeFormat WRITE setDateTimeFormat)
  Q_PROPERTY(QString numberFormat READ numberFormat WRITE setNumberFormat)
  Q_PROPERTY(double tickStep READ tickStep WRITE setTickStep)
  Q_PROPERTY(QVector<double>* tickVector READ tickVector WRITE setTickVector)
  Q_PROPERTY(QVector<QString>* tickVectorLabels READ tickVectorLabels WRITE setTickVectorLabels)
  Q_PROPERTY(int subTickCount READ subTickCount WRITE setSubTickCount)
  Q_PROPERTY(QPen basePen READ basePen WRITE setBasePen)
  Q_PROPERTY(QPen gridPen READ gridPen WRITE setGridPen)
  Q_PROPERTY(QPen subGridPen READ subGridPen WRITE setSubGridPen)
  Q_PROPERTY(QPen tickPen READ tickPen WRITE setTickPen)
  Q_PROPERTY(QPen subTickPen READ subTickPen WRITE setSubTickPen)
  Q_PROPERTY(QFont labelFont READ labelFont WRITE setLabelFont)
  Q_PROPERTY(QString label READ label WRITE setLabel)
  Q_PROPERTY(int labelPadding READ labelPadding WRITE setLabelPadding)
  /// \endcond
public:
  /*!
    Defines at which side of the axis rect the axis will appear. This also affects how the tick
    marks are drawn, on which side the labels are placed etc.
    \see setAxisType
  */
  enum AxisType { atLeft   ///< Axis is vertical and on the left side of the axis rect of the parent QCustomPlot
                 ,atRight  ///< Axis is vertical and on the right side of the axis rect of the parent QCustomPlot
                 ,atTop    ///< Axis is horizontal and on the top side of the axis rect of the parent QCustomPlot
                 ,atBottom ///< Axis is horizontal and on the bottom side of the axis rect of the parent QCustomPlot
                };
  Q_ENUMS(AxisType)
  /*!
    When automatic tick label generation is enabled (\ref setAutoTickLabels), defines how the
    numerical value (coordinate) of the tick position is translated into a string that will be
    drawn at the tick position.
    \see setTickLabelType
  */
  enum LabelType { ltNumber   ///< Tick coordinate is regarded as normal number and will be displayed as such. (see \ref setNumberFormat)
                  ,ltDateTime ///< Tick coordinate is regarded as a date/time (seconds since 1970-01-01T00:00:00 UTC, see QDateTime::toTime_t) and will be displayed and formatted as such. (see \ref setDateTimeFormat)
                 };
  Q_ENUMS(LabelType)
  /*!
    Defines the scale of an axis.
    \see setScaleType
  */
  enum ScaleType { stLinear      ///< Normal linear scaling
                  ,stLogarithmic ///< Logarithmic scaling with correspondingly transformed plots and (major) tick marks at every base power (see \ref setScaleLogBase).
                 };
  Q_ENUMS(ScaleType)
  /*!
    Defines the selectable parts of an axis.
    \see setSelectable, setSelected
  */
  enum SelectablePart { spNone       = 0      ///< None of the selectable parts
                       ,spAxis       = 0x001  ///< The axis backbone and tick marks are selectable
                       ,spTickLabels = 0x002  ///< Tick labels of this axis (numbers) are selectable (as a whole, not individually)
                       ,spAxisLabel  = 0x004  ///< The axis label is selectable
                      };
  Q_ENUMS(SelectablePart)
  Q_DECLARE_FLAGS(SelectableParts, SelectablePart)
  
  explicit QCPAxis(QCustomPlot *parentPlot, AxisType type);
  virtual ~QCPAxis();
      
  // getters:
  QCustomPlot *parentPlot() const { return mParentPlot; }
  AxisType axisType() const { return mAxisType; }
  QRect axisRect() const { return mAxisRect; }
  ScaleType scaleType() const { return mScaleType; }
  double scaleLogBase() const { return mScaleLogBase; }
  const QCPRange range() const { return mRange; }
  bool rangeReversed() const { return mRangeReversed; }
  bool visible() const { return mVisible; }
  bool grid() const { return mGrid; }
  bool subGrid() const { return mSubGrid; }
  bool autoTicks() const { return mAutoTicks; }
  int autoTickCount() const { return mAutoTickCount; }
  bool autoTickLabels() const { return mAutoTickLabels; }
  bool autoTickStep() const { return mAutoTickStep; }
  bool autoSubTicks() const { return mAutoSubTicks; }
  bool ticks() const { return mTicks; }
  bool tickLabels() const { return mTickLabels; }
  int tickLabelPadding() const { return mTickLabelPadding; }
  LabelType tickLabelType() const { return mTickLabelType; }
  QFont tickLabelFont() const { return mTickLabelFont; }
  QColor tickLabelColor() const { return mTickLabelColor; }
  double tickLabelRotation() const { return mTickLabelRotation; }
  QString dateTimeFormat() const { return mDateTimeFormat; }
  QString numberFormat() const;
  int numberPrecision() const { return mNumberPrecision; }
  double tickStep() const { return mTickStep; }
  QVector<double> *tickVector() const { return mTickVector; }
  QVector<QString> *tickVectorLabels() const { return mTickVectorLabels; }
  int tickLengthIn() const { return mTickLengthIn; }
  int tickLengthOut() const { return mTickLengthOut; }
  int subTickCount() const { return mSubTickCount; }
  int subTickLengthIn() const { return mSubTickLengthIn; }
  int subTickLengthOut() const { return mSubTickLengthOut; }
  QPen basePen() const { return mBasePen; }
  QPen gridPen() const { return mGridPen; }
  QPen subGridPen() const { return mSubGridPen; }
  QPen zeroLinePen() const { return mZeroLinePen; }
  QPen tickPen() const { return mTickPen; }
  QPen subTickPen() const { return mSubTickPen; }
  QFont labelFont() const { return mLabelFont; }
  QColor labelColor() const { return mLabelColor; }
  QString label() const { return mLabel; }
  int labelPadding() const { return mLabelPadding; }
  int padding() const { return mPadding; }
  SelectableParts selected() const { return mSelected; }
  SelectableParts selectable() const { return mSelectable; }
  QFont selectedTickLabelFont() const { return mSelectedTickLabelFont; }
  QFont selectedLabelFont() const { return mSelectedLabelFont; }
  QColor selectedTickLabelColor() const { return mSelectedTickLabelColor; }
  QColor selectedLabelColor() const { return mSelectedLabelColor; }
  QPen selectedBasePen() const { return mSelectedBasePen; }
  QPen selectedTickPen() const { return mSelectedTickPen; }
  QPen selectedSubTickPen() const { return mSelectedSubTickPen; }
  
  // setters:
  void setScaleType(ScaleType type);
  void setScaleLogBase(double base);
  void setRange(double lower, double upper);
  void setRange(double position, double size, Qt::AlignmentFlag alignment);
  void setRangeLower(double lower);
  void setRangeUpper(double upper);
  void setRangeReversed(bool reversed);
  void setVisible(bool on);
  void setGrid(bool show);
  void setSubGrid(bool show);
  void setAutoTicks(bool on);
  void setAutoTickCount(int approximateCount);
  void setAutoTickLabels(bool on);
  void setAutoTickStep(bool on);
  void setAutoSubTicks(bool on);
  void setTicks(bool show);
  void setTickLabels(bool show);
  void setTickLabelPadding(int padding);
  void setTickLabelType(LabelType type);
  void setTickLabelFont(const QFont &font);
  void setTickLabelColor(const QColor &color);
  void setTickLabelRotation(double degrees);
  void setDateTimeFormat(const QString &format);
  void setNumberFormat(const QString &formatCode);
  void setNumberPrecision(int precision);
  void setTickStep(double step);
  void setTickVector(QVector<double> *vec, bool copy=false);
  void setTickVectorLabels(QVector<QString> *vec, bool copy=false);
  void setTickLength(int inside, int outside=0);
  void setSubTickCount(int count);
  void setSubTickLength(int inside, int outside=0);
  void setBasePen(const QPen &pen);
  void setGridPen(const QPen &pen);
  void setSubGridPen(const QPen &pen);
  void setZeroLinePen(const QPen &pen);
  void setTickPen(const QPen &pen);
  void setSubTickPen(const QPen &pen);
  void setLabelFont(const QFont &font);
  void setLabelColor(const QColor &color);
  void setLabel(const QString &str);
  void setLabelPadding(int padding);
  void setPadding(int padding);
  void setSelectedTickLabelFont(const QFont &font);
  void setSelectedLabelFont(const QFont &font);
  void setSelectedTickLabelColor(const QColor &color);
  void setSelectedLabelColor(const QColor &color);
  void setSelectedBasePen(const QPen &pen);
  void setSelectedTickPen(const QPen &pen);
  void setSelectedSubTickPen(const QPen &pen);
  
  // non-property methods:
  Qt::Orientation orientation() const { return mOrientation; }
  void moveRange(double diff);
  void scaleRange(double factor, double center);
  void setScaleRatio(const QCPAxis *otherAxis, double ratio=1.0);
  double pixelToCoord(double value) const;
  double coordToPixel(double value) const;
  SelectablePart selectTest(QPoint pos) const;
  
public slots:
  // slot setters:
  void setRange(const QCPRange &range);
  void setSelectable(const QCPAxis::SelectableParts &selectable);
  void setSelected(const QCPAxis::SelectableParts &selected);
  
signals:
  void ticksRequest();
  void rangeChanged(const QCPRange &newRange);
  void selectionChanged(QCPAxis::SelectableParts selection);

protected:
  // simple properties with getters and setters:
  QVector<double> *mTickVector;
  QVector<QString> *mTickVectorLabels;
  QCPRange mRange;
  QString mDateTimeFormat;
  QString mLabel;
  QRect mAxisRect;
  QPen mBasePen, mGridPen, mSubGridPen, mZeroLinePen, mTickPen, mSubTickPen;
  QFont mTickLabelFont, mLabelFont;
  QColor mTickLabelColor, mLabelColor;
  LabelType mTickLabelType;
  ScaleType mScaleType;
  AxisType mAxisType;
  double mTickStep;
  double mScaleLogBase, mScaleLogBaseLogInv;
  int mSubTickCount, mTickLengthIn, mTickLengthOut, mSubTickLengthIn, mSubTickLengthOut;
  int mAutoTickCount;
  int mTickLabelPadding, mLabelPadding, mPadding;
  double mTickLabelRotation;
  bool mVisible, mGrid, mSubGrid, mTicks, mTickLabels, mAutoTicks, mAutoTickLabels, mAutoTickStep, mAutoSubTicks;
  bool mRangeReversed;
  SelectableParts mSelectable, mSelected;
  QFont mSelectedTickLabelFont, mSelectedLabelFont;
  QColor mSelectedTickLabelColor, mSelectedLabelColor;
  QPen mSelectedBasePen, mSelectedTickPen, mSelectedSubTickPen;
  QRect mAxisSelectionBox, mTickLabelsSelectionBox, mLabelSelectionBox;
  
  // internal or not explicitly exposed properties:
  QCustomPlot *mParentPlot;
  QVector<double> *mSubTickVector;
  QChar mExponentialChar, mPositiveSignChar;
  int mNumberPrecision;
  char mNumberFormatChar;
  bool mNumberBeautifulPowers, mNumberMultiplyCross;
  Qt::Orientation mOrientation;
  
  // internal setters:
  void setAxisType(AxisType type);
  void setAxisRect(const QRect &rect);
  
  // introduced methods:
  virtual void generateTickVectors();
  virtual void generateAutoTicks();
  virtual int calculateAutoSubTickCount(double tickStep) const;
  virtual int calculateMargin() const;
  virtual void drawGrid(QPainter *painter);
  virtual void drawSubGrid(QPainter *painter);
  virtual void drawAxis(QPainter *painter);
  virtual void drawTickLabel(QPainter *painter, double position, int distanceToAxis, const QString &text, QSize *tickLabelsSize);
  virtual void getMaxTickLabelSize(const QFont &font, const QString &text, QSize *tickLabelsSize) const;
  virtual bool handleAxisSelection(QMouseEvent *event, bool additiveSelection, bool &modified);
  
  // basic non virtual helpers:
  void visibleTickBounds(int &lowIndex, int &highIndex) const;
  double baseLog(double value) const;
  double basePow(double value) const;
  
  // helpers to get the right pen/font depending on selection state:
  QPen getBasePen() const;
  QPen getTickPen() const;
  QPen getSubTickPen() const;
  QFont getTickLabelFont() const;
  QFont getLabelFont() const;
  QColor getTickLabelColor() const;
  QColor getLabelColor() const;
  
  friend class QCustomPlot;
};
Q_DECLARE_OPERATORS_FOR_FLAGS(QCPAxis::SelectableParts)

class QCustomPlot : public QWidget
{
  Q_OBJECT
  /// \cond INCLUDE_QPROPERTIES
  Q_PROPERTY(QString title READ title WRITE setTitle)
  Q_PROPERTY(QRect axisRect READ axisRect WRITE setAxisRect)
  Q_PROPERTY(int marginLeft READ marginLeft WRITE setMarginLeft)
  Q_PROPERTY(int marginRight READ marginRight WRITE setMarginRight)
  Q_PROPERTY(int marginTop READ marginTop WRITE setMarginTop)
  Q_PROPERTY(int marginBottom READ marginBottom WRITE setMarginBottom)
  Q_PROPERTY(int autoMargin READ autoMargin WRITE setAutoMargin)
  Q_PROPERTY(QColor color READ color WRITE setColor)
  Q_PROPERTY(Qt::Orientations rangeDrag READ rangeDrag WRITE setRangeDrag)
  Q_PROPERTY(Qt::Orientations rangeZoom READ rangeZoom WRITE setRangeZoom)
  /// \endcond
public:
  /*!
    Defines what elements of a plot will be drawn antialiased.
    
    \c AntialiasedElements is a flag of or-combined elements of this enum type.
    \see setAntialiasedElements, setAntialiasedElement
  */
  enum AntialiasedElement { aeAxes       = 0x001 ///< Axis base line and tick marks
                           ,aeGrid       = 0x002 ///< Grid lines
                           ,aeSubGrid    = 0x004 ///< Sub grid lines
                           ,aeGraphs     = 0x008 ///< deprecated, see aePlottables
                           ,aePlottables = 0x008 ///< Any lines of plottables (excluding error bars, see element \ref aeErrorBars)
                           ,aeScatters   = 0x010 ///< Scatter symbols of graphs (excluding scatter symbols of type ssPixmap)
                           ,aeErrorBars  = 0x020 ///< Error bars
                           ,aeFills      = 0x040 ///< Borders of fills (e.g. under or between graphs)
                           ,aeZeroLine   = 0x080 ///< Zero-lines, see \ref QCPAxis::setZeroLinePen
                          };
  Q_ENUMS(AntialiasedElement)
  Q_DECLARE_FLAGS(AntialiasedElements, AntialiasedElement)
  
  /*!
    Defines the mouse interactions possible with QCustomPlot
    
    \c Interactions is a flag of or-combined elements of this enum type.
    \see setInteractions, setInteraction
  */
  enum Interaction { iRangeDrag         = 0x001 ///< Axis ranges are draggable (see \ref setRangeDrag, \ref setRangeDragAxes)
                    ,iRangeZoom         = 0x002 ///< Axis ranges are zoomable with the mouse wheel (see \ref setRangeZoom, \ref setRangeZoomAxes)
                    ,iMultiSelect       = 0x004 ///< The user can select multiple objects by holding Control (Ctrl) while clicking
                    ,iSelectTitle       = 0x008 ///< The plot title is selectable
                    ,iSelectPlottables  = 0x010 ///< Plottables are selectable
                    ,iSelectAxes        = 0x020 ///< Axes are selectable (or parts of them, see QCPAxis::setSelectable)
                    ,iSelectLegend      = 0x040 ///< Legends are selectable (or their child items, see QCPLegend::setSelectable)
                   };
  Q_ENUMS(Interaction)
  Q_DECLARE_FLAGS(Interactions, Interaction)
  
  explicit QCustomPlot(QWidget *parent = 0);
  virtual ~QCustomPlot();
  
  // getters:
  QString title() const { return mTitle; }
  QFont titleFont() const { return mTitleFont; }
  QColor titleColor() const { return mTitleColor; }
  QRect axisRect() const { return mAxisRect; }
  int marginLeft() const { return mMarginLeft; }
  int marginRight() const { return mMarginRight; }
  int marginTop() const { return mMarginTop; }
  int marginBottom() const { return mMarginBottom; }
  bool autoMargin() const { return mAutoMargin; }
  QColor color() const { return mColor; }
  Qt::Orientations rangeDrag() const { return mRangeDrag; }
  Qt::Orientations rangeZoom() const { return mRangeZoom; }
  QCPAxis *rangeDragAxis(Qt::Orientation orientation);
  QCPAxis *rangeZoomAxis(Qt::Orientation orientation);
  double rangeZoomFactor(Qt::Orientation orientation);
  const AntialiasedElements antialiasedElements() const { return mAntialiasedElements; }
  bool autoAddPlottableToLegend() const { return mAutoAddPlottableToLegend; }
  QPixmap axisBackground() const { return mAxisBackground; }
  bool axisBackgroundScaled() const { return mAxisBackgroundScaled; }
  Qt::AspectRatioMode axisBackgroundScaledMode() const { return mAxisBackgroundScaledMode; }
  const Interactions interactions() const { return mInteractions; }
  int selectionTolerance() const { return mSelectionTolerance; }
  QFont selectedTitleFont() const { return mSelectedTitleFont; }
  QColor selectedTitleColor() const { return mSelectedTitleColor; }
  bool titleSelected() const { return mTitleSelected; }
  
  // setters:
  void setTitle(const QString &title);
  void setTitleFont(const QFont &font);
  void setTitleColor(const QColor &color);
  void setAxisRect(const QRect &arect);
  void setMarginLeft(int margin);
  void setMarginRight(int margin);
  void setMarginTop(int margin);
  void setMarginBottom(int margin);
  void setMargin(int left, int right, int top, int bottom);
  void setAutoMargin(bool enabled);
  void setColor(const QColor &color);
  void setRangeDrag(Qt::Orientations orientations);
  void setRangeZoom(Qt::Orientations orientations);
  void setRangeDragAxes(QCPAxis *horizontal, QCPAxis *vertical);
  void setRangeZoomAxes(QCPAxis *horizontal, QCPAxis *vertical);
  void setRangeZoomFactor(double horizontalFactor, double verticalFactor);
  void setRangeZoomFactor(double factor);
  void setAntialiasedElements(const AntialiasedElements &antialiasedElements);
  void setAntialiasedElement(AntialiasedElement antialiasedElement, bool enabled=true);
  void setAutoAddPlottableToLegend(bool on);
  void setAxisBackground(const QPixmap &pm);
  void setAxisBackground(const QPixmap &pm, bool scaled, Qt::AspectRatioMode mode=Qt::KeepAspectRatioByExpanding);
  void setAxisBackgroundScaled(bool scaled);
  void setAxisBackgroundScaledMode(Qt::AspectRatioMode mode);
  void setInteractions(const Interactions &interactions);
  void setInteraction(const Interaction &interaction, bool enabled=true);
  void setSelectionTolerance(int pixels);
  void setSelectedTitleFont(const QFont &font);
  void setSelectedTitleColor(const QColor &color);
  void setTitleSelected(bool selected);
  
  // non-property methods:
  // plottable interface:
  QCPAbstractPlottable *plottable(int index);
  QCPAbstractPlottable *plottable();
  bool addPlottable(QCPAbstractPlottable *plottable);
  bool removePlottable(QCPAbstractPlottable *plottable);
  bool removePlottable(int index);
  int clearPlottables();
  int plottableCount() const;
  QList<QCPAbstractPlottable*> selectedPlottables() const;
  QCPAbstractPlottable *plottableAt(const QPoint &pos, bool onlySelectable=false) const;
  
  // specialized interface for QCPGraph:
  QCPGraph *graph(int index) const;
  QCPGraph *graph() const;
  QCPGraph *addGraph(QCPAxis *keyAxis=0, QCPAxis *valueAxis=0);
  bool removeGraph(QCPGraph *graph);
  bool removeGraph(int index);
  int clearGraphs();
  int graphCount() const;
  QList<QCPGraph*> selectedGraphs() const;
  
  QList<QCPAxis*> selectedAxes() const;
  QList<QCPLegend*> selectedLegends() const;
  void setupFullAxesBox();
  void savePdf(const QString &fileName, bool noCosmeticPen=false, int width=0, int height=0);
  //void saveSvg(const QString &fileName);
  void savePng(const QString &fileName, int width=0, int height=0);
  void savePngScaled(const QString &fileName, double scale, int width=0, int height=0);
  
  QCPAxis *xAxis, *yAxis, *xAxis2, *yAxis2;
  QCPLegend *legend;
  
public slots:
  void deselectAll();
  void replot();
  void rescaleAxes();
  
signals:
  void mouseDoubleClick(QMouseEvent *event);
  void mousePress(QMouseEvent *event);
  void mouseMove(QMouseEvent *event);
  void mouseRelease(QMouseEvent *event);
  void mouseWheel(QWheelEvent *event);
  
  void plottableClick(QCPAbstractPlottable *plottable, QMouseEvent *event);
  void plottableDoubleClick(QCPAbstractPlottable *plottable, QMouseEvent *event);
  void axisClick(QCPAxis *axis, QCPAxis::SelectablePart part, QMouseEvent *event);
  void axisDoubleClick(QCPAxis *axis, QCPAxis::SelectablePart part, QMouseEvent *event);
  void legendClick(QCPLegend *legend, QCPAbstractLegendItem *item, QMouseEvent *event);
  void legendDoubleClick(QCPLegend *legend,  QCPAbstractLegendItem *item, QMouseEvent *event);
  void titleClick(QMouseEvent *event);
  void titleDoubleClick(QMouseEvent *event);
  
  void selectionChangedByUser();
  void beforeReplot();
  void afterReplot();
  
protected:
  QPixmap buffer;
  QString mTitle;
  QFont mTitleFont;
  QColor mTitleColor;
  QRect mViewport;
  QRect mAxisRect;
  int mMarginLeft, mMarginRight, mMarginTop, mMarginBottom;
  bool mAutoMargin, mAutoAddPlottableToLegend;
  QColor mColor;
  QList<QCPAbstractPlottable*> mPlottables;
  QList<QCPGraph*> mGraphs; // extra list of items also in mPlottables that are of type QCPGraph
  Qt::Orientations mRangeDrag, mRangeZoom;
  QCPAxis *mRangeDragHorzAxis, *mRangeDragVertAxis, *mRangeZoomHorzAxis, *mRangeZoomVertAxis;
  double mRangeZoomFactorHorz, mRangeZoomFactorVert;
  bool mDragging;
  QPoint mDragStart;
  QCPRange mDragStartHorzRange, mDragStartVertRange;
  AntialiasedElements mAntialiasedElements;
  QPixmap mAxisBackground, mScaledAxisBackground;
  bool mAxisBackgroundScaled;
  Qt::AspectRatioMode mAxisBackgroundScaledMode;
  Interactions mInteractions;
  int mSelectionTolerance;
  QFont mSelectedTitleFont;
  QColor mSelectedTitleColor;
  bool mTitleSelected;
  QRect mTitleBoundingBox;
  bool mReplotting;
  
  // reimplemented methods:
  virtual void paintEvent(QPaintEvent *event);
  virtual void resizeEvent(QResizeEvent *event);
  virtual void mouseDoubleClickEvent(QMouseEvent *event);
  virtual void mousePressEvent(QMouseEvent *event);
  virtual void mouseMoveEvent(QMouseEvent *event);
  virtual void mouseReleaseEvent(QMouseEvent *event);
  virtual void wheelEvent(QWheelEvent *event);
  // event helpers:
  virtual bool handlePlottableSelection(QMouseEvent *event, bool additiveSelection, bool &modified);  
  virtual bool handleAxisSelection(QMouseEvent *event, bool additiveSelection, bool &modified);
  virtual bool handleTitleSelection(QMouseEvent *event, bool additiveSelection, bool &modified);
  
  // introduced methods:
  virtual void draw(QPainter *painter);
  virtual void drawAxisBackground(QPainter *painter);
  
  // helpers:
  void updateAxisRect();
  bool selectTestTitle(const QPoint &pos) const;
  
  
  friend class QCPLegend;
  friend class QCPAxis;
};
Q_DECLARE_OPERATORS_FOR_FLAGS(QCustomPlot::AntialiasedElements)
Q_DECLARE_OPERATORS_FOR_FLAGS(QCustomPlot::Interactions)

#endif // QCUSTOMPLOT_H
