//
// project:      dwfs core
// file:
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
//

#ifndef PLANEGRIDDIALOG_H
#define PLANEGRIDDIALOG_H

#include <QDialog>

namespace Ui {
    class PlaneGridDialog;
}

class ViewManager;

/** Setup coordinate plane display.
  */
class PlaneGridDialog : public QDialog
{
  Q_OBJECT
  public:

    /// create dialog
    PlaneGridDialog(QWidget *parent, ViewManager *v);

    /// destroy
    ~PlaneGridDialog();

  signals:

    /// emitted when redraw is needed
    void planesChanged();

  private slots:

    /// toggle plane
    void toggleX(bool flag=true);

    /// toggle plane
    void toggleY(bool flag=true);

    /// toggle plane
    void toggleZ(bool flag=true);

  protected:

    /// language change etc
    void changeEvent(QEvent *e);

  private:

    /// view to modify
    ViewManager *view;

    /// UI object
    Ui::PlaneGridDialog *ui;
};

#endif // PLANEGRIDDIALOG_H
