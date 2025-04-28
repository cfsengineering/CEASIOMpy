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

#ifndef QGLVIEWER_QGLVIEWER_H
#define QGLVIEWER_QGLVIEWER_H

#include "camera.h"

#if QT_VERSION >= 0x040000
# include <QMap>
#else
# include <qmap.h>
#endif

class QTabWidget;

namespace qglviewer {
	class MouseGrabber;
}

#if QT_VERSION >= 0x040000
// Qt::ButtonState was split into Qt::KeyboardModifiers and Qt::MouseButtons in Qt 4.
# define QtKeyboardModifiers Qt::KeyboardModifiers
# define QtMouseButtons Qt::MouseButtons
#else
# define QtKeyboardModifiers Qt::ButtonState
# define QtMouseButtons Qt::ButtonState
#endif

/*! \brief A versatile 3D OpenGL viewer based on QGLWidget.
\class QGLViewer qglviewer.h QGLViewer/qglviewer.h

It features many classical viewer functionalities, such as a camera trackball, manipulated objects,
snapshot saving and much <a href="../features.html">more</a>. Its main goal is to ease the development
of new 3D applications.

New users should read the <a href="../introduction.html">introduction page</a> to get familiar with
important notions such as sceneRadius(), sceneCenter() and the world coordinate system. Try the
numerous simple <a href="../examples/index.html">examples</a> to discover the possibilities and
understand how it works.

<h3>Usage</h3>

To use a QGLViewer, derive you viewer class from the QGLViewer and overload its draw() virtual
method. See the <a href="../examples/simpleViewer.html">simpleViewer example</a> for an illustration.

An other option is to connect your drawing methods to the signals emitted by the QGLViewer (Qt's
callback mechanism). See the <a href="../examples/callback.html">callback example</a> for a
complete implementation.

\nosubgrouping */
class QGLVIEWER_EXPORT QGLViewer : public QGLWidget
{
	Q_OBJECT

public:
	// Complete implementation is provided so that the constructor is defined with QT3_SUPPORT when .h is included.
	// (Would not be available otherwise since lib is compiled without QT3_SUPPORT).
#if QT_VERSION < 0x040000 || defined QT3_SUPPORT
	explicit QGLViewer(QWidget* parent=NULL, const char* name=0, const QGLWidget* shareWidget=0, Qt::WFlags flags=0)
		: QGLWidget(parent, name, shareWidget, flags)
	{ defaultConstructor(); }

	explicit QGLViewer(const QGLFormat& format, QWidget* parent=0, const char* name=0, const QGLWidget* shareWidget=0,Qt::WFlags flags=0)
		: QGLWidget(format, parent, name, shareWidget, flags)
	{ defaultConstructor(); }

	QGLViewer(QGLContext* context, QWidget* parent, const char* name=0, const QGLWidget* shareWidget=0, Qt::WFlags flags=0)
# if QT_VERSION >= 0x030200
		: QGLWidget(context, parent, name, shareWidget, flags) {
# else
		// MOC_SKIP_BEGIN
		: QGLWidget(parent, name, shareWidget, flags) {
			Q_UNUSED(context);
			// MOC_SKIP_END
# endif
			defaultConstructor(); }
#else

    explicit QGLViewer(QWidget* parent=0, const QGLWidget* shareWidget=0, Qt::WindowFlags flags=0);
    explicit QGLViewer(QGLContext *context, QWidget* parent=0, const QGLWidget* shareWidget=0, Qt::WindowFlags flags=0);
    explicit QGLViewer(const QGLFormat& format, QWidget* parent=0, const QGLWidget* shareWidget=0, Qt::WindowFlags flags=0);
#endif

	virtual ~QGLViewer();

	/*! @name Display of visual hints */
	//@{
public:
	/*! Returns \c true if the world axis is drawn by the viewer.

	Set by setAxisIsDrawn() or toggleAxisIsDrawn(). Default value is \c false. */
	bool axisIsDrawn() const { return axisIsDrawn_; };
	/*! Returns \c true if a XY grid is drawn by the viewer.

	Set by setGridIsDrawn() or toggleGridIsDrawn(). Default value is \c false. */
	bool gridIsDrawn() const { return gridIsDrawn_; };
	/*! Returns \c true if the viewer displays the current frame rate (Frames Per Second).

	Use QApplication::setFont() to define the display font (see drawText()).

	Set by setFPSIsDisplayed() or toggleFPSIsDisplayed(). Use currentFPS() to get the current FPS.
	Default value is \c false. */
	bool FPSIsDisplayed() const { return FPSIsDisplayed_; };
	/*! Returns \c true if text display (see drawText()) is enabled.

	Set by setTextIsEnabled() or toggleTextIsEnabled(). This feature conveniently removes all the
	possibly displayed text, cleaning display. Default value is \c true. */
	bool textIsEnabled() const { return textIsEnabled_; };

	/*! Returns \c true if the camera() is being edited in the viewer.

	Set by setCameraIsEdited() or toggleCameraIsEdited(). Default value is \p false.

	The current implementation is limited: the defined camera() paths (see
	qglviewer::Camera::keyFrameInterpolator()) are simply displayed using
	qglviewer::Camera::drawAllPaths(). Actual camera and path edition will be implemented in the
	future. */
	bool cameraIsEdited() const { return cameraIsEdited_; }


	public slots:
		/*! Sets the state of axisIsDrawn(). Emits the axisIsDrawnChanged() signal. See also toggleAxisIsDrawn(). */
		void setAxisIsDrawn(bool draw=true) { axisIsDrawn_ = draw; emit axisIsDrawnChanged(draw); if (updateGLOK_) updateGL(); };
		/*! Sets the state of gridIsDrawn(). Emits the gridIsDrawnChanged() signal. See also toggleGridIsDrawn(). */
		void setGridIsDrawn(bool draw=true) { gridIsDrawn_ = draw; emit gridIsDrawnChanged(draw); if (updateGLOK_) updateGL(); };
		/*! Sets the state of FPSIsDisplayed(). Emits the FPSIsDisplayedChanged() signal. See also toggleFPSIsDisplayed(). */
		void setFPSIsDisplayed(bool display=true) { FPSIsDisplayed_ = display; emit FPSIsDisplayedChanged(display); if (updateGLOK_) updateGL(); };
		/*! Sets the state of textIsEnabled(). Emits the textIsEnabledChanged() signal. See also toggleTextIsEnabled(). */
		void setTextIsEnabled(bool enable=true) { textIsEnabled_ = enable; emit textIsEnabledChanged(enable); if (updateGLOK_) updateGL(); };
		void setCameraIsEdited(bool edit=true);

		/*! Toggles the state of axisIsDrawn(). See also setAxisIsDrawn(). */
		void toggleAxisIsDrawn() { setAxisIsDrawn(!axisIsDrawn()); };
		/*! Toggles the state of gridIsDrawn(). See also setGridIsDrawn(). */
		void toggleGridIsDrawn() { setGridIsDrawn(!gridIsDrawn()); };
		/*! Toggles the state of FPSIsDisplayed(). See also setFPSIsDisplayed(). */
		void toggleFPSIsDisplayed() { setFPSIsDisplayed(!FPSIsDisplayed()); };
		/*! Toggles the state of textIsEnabled(). See also setTextIsEnabled(). */
		void toggleTextIsEnabled() { setTextIsEnabled(!textIsEnabled()); };
		/*! Toggles the state of cameraIsEdited(). See also setCameraIsEdited(). */
		void toggleCameraIsEdited() { setCameraIsEdited(!cameraIsEdited()); };
		//@}


		/*! @name Viewer's colors */
		//@{
public:
	/*! Returns the background color of the viewer.

	This method is provided for convenience since the background color is an OpenGL state variable
	set with \c glClearColor(). However, this internal representation has the advantage that it is
	saved (resp. restored) with saveStateToFile() (resp. restoreStateFromFile()).

	Use setBackgroundColor() to define and activate a background color.

	\attention Each QColor component is an integer ranging from 0 to 255. This differs from the float
	values used by \c glClearColor() which are in the 0.0-1.0 range. Default value is (51, 51, 51)
	(dark gray). You may have to change foregroundColor() accordingly.

	\attention This method does not return the current OpenGL clear color as \c glGet() does. Instead,
	it returns the QGLViewer internal variable. If you directly use \c glClearColor() or \c
	qglClearColor() instead of setBackgroundColor(), the two results will differ. */
  QColor backgroundColor() const { return backgroundColor_; }

	/*! Returns the foreground color used by the viewer.

	This color is used when FPSIsDisplayed(), gridIsDrawn(), to display the camera paths when the
	cameraIsEdited().

	\attention Each QColor component is an integer in the range 0-255. This differs from the float
	values used by \c glColor3f() which are in the range 0-1. Default value is (180, 180, 180) (light
	gray).

	Use \c qglColor(foregroundColor()) to set the current OpenGL color to the foregroundColor().

	See also backgroundColor(). */
  QColor foregroundColor() const { return foregroundColor_; }
	public slots:
		/*! Sets the backgroundColor() of the viewer and calls \c qglClearColor(). See also
		setForegroundColor(). */
    void setBackgroundColor(const QColor& color) { backgroundColor_=color; qglClearColor(color); }
		/*! Sets the foregroundColor() of the viewer, used to draw visual hints. See also setBackgroundColor(). */
    void setForegroundColor(const QColor& color) { foregroundColor_ = color; }
		//@}


		/*! @name Scene dimensions */
		//@{
public:
	/*! Returns the scene radius.

	The entire displayed scene should be included in a sphere of radius sceneRadius(), centered on
	sceneCenter().

	This approximate value is used by the camera() to set qglviewer::Camera::zNear() and
	qglviewer::Camera::zFar(). It is also used to showEntireScene() or to scale the world axis
	display..

	Default value is 1.0. This method is equivalent to camera()->sceneRadius(). See
	setSceneRadius(). */
	float sceneRadius() const { return camera()->sceneRadius(); }
	/*! Returns the scene center, defined in world coordinates.

	See sceneRadius() for details.

	Default value is (0,0,0). Simply a wrapper for camera()->sceneCenter(). Set using
	setSceneCenter().

	Do not mismatch this value (that only depends on the scene) with the qglviewer::Camera::revolveAroundPoint(). */
	qglviewer::Vec sceneCenter() const { return camera()->sceneCenter(); }

	public slots:
		/*! Sets the sceneRadius().

		The camera() qglviewer::Camera::flySpeed() is set to 1% of this value by this method. Simple
		wrapper around camera()->setSceneRadius(). */
		virtual void setSceneRadius(float radius) { camera()->setSceneRadius(radius); }

		/*! Sets the sceneCenter(), defined in world coordinates.

		\attention The qglviewer::Camera::revolveAroundPoint() is set to the sceneCenter() value by this
		method. */
		virtual void setSceneCenter(const qglviewer::Vec& center) { camera()->setSceneCenter(center); }

		/*! Convenient way to call setSceneCenter() and setSceneRadius() from a (world axis aligned) bounding box of the scene.

		This is equivalent to:
		\code
		setSceneCenter((m+M)/2.0);
		setSceneRadius(0.5*(M-m).norm());
		\endcode */
		void setSceneBoundingBox(const qglviewer::Vec& min, const qglviewer::Vec& max) { camera()->setSceneBoundingBox(min,max); }

		/*! Moves the camera so that the entire scene is visible.

		Simple wrapper around qglviewer::Camera::showEntireScene(). */
		void showEntireScene() { camera()->showEntireScene(); if (updateGLOK_) updateGL(); }
		//@}


		/*! @name Associated objects */
		//@{
public:
	/*! Returns the associated qglviewer::Camera, never \c NULL. */
	qglviewer::Camera* camera() const { return camera_; };

	/*! Returns the viewer's qglviewer::ManipulatedFrame.

	This qglviewer::ManipulatedFrame can be moved with the mouse when the associated mouse bindings
	are used (default is when pressing the \c Control key with any mouse button). Use
	setMouseBinding() to define new bindings.

	See the <a href="../examples/manipulatedFrame.html">manipulatedFrame example</a> for a complete
	implementation.

	Default value is \c NULL, meaning that no qglviewer::ManipulatedFrame is set. */
	qglviewer::ManipulatedFrame* manipulatedFrame() const { return manipulatedFrame_; };

	public slots:
		void setCamera(qglviewer::Camera* const camera);
		void setManipulatedFrame(qglviewer::ManipulatedFrame* frame);
		//@}


		/*! @name Mouse grabbers */
		//@{
public:
	/*! Returns the current qglviewer::MouseGrabber, or \c NULL if no qglviewer::MouseGrabber
	currently grabs mouse events.

	When qglviewer::MouseGrabber::grabsMouse(), the different mouse events are sent to the
	mouseGrabber() instead of their usual targets (camera() or manipulatedFrame()).

	See the qglviewer::MouseGrabber documentation for details on MouseGrabber's mode of operation.

	In order to use MouseGrabbers, you need to enable mouse tracking (so that mouseMoveEvent() is
	called even when no mouse button is pressed). Add this line in init() or in your viewer
	constructor:
	\code
	setMouseTracking(true);
	\endcode
	Note that mouse tracking is disabled by default. Use QWidget::hasMouseTracking() to
	retrieve current state. */
	qglviewer::MouseGrabber* mouseGrabber() const { return mouseGrabber_; };

	void setMouseGrabberIsEnabled(const qglviewer::MouseGrabber* const mouseGrabber, bool enabled=true);
	/*! Returns \c true if \p mouseGrabber is enabled.

	Default value is \c true for all MouseGrabbers. When set to \c false using
	setMouseGrabberIsEnabled(), the specified \p mouseGrabber will never become the mouseGrabber() of
	this QGLViewer. This is useful when you use several viewers: some MouseGrabbers may only have a
	meaning for some specific viewers and should not be selectable in others.

	You can also use qglviewer::MouseGrabber::removeFromMouseGrabberPool() to completely disable a
	MouseGrabber in all the QGLViewers. */
	bool mouseGrabberIsEnabled(const qglviewer::MouseGrabber* const mouseGrabber) { return !disabledMouseGrabbers_.contains(reinterpret_cast<size_t>(mouseGrabber)); };
	public slots:
		void setMouseGrabber(qglviewer::MouseGrabber* mouseGrabber);
		//@}


		/*! @name State of the viewer */
		//@{
public:
	/*! Returns the aspect ratio of the viewer's widget (width() / height()). */
	float aspectRatio() const { return static_cast<float>(width())/static_cast<float>(height()); };
	/*! Returns the current averaged viewer frame rate.

	This value is computed and averaged over 20 successive frames. It only changes every 20 draw()
	(previously computed value is otherwise returned).

	This method is useful for true real-time applications that may adapt their computational load
	accordingly in order to maintain a given frequency.

	This value is meaningful only when draw() is regularly called, either using a \c QTimer, when
	animationIsStarted() or when the camera is manipulated with the mouse.  */
	float currentFPS() { return f_p_s_; };
	/*! Returns \c true if the viewer is in fullScreen mode.

	Default value is \c false. Set by setFullScreen() or toggleFullScreen().

	Note that if the QGLViewer is embedded in an other QWidget, it returns \c true when the top level
	widget is in full screen mode. */
	bool isFullScreen() const { return fullScreen_; };
	/*! Returns \c true if the viewer displays in stereo.

	The QGLViewer object must be created with a stereo format to handle stereovision:
	\code
	QGLFormat format;
	format.setStereoDisplay( TRUE );
	QGLViewer viewer(format);
	\endcode
	The hardware needs to support stereo display. Try the <a
	href="../examples/stereoViewer.html">stereoViewer example</a> to check.

	Set by setStereoDisplay() or toggleStereoDisplay(). Default value is \c false.

	Stereo is performed using the Parallel axis asymmetric frustum perspective projection method.
	See Camera::loadProjectionMatrixStereo() and Camera::loadModelViewMatrixStereo().

	The stereo parameters are defined by the camera(). See qglviewer::Camera::setIODistance(),
	qglviewer::Camera::setPhysicalDistanceToScreen(),
	qglviewer::Camera::setPhysicalScreenWidth() and
	qglviewer::Camera::setFocusDistance(). */
	bool displaysInStereo() const { return stereo_; }
	/*! Returns the recommended size for the QGLViewer. Default value is 600x400 pixels. */
	virtual QSize sizeHint() const { return QSize(600, 400); }

	public slots:
		void setFullScreen(bool fullScreen=true);
		void setStereoDisplay(bool stereo=true);
		/*! Toggles the state of isFullScreen(). See also setFullScreen(). */
		void toggleFullScreen() { setFullScreen(!isFullScreen()); };
		/*! Toggles the state of displaysInStereo(). See setStereoDisplay(). */
		void toggleStereoDisplay() { setStereoDisplay(!stereo_); };
		void toggleCameraMode();

private:
	bool cameraIsInRevolveMode() const;
	//@}


	/*! @name Display methods */
	//@{
public:
	static void drawArrow(float length=1.0f, float radius=-1.0f, int nbSubdivisions=12);
	static void drawArrow(const qglviewer::Vec& from, const qglviewer::Vec& to, float radius=-1.0f, int nbSubdivisions=12);
	static void drawAxis(float length=1.0f);
	static void drawGrid(float size=1.0f, int nbSubdivisions=10);

	virtual void startScreenCoordinatesSystem(bool upward=false) const;
	virtual void stopScreenCoordinatesSystem() const;

	void drawText(int x, int y, const QString& text, const QFont& fnt=QFont());
	void displayMessage(const QString& message, int delay=2000);
	// void draw3DText(const qglviewer::Vec& pos, const qglviewer::Vec& normal, const QString& string, GLfloat height=0.1f);

protected:
	virtual void drawLight(GLenum light, float scale = 1.0f) const;

private:
	void displayFPS();
	/*! Vectorial rendering callback method. */
	void drawVectorial() { paintGL(); };

#ifndef DOXYGEN
	friend void drawVectorial(void* param);
#endif
	//@}


#ifdef DOXYGEN
	/*! @name Useful inherited methods */
	//@{
public:
	/*! Returns viewer's widget width (in pixels). See QGLWidget documentation. */
	int width() const;
	/*! Returns viewer's widget height (in pixels). See QGLWidget documentation. */
	int height() const;
	/*! Updates the display. Do not call draw() directly, use this method instead. See QGLWidget documentation. */
	virtual void updateGL();
	/*! Converts \p image into the unnamed format expected by OpenGL methods such as glTexImage2D().
	See QGLWidget documentation. */
	static QImage convertToGLFormat(const QImage & image);
	/*! Calls \c glColor3. See QGLWidget::qglColor(). */
	void qglColor(const QColor& color) const;
	/*! Calls \c glClearColor. See QGLWidget documentation. */
	void qglClearColor(const QColor& color) const;
	/*! Returns \c true if the widget has a valid GL rendering context. See QGLWidget
	documentation. */
	bool isValid() const;
	/*! Returns \c true if display list sharing with another QGLWidget was requested in the
	constructor. See QGLWidget documentation. */
	bool isSharing() const;
	/*! Makes this widget's rendering context the current OpenGL rendering context. Useful with
	several viewers. See QGLWidget documentation. */
	virtual void makeCurrent();
	/*! Returns \c true if mouseMoveEvent() is called even when no mouse button is pressed.

	You need to setMouseTracking() to \c true in order to use MouseGrabber (see mouseGrabber()). See
	details in the QWidget documentation. */
	bool hasMouseTracking () const;
	public slots:
		/*! Resizes the widget to size \p width by \p height pixels. See also width() and height(). */
		virtual void resize(int width, int height);
		/*! Sets the hasMouseTracking() value. */
		virtual void setMouseTracking(bool enable);
protected:
	/*! Returns \c true when buffers are automatically swapped (default). See details in the QGLWidget
	documentation. */
	bool autoBufferSwap() const;
	protected slots:
		/*! Sets the autoBufferSwap() value. */
		void setAutoBufferSwap(bool on);
		//@}
#endif


		/*! @name Snapshots */
		//@{
public:
#if QT_VERSION < 0x030000
	virtual QImage grabFrameBuffer(bool withAlpha=false);
#endif
	/*! Returns the snapshot file name used by saveSnapshot().

	This value is used in \p automatic mode (see saveSnapshot()). A dialog is otherwise popped-up to
	set it.

	You can also directly provide a file name using saveSnapshot(const QString&, bool).

	If the file name is relative, the current working directory at the moment of the method call is
	used. Set using setSnapshotFileName(). */
	const QString& snapshotFileName() const { return snapshotFileName_; };
#ifndef DOXYGEN
	const QString& snapshotFilename() const;
#endif
	/*! Returns the snapshot file format used by saveSnapshot().

	This value is used when saveSnapshot() is passed the \p automatic flag. It is defined using a
	saveAs pop-up dialog otherwise.

	The available formats are those handled by Qt. Classical values are \c "JPEG", \c "PNG",
	\c "PPM, \c "BMP". Use the following code to get the actual list:
	\code
	QList<QByteArray> formatList = QImageReader::supportedImageFormats();
	// or with Qt version 2 or 3:
	QStringList formatList = QImage::outputFormatList();
	\endcode

	If the library was compiled with the vectorial rendering option (default), three additional
	vectorial formats are available: \c "EPS", \c "PS" and \c "XFIG". \c "SVG" and \c "PDF" formats
	should soon be available. The <a href="http://artis.imag.fr/Software/VRender">VRender library</a>
	was created by Cyril Soler.

	Note that the VRender library has some limitations: vertex shader effects are not reproduced and
	\c PASS_THROUGH tokens are not handled so one can not change point and line size in the middle of
	a drawing.

	Default value is the first supported among "JPEG, PNG, EPS, PS, PPM, BMP", in that order.

	This value is set using setSnapshotFormat() or with openSnapshotFormatDialog().

	\attention No verification is performed on the provided format validity. The next call to
	saveSnapshot() may fail if the format string is not supported. */
	const QString& snapshotFormat() const { return snapshotFormat_; };
	/*! Returns the value of the counter used to name snapshots in saveSnapshot() when \p automatic is
	\c true.

	Set using setSnapshotCounter(). Default value is 0, and it is incremented after each \p automatic
	snapshot. See saveSnapshot() for details. */
	int snapshotCounter() const { return snapshotCounter_; };
	/*! Defines the image quality of the snapshots produced with saveSnapshot().

	Values must be in the range -1..100. Use 0 for lowest quality and 100 for highest quality (and
	larger files). -1 means use Qt default quality. Default value is 95.

	Set using setSnapshotQuality(). See also the QImage::save() documentation.

	\note This value has no impact on the images produced in vectorial format. */
	int snapshotQuality() { return snapshotQuality_; };

	// Qt 2.3 does not support double default value parameters in slots.
	// Remove "slots" from the following line to compile with Qt 2.3
	public slots:
		void saveSnapshot(bool automatic=true, bool overwrite=false);

		public slots:
			void saveSnapshot(const QString& fileName, bool overwrite=false);
			void setSnapshotFileName(const QString& name);

			/*! Sets the snapshotFormat(). */
			void setSnapshotFormat(const QString& format) { snapshotFormat_ = format; };
			/*! Sets the snapshotCounter(). */
			void setSnapshotCounter(int counter) { snapshotCounter_ = counter; };
			/*! Sets the snapshotQuality(). */
			void setSnapshotQuality(int quality) { snapshotQuality_ = quality; };
			bool openSnapshotFormatDialog();

private:
	bool saveImageSnapshot(const QString& fileName);
	//@}


	/*! @name Buffer to texture */
	//@{
public:
	GLuint bufferTextureId() const;
	/*! Returns the texture coordinate corresponding to the u extremum of the bufferTexture.

	The bufferTexture is created by copyBufferToTexture(). The texture size has powers of two
	dimensions and the buffer image hence only fills a part of it. This value corresponds to the u
	coordinate of the extremum right side of the buffer image.

	Use (0,0) to (bufferTextureMaxU(), bufferTextureMaxV()) texture coordinates to map the entire
	texture on a quad. */
	float bufferTextureMaxU() const { return bufferTextureMaxU_; };
	/*! Same as bufferTextureMaxU(), but for the v texture coordinate. */
	float bufferTextureMaxV() const { return bufferTextureMaxV_; };
	public slots:
		void copyBufferToTexture(GLint internalFormat, GLenum format=GL_NONE);
		//@}

		/*! @name Animation */
		//@{
public:
	/*! Return \c true when the animation loop is started.

	During animation, an infinite loop calls animate() and draw() and then waits for animationPeriod()
	milliseconds before calling animate() and draw() again. And again.

	Use startAnimation(), stopAnimation() or toggleAnimation() to change this value.

	See the <a href="../examples/animation.html">animation example</a> for illustration. */
	bool animationIsStarted() const { return animationStarted_; };
	/*! The animation loop period, in milliseconds.

	When animationIsStarted(), this is delay waited after draw() to call animate() and draw() again.
	Default value is 40 milliseconds (25 Hz).

	This value will define the currentFPS() when animationIsStarted() (provided that your animate()
	and draw() methods are fast enough).

	If you want to know the maximum possible frame rate of your machine on a given scene,
	setAnimationPeriod() to \c 0, and startAnimation() (keyboard shortcut is \c Enter). The display
	will then be updated as often as possible, and the frame rate will be meaningful.

	\note This value is taken into account only the next time you call startAnimation(). If
	animationIsStarted(), you should stopAnimation() first. */
	int animationPeriod() const { return animationPeriod_; };

	public slots:
		/*! Sets the animationPeriod(), in milliseconds. */
		void setAnimationPeriod(int period) { animationPeriod_ = period; };
		virtual void startAnimation();
		virtual void stopAnimation();
		/*! Scene animation method.

		When animationIsStarted(), this method is in charge of the scene update before each draw().
		Overload it to define how your scene evolves over time. The time should either be regularly
		incremented in this method (frame-rate independent animation) or computed from actual time (for
		instance using QTime::elapsed()) for real-time animations.

		Note that KeyFrameInterpolator (which regularly updates a Frame) do not use this method but rather
		rely on a QTimer signal-slot mechanism.

		See the <a href="../examples/animation.html">animation example</a> for an illustration. */
		virtual void animate() { emit animateNeeded(); };
		/*! Calls startAnimation() or stopAnimation(), depending on animationIsStarted(). */
		void toggleAnimation() { if (animationIsStarted()) stopAnimation(); else startAnimation(); };
		//@}

public:
signals:
	/*! Signal emitted by the default init() method.

	Connect this signal to the methods that need to be called to initialize your viewer or overload init(). */
	void viewerInitialized();

	/*! Signal emitted by the default draw() method.

	Connect this signal to your main drawing method or overload draw(). See the <a
	href="../examples/callback.html">callback example</a> for an illustration. */
	void drawNeeded();

	/*! Signal emitted at the end of the QGLViewer::paintGL() method, when frame is drawn.

	Can be used to notify an image grabbing process that the image is ready. A typical example is to
	connect this signal to the saveSnapshot() method, so that a (numbered) snapshot is generated after
	each new display, in order to create a movie:
	\code
	connect(viewer, SIGNAL(drawFinished(bool)), SLOT(saveSnapshot(bool)));
	\endcode

	The \p automatic bool variable is always \c true and has been added so that the signal can be
	connected to saveSnapshot() with an \c automatic value set to \c true. */
	void drawFinished(bool automatic);

	/*! Signal emitted by the default animate() method.

	Connect this signal to your scene animation method or overload animate(). */
	void animateNeeded();

	/*! Signal emitted by the default QGLViewer::help() method.

	Connect this signal to your own help method or overload help(). */
	void helpRequired();

	/*! This signal is emitted whenever axisIsDrawn() changes value. */
	void axisIsDrawnChanged(bool drawn);
	/*! This signal is emitted whenever gridIsDrawn() changes value. */
	void gridIsDrawnChanged(bool drawn);
	/*! This signal is emitted whenever FPSIsDisplayed() changes value. */
	void FPSIsDisplayedChanged(bool displayed);
	/*! This signal is emitted whenever textIsEnabled() changes value. */
	void textIsEnabledChanged(bool enabled);
	/*! This signal is emitted whenever cameraIsEdited() changes value.. */
	void cameraIsEditedChanged(bool edited);
	/*! This signal is emitted whenever displaysInStereo() changes value. */
	void stereoChanged(bool on);
	/*! Signal emitted by select().

	Connect this signal to your selection method or overload select(), or more probably simply
	drawWithNames(). */
	void pointSelected(const QMouseEvent* e);

	/*! Signal emitted by setMouseGrabber() when the mouseGrabber() is changed.

	\p mouseGrabber is a pointer to the new MouseGrabber. Note that this signal is emitted with a \c
	NULL parameter each time a MouseGrabber stops grabbing mouse. */
	void mouseGrabberChanged(qglviewer::MouseGrabber* mouseGrabber);

	/*! @name Help window */
	//@{
public:
	/*! Returns the QString displayed in the help() window main tab.

	Overload this method to define your own help string, which should shortly describe your
	application and explain how it works. Rich-text (HTML) tags can be used (see QStyleSheet()
	documentation for available tags):
	\code
	QString myViewer::helpString() const
	{
	QString text("<h2>M y V i e w e r</h2>");
	text += "Displays a <b>Scene</b> using OpenGL. Move the camera using the mouse.";
	return text;
	}
	\endcode

	See also mouseString() and keyboardString(). */
	virtual QString helpString() const { return tr("No help available."); };

	virtual QString mouseString() const;
	virtual QString keyboardString() const;

#ifndef DOXYGEN
	/*! This method is deprecated, use mouseString() instead. */
	virtual QString mouseBindingsString () const { return mouseString(); }
	/*! This method is deprecated, use keyboardString() instead. */
	virtual QString shortcutBindingsString () const { return keyboardString(); }
#endif

	public slots:
		virtual void help();
		virtual void aboutQGLViewer();

protected:
	/*! Returns a pointer to the help widget.

	Use this only if you want to directly modify the help widget. Otherwise use helpString(),
	setKeyDescription() and setMouseBindingDescription() to customize the text displayed in the help
	window tabs. */
	QTabWidget* helpWidget() { return helpWidget_; }
	//@}


	/*! @name Drawing methods */
	//@{
protected:
	virtual void resizeGL(int width, int height);
	virtual void initializeGL();

	/*! Initializes the viewer OpenGL context.

	This method is called before the first drawing and should be overloaded to initialize some of the
	OpenGL flags. The default implementation is empty. See initializeGL().

	Typical usage include camera() initialization (showEntireScene()), previous viewer state
	restoration (restoreStateFromFile()), OpenGL state modification and display list creation.

	Note that initializeGL() modifies the standard OpenGL context. These values can be restored back
	in this method.

	\attention You should not call updateGL() (or any method that calls it) in this method, as it will
	result in an infinite loop. The different QGLViewer set methods (setAxisIsDrawn(),
	setFPSIsDisplayed()...) are protected against this problem and can safely be called.

	\note All the OpenGL specific initializations must be done in this method: the OpenGL context is
	not yet available in your viewer constructor. */
  virtual void init() { emit viewerInitialized(); }

	virtual void paintGL();
	virtual void preDraw();
	virtual void preDrawStereo(bool leftBuffer=true);

	/*! The core method of the viewer, that draws the scene.

	If you build a class that inherits from QGLViewer, this is the method you want to overload. See
	the <a href="../examples/simpleViewer.html">simpleViewer example</a> for an illustration.

	The camera modelView matrix set in preDraw() converts from the world to the camera coordinate
	systems. Vertices given in draw() can then be considered as being given in the world coordinate
	system. The camera is moved in this world using the mouse. This representation is much more
	intuitive than the default camera-centric OpenGL standard.

	\attention The \c GL_PROJECTION matrix should not be modified by this method, to correctly display
	visual hints (axis, grid, FPS...) in postDraw(). Use push/pop or call
	camera()->loadProjectionMatrix() at the end of draw() if you need to change the projection matrix
	(unlikely). On the other hand, the \c GL_MODELVIEW matrix can be modified and left in a arbitrary
	state. */
  virtual void draw() {}
	virtual void fastDraw();
	virtual void postDraw();
	//@}

	/*! @name Mouse, keyboard and event handlers */
	//@{
protected:
	virtual void mousePressEvent(QMouseEvent *);
	virtual void mouseMoveEvent(QMouseEvent *);
	virtual void mouseReleaseEvent(QMouseEvent *);
	virtual void mouseDoubleClickEvent(QMouseEvent *);
	virtual void wheelEvent(QWheelEvent *);
	virtual void keyPressEvent(QKeyEvent *);
	virtual void timerEvent(QTimerEvent *);
	virtual void closeEvent(QCloseEvent *);
	//@}

	/*! @name Object selection */
	//@{
public:
	/*! Returns the name (an integer value) of the entity that was last selected by select(). This
	value is set by endSelection(). See the select() documentation for details.

	As a convention, this method returns -1 if the selectBuffer() was empty, meaning that no object
	was selected.

	Return value is -1 before the first call to select(). This value is modified using setSelectedName(). */
  int selectedName() const { return selectedObjectId_; }
	/*! Returns the selectBuffer() size.

	See the select() documentation for details. Use setSelectBufferSize() to change this value.

	Default value is 4000 (i.e. 1000 objects in selection region, since each object pushes 4 values).
	This size should be over estimated to prevent a buffer overflow when many objects are drawn under
	the mouse cursor. */
  int selectBufferSize() const { return selectBufferSize_; }

	/*! Returns the width (in pixels) of a selection frustum, centered on the mouse cursor, that is
	used to select objects.

	The height of the selection frustum is defined by selectRegionHeight().

	The objects that will be drawn in this region by drawWithNames() will be recorded in the
	selectBuffer(). endSelection() then analyzes this buffer and setSelectedName() to the name of the
	closest object. See the gluPickMatrix() documentation for details.

	The default value is 3, which is adapted to standard applications. A smaller value results in a
	more precise selection but the user has to be careful for small feature selection.

	See the <a href="../examples/multiSelect.html">multiSelect example</a> for an illustration. */
  int selectRegionWidth() const { return selectRegionWidth_; }
	/*! See the selectRegionWidth() documentation. Default value is 3 pixels. */
  int selectRegionHeight() const { return selectRegionHeight_; }

	/*! Returns a pointer to an array of \c GLuint.

	This buffer is used by the \c GL_SELECT mode in select() to perform object selection. The buffer
	size can be modified using setSelectBufferSize(). If you overload endSelection(), you will analyze
	the content of this buffer. See the \c glSelectBuffer() man page for details. */
  GLuint* selectBuffer() { return selectBuffer_; }

	public slots:
		virtual void select(const QMouseEvent* event);
		virtual void select(const QPoint& point);

		void setSelectBufferSize(int size);
		/*! Sets the selectRegionWidth(). */
    void setSelectRegionWidth(int width) { selectRegionWidth_ = width; }
		/*! Sets the selectRegionHeight(). */
    void setSelectRegionHeight(int height) { selectRegionHeight_ = height; }
		/*! Set the selectedName() value.

		Used in endSelection() during a selection. You should only call this method if you overload the
		endSelection() method. */
    void setSelectedName(int id) { selectedObjectId_=id; }

protected:
	virtual void beginSelection(const QPoint& point);
	/*! This method is called by select() and should draw selectable entities.

	Default implementation is empty. Overload and draw the different elements of your scene you want
	to be able to select. The default select() implementation relies on the \c GL_SELECT, and requires
	that each selectable element is drawn within a \c glPushName() - \c glPopName() block. A typical
	usage would be (see the <a href="../examples/select.html">select example</a>):
	\code
	void Viewer::drawWithNames()
	{
	for (int i=0; i<nbObjects; ++i)
	{
	glPushName(i);
	object(i)->draw();
	glPopName();
	}
	}
	\endcode

	The resulting selected name is computed by endSelection(), which setSelectedName() to the integer
	id pushed by this method (a value of -1 means no selection). Use selectedName() to update your
	selection, probably in the postSelection() method.

	\attention If your selected objects are points, do not use \c glBegin(GL_POINTS); and \c glVertex3fv()
	in the above \c draw() method (not compatible with raster mode): use \c glRasterPos3fv() instead. */
  virtual void drawWithNames() {}
	virtual void endSelection(const QPoint& point);
	/*! This method is called at the end of the select() procedure. It should finalize the selection
	process and update the data structure/interface/computation/display... according to the newly
	selected entity.

	The default implementation is empty. Overload this method if needed, and use selectedName() to
	retrieve the selected entity name (returns -1 if no object was selected). See the <a
	href="../examples/select.html">select example</a> for an illustration. */
  virtual void postSelection(const QPoint& point) { Q_UNUSED(point); }
	//@}


	/*! @name Keyboard customization */
	//@{
protected:
	/*! Defines the different actions that can be associated with a keyboard shortcut using
	setShortcut().

	See the <a href="../keyboard.html">keyboard page</a> for details. */
	enum KeyboardAction { DRAW_AXIS, DRAW_GRID, DISPLAY_FPS, ENABLE_TEXT, EXIT_VIEWER,
		SAVE_SCREENSHOT, CAMERA_MODE, FULL_SCREEN, STEREO, ANIMATION, HELP, EDIT_CAMERA,
		MOVE_CAMERA_LEFT, MOVE_CAMERA_RIGHT, MOVE_CAMERA_UP, MOVE_CAMERA_DOWN,
		INCREASE_FLYSPEED, DECREASE_FLYSPEED };
public:
	int shortcut(KeyboardAction action) const;
#ifndef DOXYGEN
	// QGLViewer 1.x
	int keyboardAccelerator(KeyboardAction action) const;
	Qt::Key keyFrameKey(int index) const;
	QtKeyboardModifiers playKeyFramePathStateKey() const;
	// QGLViewer 2.0 without Qt4 support
	QtKeyboardModifiers addKeyFrameStateKey() const;
	QtKeyboardModifiers playPathStateKey() const;
#endif
	Qt::Key pathKey(int index) const;
	QtKeyboardModifiers addKeyFrameKeyboardModifiers() const;
	QtKeyboardModifiers playPathKeyboardModifiers() const;

	public slots:
		void setShortcut(KeyboardAction action, int key);
#ifndef DOXYGEN
		void setKeyboardAccelerator(KeyboardAction action, int key);
#endif
		void setKeyDescription(int key, QString description);

		// Key Frames shortcut keys
#ifndef DOXYGEN
		// QGLViewer 1.x compatibility methods
		virtual void setKeyFrameKey(int index, int key);
		virtual void setPlayKeyFramePathStateKey(int buttonState);
		// QGLViewer 2.0 without Qt4 support
		virtual void setPlayPathStateKey(int buttonState);
		virtual void setAddKeyFrameStateKey(int buttonState);
#endif
		virtual void setPathKey(int key, int index = 0);
		virtual void setPlayPathKeyboardModifiers(QtKeyboardModifiers modifiers);
		virtual void setAddKeyFrameKeyboardModifiers(QtKeyboardModifiers modifiers);
		//@}


		/*! @name Mouse customization */
		//@{
protected:
	/*! Defines the different mouse handlers: camera() or manipulatedFrame().

	Used by setMouseBinding(), setMouseBinding(int, ClickAction, bool, int) and setWheelBinding() to
	define which handler receives the mouse events. */
	enum MouseHandler { CAMERA, FRAME };

	/*! Defines the possible actions that can be binded to a mouse click using
	setMouseBinding(int,ClickAction,bool,int).

	See the <a href="../mouse.html">mouse page</a> for details. */
	enum ClickAction { NO_CLICK_ACTION, ZOOM_ON_PIXEL, ZOOM_TO_FIT, SELECT, RAP_FROM_PIXEL, RAP_IS_CENTER,
		CENTER_FRAME, CENTER_SCENE, SHOW_ENTIRE_SCENE, ALIGN_FRAME, ALIGN_CAMERA };

#ifndef DOXYGEN
	// So that it can be used in ManipulatedFrame and ManipulatedCameraFrame.
public:
#endif

	/*! Defines the possible actions that can be binded to a mouse motion (a click, followed by a
	mouse displacement).

	These actions may be binded to the camera() or to the manipulatedFrame() (see QGLViewer::MouseHandler) using
	setMouseBinding(). */
	enum MouseAction { NO_MOUSE_ACTION,
		ROTATE, ZOOM, TRANSLATE,
		MOVE_FORWARD, LOOK_AROUND, MOVE_BACKWARD,
		SCREEN_ROTATE, ROLL, DRIVE,
		SCREEN_TRANSLATE, ZOOM_ON_REGION };

#ifdef DOXYGEN
public:
#endif

	MouseAction mouseAction(int state) const;
	int mouseHandler(int state) const;
	int mouseButtonState(MouseHandler handler, MouseAction action, bool withConstraint=true) const;
	ClickAction clickAction(int state, bool doubleClick, QtMouseButtons buttonsBefore) const;
	void getClickButtonState(ClickAction action, int& state, bool& doubleClick, QtMouseButtons& buttonsBefore) const;

	MouseAction wheelAction(QtKeyboardModifiers modifiers) const;
	int wheelHandler(QtKeyboardModifiers modifiers) const;
	int wheelButtonState(MouseHandler handler, MouseAction action, bool withConstraint=true) const;

	public slots:
		void setMouseBinding(int state, MouseHandler handler, MouseAction action, bool withConstraint=true);
#if QT_VERSION < 0x030000
		// Two slots cannot have the same name or two default parameters with Qt 2.3.
public:
#endif
	void setMouseBinding(int state, ClickAction action, bool doubleClick=false, QtMouseButtons buttonsBefore=Qt::NoButton);
	void setMouseBindingDescription(int state, QString description, bool doubleClick=false, QtMouseButtons buttonsBefore=Qt::NoButton);
#if QT_VERSION < 0x030000
	public slots:
#endif
		void setWheelBinding(QtKeyboardModifiers modifiers, MouseHandler handler, MouseAction action, bool withConstraint=true);
		void setHandlerKeyboardModifiers(MouseHandler handler, QtKeyboardModifiers modifiers);
#ifndef DOXYGEN
		void setHandlerStateKey(MouseHandler handler, int buttonState);
		void setMouseStateKey(MouseHandler handler, int buttonState);
#endif

private:
	static QString mouseActionString(QGLViewer::MouseAction ma);
	static QString clickActionString(QGLViewer::ClickAction ca);
	//@}


	/*! @name State persistence */
	//@{
public:
	QString stateFileName() const;
	virtual QDomElement domElement(const QString& name, QDomDocument& document) const;

	public slots:
		virtual void initFromDOMElement(const QDomElement& element);
		virtual void saveStateToFile(); // cannot be const because of QMessageBox
		virtual bool restoreStateFromFile();

		/*! Defines the stateFileName() used by saveStateToFile() and restoreStateFromFile().

		The file name can have an optional prefix directory (no prefix meaning current directory). If the
		directory does not exist, it will be created by saveStateToFile().

		\code
		// Name depends on the displayed 3D model. Saved in current directory.
		setStateFileName(3DModelName() + ".xml");

		// Files are stored in a dedicated directory under user's home directory.
		setStateFileName(QDir::homeDirPath + "/.config/myApp.xml");
		\endcode */
		void setStateFileName(const QString& name) { stateFileName_ = name; };

#ifndef DOXYGEN
		void saveToFile(const QString& fileName=QString::null);
		bool restoreFromFile(const QString& fileName=QString::null);
#endif

private:
	static void saveStateToFileForAllViewers();
	//@}


	/*! @name QGLViewer pool */
	//@{
public:
	/*! Returns a \c QList (see Qt documentation) that contains pointers to all the created
	QGLViewers. Note that this list may contain \c NULL pointers if the associated viewer has been deleted.

	Can be useful to apply a method or to connect a signal to all the viewers.

	\attention With Qt version 3, this method returns a \c QPtrList instead. Use a \c QPtrListIterator
	to iterate on the list:
	\code
	QPtrListIterator<QGLViewer> it(QGLViewer::QGLViewerPool());
	for (QGLViewer* viewer; (viewer = it.current()) != NULL; ++it)
	connect(myObject, SIGNAL(mySignal), viewer, SLOT(updateGL()));
	\endcode */
#if QT_VERSION >= 0x040000
	static const QList<QGLViewer*>& QGLViewerPool() { return QGLViewer::QGLViewerPool_; };
#else
	static const QPtrList<QGLViewer>& QGLViewerPool() { return QGLViewer::QGLViewerPool_; };
#endif


	/*! Returns the index of the QGLViewer \p viewer in the QGLViewerPool(). This index in unique and
	can be used to identify the different created QGLViewers (see stateFileName() for an application
	example).

	When a QGLViewer is deleted, the following QGLViewers' indexes are shifted down. Returns -1 if the
	QGLViewer could not be found (which should not be possible). */
#if QT_VERSION >= 0x040000
	static int QGLViewerIndex(const QGLViewer* const viewer) { return QGLViewer::QGLViewerPool_.indexOf(const_cast<QGLViewer*>(viewer)); };
#else
	static int QGLViewerIndex(const QGLViewer* const viewer) { return QGLViewer::QGLViewerPool_.find(viewer); };
#endif
	//@}

#ifndef DOXYGEN
	/*! @name Visual hints */
	//@{
public:
	virtual void setVisualHintsMask(int mask, int delay = 2000);
	virtual void drawVisualHints();

	public slots:
		virtual void resetVisualHints();
		//@}
#endif

		private slots:
			// Patch for a Qt bug with fullScreen on startup
			void delayedFullScreen() { move(prevPos_); setFullScreen(); };
			void hideMessage();

private:
	// Copy constructor and operator= are declared private and undefined
	// Prevents everyone from trying to use them
	QGLViewer(const QGLViewer& v);
	QGLViewer& operator=(const QGLViewer& v);

	// Set parameters to their default values. Called by the constructors.
	void defaultConstructor();

	void handleKeyboardAction(KeyboardAction id);

	// C a m e r a
	qglviewer::Camera* camera_;
	bool cameraIsEdited_;
	float previousCameraZClippingCoefficient_;
	int previousPathId_; // Double key press recognition
	void connectAllCameraKFIInterpolatedSignals(bool connection=true);

	// C o l o r s
	QColor backgroundColor_, foregroundColor_;

	// D i s p l a y    f l a g s
	bool axisIsDrawn_;	// world axis
	bool gridIsDrawn_;	// world XY grid
	bool FPSIsDisplayed_;	// Frame Per Seconds
	bool textIsEnabled_;	// drawText() actually draws text or not
	bool stereo_;		// stereo display
	bool fullScreen_;	// full screen mode
	QPoint prevPos_;	// Previous window position, used for full screen mode

	// A n i m a t i o n
	bool animationStarted_; // animation mode started
	int animationPeriod_;   // period in msecs
	int animationTimerId_;

	// F P S    d i s p l a y
	QTime fpsTime_;
	unsigned int fpsCounter_;
	QString fpsString_;
	float f_p_s_;

	// M e s s a g e s
	QString message_;
	bool displayMessage_;
	QTimer messageTimer_;

	// M a n i p u l a t e d    f r a m e
	qglviewer::ManipulatedFrame* manipulatedFrame_;
	bool manipulatedFrameIsACamera_;

	// M o u s e   G r a b b e r
	qglviewer::MouseGrabber* mouseGrabber_;
	bool mouseGrabberIsAManipulatedFrame_;
	bool mouseGrabberIsAManipulatedCameraFrame_;
	QMap<size_t, bool> disabledMouseGrabbers_;

	// S e l e c t i o n
	int selectRegionWidth_, selectRegionHeight_;
	int selectBufferSize_;
	GLuint* selectBuffer_;
	int selectedObjectId_;

	// V i s u a l   h i n t s
	int visualHint_;

	// S h o r t c u t   k e y s
	void setDefaultShortcuts();
	QString cameraPathKeysString() const;
	QMap<KeyboardAction, QString> keyboardActionDescription_;
	QMap<KeyboardAction, int> keyboardBinding_;
	QMap<int, QString> keyDescription_;

	// K e y   F r a m e s   s h o r t c u t s
	QMap<Qt::Key, int> pathIndex_;
	QtKeyboardModifiers addKeyFrameKeyboardModifiers_, playPathKeyboardModifiers_;

	// B u f f e r   T e x t u r e
	GLuint bufferTextureId_;
	float bufferTextureMaxU_, bufferTextureMaxV_;
	int bufferTextureWidth_, bufferTextureHeight_;
	unsigned int previousBufferTextureFormat_;
	int previousBufferTextureInternalFormat_;

#ifndef DOXYGEN
	// M o u s e   a c t i o n s
	struct MouseActionPrivate {
		MouseHandler handler;
		MouseAction action;
		bool withConstraint;
	};

	// C l i c k   a c t i o n s
	struct ClickActionPrivate {
		QtKeyboardModifiers modifiers;
		QtMouseButtons button;
		bool doubleClick;
		QtMouseButtons buttonsBefore; // only defined when doubleClick is true

		// This sort order in used in mouseString() to displays sorted mouse bindings
		bool operator<(const ClickActionPrivate& cap) const
		{
			if (buttonsBefore != cap.buttonsBefore)
				return buttonsBefore < cap.buttonsBefore;
			else
				if (modifiers != cap.modifiers)
					return modifiers < cap.modifiers;
				else
					if (button != cap.button)
						return button < cap.button;
					else
						return !doubleClick && cap.doubleClick;
		}
	};
#endif
    static QString formatClickActionPrivate(ClickActionPrivate cap);

	QMap<ClickActionPrivate, QString> mouseDescription_;

	void setDefaultMouseBindings();
	void performClickAction(ClickAction ca, const QMouseEvent* const e);
	QMap<int, MouseActionPrivate> mouseBinding_;
	QMap<QtKeyboardModifiers, MouseActionPrivate> wheelBinding_;
	QMap<ClickActionPrivate, ClickAction> clickBinding_;

	// S n a p s h o t s
	void initializeSnapshotFormats();
	QString snapshotFileName_, snapshotFormat_;
	int snapshotCounter_, snapshotQuality_;

	// Q G L V i e w e r   p o o l
#if QT_VERSION >= 0x040000
	static QList<QGLViewer*> QGLViewerPool_;
#else
	static QPtrList<QGLViewer> QGLViewerPool_;
#endif

	// S t a t e   F i l e
	QString stateFileName_;

	// H e l p   w i n d o w
	QTabWidget* helpWidget_;

	// I n t e r n a l   d e b u g
	bool updateGLOK_;
};

#endif // QGLVIEWER_QGLVIEWER_H
