#ifndef DLGGLOBALTRANSFORM_H
#define DLGGLOBALTRANSFORM_H

#include <QDialog>
#include <genua/forward.h>

namespace Ui {
class DlgGlobalTransform;
}

class DlgGlobalTransform : public QDialog
{
  Q_OBJECT

public:

  /// construct
  explicit DlgGlobalTransform(QWidget *parent = 0);

  /// destroy UI
  ~DlgGlobalTransform();

  /// access coordinates
  Vct3 translation() const;

  /// access scaling value
  double scale() const;

private:

  /// widget
  Ui::DlgGlobalTransform *ui;
};

#endif // DLGGLOBALTRANSFORM_H
