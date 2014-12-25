#!/usr/bin/env python

# vim: sw=4 ts=4 sts=4 et:

import sys, re, traceback, signal, time, collections, atexit, os
from PySide import QtCore, QtGui, QtOpenGL
from OpenGL import GL
import OpenGL.GL.shaders
from preprocessor import preprocess
from updater import Updater

### global TODO: handle input (python code in shader comment, eval it),
###              advanced GUI generation (from comments)

class PlainUniform:
    def __init__(self, value=0.):
        self.value = value

    def update(self): # TODO: update(self, deps)
        pass

class TimeUniform:
        def __init__(self):
            self._start = QtCore.QTime()
            self._start.start()
            self.value = 0.

        def update(self):
            self.value = float(self._start.elapsed())

class SmoothControlUniform:
    def __init__(self, value=0., speed=0.):
        self.value = value
        self._speed = speed
        self.speed = speed

    def update(self):
        self._speed = (15*self._speed + self.speed)/16
        self.value += self._speed/5

class MapUniform:
    def __init__(self, uni, f):
        self.uni = uni
        self.f = f
        self.value = self.f(self.uni.value)

    def update(self):
        self.uni.update()
        self.value = self.f(self.uni.value)

class GLWidget(QtOpenGL.QGLWidget):
    vertexShaderData = """
        #version 120

        varying vec4 p;

        uniform float _aspect;
        uniform float _x = 0.;
        uniform float _y = 0.;
        uniform float _z = 1.;

        void main() {
            gl_Position = p = gl_Vertex;
            p.x *= _aspect;
            p /= _z;
            p.x += _x;
            p.y += _y;
        }
    """

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.parent = parent
        self.program = None
        self.times = collections.deque(maxlen=10)
        self.uniforms = {'time': TimeUniform(),
                         '_x': SmoothControlUniform(),
                         '_y': SmoothControlUniform(),
                         '_z': MapUniform(SmoothControlUniform(), lambda x:1.1**x)
                        }

    def getFps(self):
        if len(self.times) > 1:
            return len(self.times) / (self.times[-1] - self.times[0])
        else:
            return 0

    def initializeGL(self):
        self.vertexShader = GL.shaders.compileShader(self.vertexShaderData, GL.GL_VERTEX_SHADER)

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        self.setUniform("_aspect", float(width) / height)

    def paintGL(self):
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        GL.glVertex3f(-1., -1., 0.)
        GL.glVertex3f(1., -1., 0.)
        GL.glVertex3f(-1., 1., 0.)
        GL.glVertex3f(1., 1., 0.)
        GL.glEnd()

    def setUniform(self, name, value):
        if isinstance(value, float) and self.program is not None:
            GL.glUniform1f(GL.glGetUniformLocation(self.program, name), value)

    def setUniforms(self):
        for name, uni in self.uniforms.items():
            self.setUniform(name, uni.value)

    def tick(self):
        for name, uni in self.uniforms.items():
            uni.update()
            self.setUniform(name, uni.value)
        self.updateGL()
        self.times.append(time.time())

    def setFragmentShader(self, shader):
        try:
            fragmentShader = GL.shaders.compileShader(shader, GL.GL_FRAGMENT_SHADER)
            self.program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
            GL.glUseProgram(self.program)
            self.setUniform("_aspect", float(self.width()) / self.height())
            self.setUniforms()
        except Exception as e:
            self.program = None
            raise e

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle('PyGL')
        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.dock = QtGui.QDockWidget()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)
        widget = QtGui.QWidget()
        self.docklayout = QtGui.QVBoxLayout()
        loadButton = QtGui.QPushButton("Load")
        loadButton.clicked.connect(self.load)
        self.docklayout.addWidget(loadButton)
        widget.setLayout(self.docklayout)
        self.dock.setWidget(widget)
        self.docklayout.addStretch(0)

        self.uniforms = {}
        self.uniformWidgets = {}
        self.filename = None
        self.updater = None

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.time = QtCore.QTime()
        self.uniforms['time'] = 0.
        self.uniformWidgets['time'] = []
        self.time.start()
        self.timeron = True # FIXME

    def updateUniforms(self, data):
        r = re.compile(r'uniform\s+(\w+)\s+(\w+)(?:\s+=\s+([^;]+))?')
        for name, widgets in self.uniformWidgets.items():
            for widget in widgets:
                widget.hide()
        uniforms = r.findall(data)
        for type_, name, value in uniforms:
            assert(type_ == 'float') ### TODO: hadle uniform type
            if name in self.uniforms:
                self.glWidget.setUniform(name, float(self.uniforms[name]))
                for widget in self.uniformWidgets[name]:
                        widget.show()
            else:
                self.uniforms[name] = value
                if name != 'time':
                    label = QtGui.QLabel(name)
                    edit = QtGui.QLineEdit(value)
                    self.uniformWidgets[name] = [label, edit]
                    def l(text, n=name):
                        try:
                            v = float(text)
                            self.uniforms[n] = v
                            self.glWidget.setUniform(n, v)
                        except ValueError:
                            pass
                    edit.textChanged.connect(l)
                    self.docklayout.addWidget(label)
                    self.docklayout.addWidget(edit)
        #self.docklayout.addStretch(1)

    def load(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, filter="Fragment shader (*.f)")
        if filename[0] != '':
            self.loadFile(filename[0])

    def reload(self):
        if self.filename:
            self.loadFile(self.filename)

    def loadFile(self, filename):
        self.filename = filename
        try:
            data, fnames = preprocess(filename)
            self.updater = Updater(fnames)
            self.glWidget.setFragmentShader(data)
            self.updateUniforms(data)
        except:
            e = sys.exc_info()[1]
            text = str(e)

            if type(e) == RuntimeError and len(e.args) == 3 and \
                e.args[2] == GL.GL_FRAGMENT_SHADER:
                text = e.args[0]

            mb = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Error loading shader",
                                   text, QtGui.QMessageBox.Ok)
            mb.exec_()

    def tick(self):
        if self.updater and self.updater.check():
            self.reload()
        if self.timeron:
            self.uniforms['time'] += float(self.time.elapsed())
            self.glWidget.setUniform('time', self.uniforms['time'])
        self.time.start()
        self.glWidget.tick()
        self.setWindowTitle(str(self.glWidget.getFps()))

    def toggleDock(self):
        if self.dock.isVisible():
            self.dock.hide()
        else:
            self.dock.show()

    def keyPressEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_W:
                self.glWidget.uniforms['_y'].speed += 1.
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.uniforms['_y'].speed -= 1.
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.uniforms['_x'].speed -= 1.
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.uniforms['_x'].speed += 1.
            if e.key() == QtCore.Qt.Key_Period:
                self.glWidget.uniforms['_z'].uni.speed += 1.
            if e.key() == QtCore.Qt.Key_Comma:
                self.glWidget.uniforms['_z'].uni.speed -= 1.
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        if e.key() == QtCore.Qt.Key_P:
            self.timeron = not self.timeron
        if e.key() == QtCore.Qt.Key_F:
            self.toggleDock()
        if e.key() == QtCore.Qt.Key_C:
            self.glWidget.origin()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_W:
                self.glWidget.uniforms['_y'].speed -= 1.
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.uniforms['_y'].speed += 1.
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.uniforms['_x'].speed += 1.
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.uniforms['_x'].speed -= 1.
            if e.key() == QtCore.Qt.Key_Period:
                self.glWidget.uniforms['_z'].uni.speed -= 1.
            if e.key() == QtCore.Qt.Key_Comma:
                self.glWidget.uniforms['_z'].uni.speed += 1.

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    args = QtGui.QApplication.arguments()
    if len(args) > 1:
        win.loadFile(args[1])
    sys.exit(app.exec_())

main()
