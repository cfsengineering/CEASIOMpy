//
// project:      dwfs core
// file:         endcapdlg.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Set end cap properties

#ifndef ENDCAPDLG_H
#define ENDCAPDLG_H

#ifndef Q_MOC_RUN
#include "component.h"
#endif
#include <QDialog>

namespace Ui {
    class EndCapDlg;
}

class EndCapDlg : public QDialog
{
    Q_OBJECT

  public:

    /// create dialog w/o attached component
    EndCapDlg(QWidget *parent);

    /// destroy widget
    ~EndCapDlg();

    /// attach to component to change
    void attach(ComponentPtr cp);

  signals:

    /// geometry/display may need update
    void geometryChanged();

  private slots:

    /// cap type changed
    void frontTypeChanged(int idx);

    /// cap type changed
    void rearTypeChanged(int idx);

    /// height changed
    void frontHeightChanged();

    /// height changed
    void rearHeightChanged();

  protected:

    void changeEvent(QEvent *e);

  private:

    /// component to modify
    ComponentPtr cmp;

    /// UI object
    Ui::EndCapDlg *ui;
};

#endif // ENDCAPDLG_H
