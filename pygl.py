#!/usr/bin/env python2

# vim: sw=4:ts=4:sts=4:expandtab

import sys, re, traceback
from PyQt4 import QtCore, QtGui, QtOpenGL
from OpenGL import GL
import OpenGL.GL.shaders

### global TODO: handle input (python code in shader comment, eval it),
###              advanced GUI generation (from comments)

class GLWidget(QtOpenGL.QGLWidget):
    vertexShaderData = "#version 120\n"\
                       "\n"\
                       "varying vec4 p;\n"\
                       "\n"\
                       "uniform float _aspect;\n"\
                       "uniform float _x = 0.;\n"\
                       "uniform float _y = 0.;\n"\
                       "uniform float _z = 1.;\n"\
                       "\n"\
                       "void main()\n"\
                       "{\n"\
                       "    gl_Position = p = gl_Vertex;\n"\
                       "    p.x *= _aspect;\n"\
                       "    p /= _z;\n"\
                       "    p.x += _x;\n"\
                       "    p.y += _y;\n"\
                       "}\n"

    def __init__(self, parent=None):
        self.parent = parent
        QtOpenGL.QGLWidget.__init__(self, parent)
        self.program = None
        self.targetSpeed = [0., 0.]
        self.speed = [0., 0.]
        self.x = 0.
        self.y = 0.
        self.z = 1.

    def initializeGL(self):
        self.vertexShader = GL.shaders.compileShader(self.vertexShaderData, GL.GL_VERTEX_SHADER)

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        if(self.program):
            GL.glUniform1f(GL.glGetUniformLocation(self.program, "_aspect"), float(width) / height)

    def paintGL(self):
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        GL.glVertex3f(-1., -1., 0.)
        GL.glVertex3f(1., -1., 0.)
        GL.glVertex3f(-1., 1., 0.)
        GL.glVertex3f(1., 1., 0.)
        GL.glEnd()

    def setFragmentShader(self, shader):
        fragmentShader = GL.shaders.compileShader(shader, GL.GL_FRAGMENT_SHADER)
        self.program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(self.program)
        GL.glUniform1f(GL.glGetUniformLocation(self.program, "_aspect"), float(self.width()) / self.height())

    def setUniform(self, name, value):
        if isinstance(value, float):
            GL.glUniform1f(GL.glGetUniformLocation(self.program, name), value)

    def move(self, x, y):
        self.x += float(x) / 10 / self.z
        self.y += float(y) / 10 / self.z
        GL.glUniform1f(GL.glGetUniformLocation(self.program, "_x"), self.x)
        GL.glUniform1f(GL.glGetUniformLocation(self.program, "_y"), self.y)

    def addSpeed(self, x, y):
        self.targetSpeed[0] += float(x)
        self.targetSpeed[1] += float(y)

    def zoom(self, zoom):
        self.z *= 1.1 ** float(zoom)
        GL.glUniform1f(GL.glGetUniformLocation(self.program, "_z"), self.z)

    def tick(self):
        self.speed[0] = (self.speed[0]*15 + self.targetSpeed[0])/16
        self.speed[1] = (self.speed[1]*15 + self.targetSpeed[1])/16
        self.move(self.speed[0]/5, self.speed[1]/5)
        self.updateGL()


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
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

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.time = QtCore.QTime()
        self.old = 0
        self.time.start()
        self.timeron = True # FIXME

    def updateUniforms(self, data):
        r = re.compile(r'uniform\s+(\w+)\s+(\w+)(?:\s+=\s+([^;]+))?')
        for type_, name, value in r.findall(data):
            assert(type_ == 'float') ### TODO: hadle uniform type
            if name in self.uniforms and name != 'time':
                self.glWidget.setUniform(name, float(self.uniforms[name]))
            else:
                self.uniforms[name] = value
                if name != 'time':
                    self.docklayout.addWidget(QtGui.QLabel(name))
                    edit = QtGui.QLineEdit(value)
                    def l(text, n=name):
                        try:
                            v = float(text)
                            self.uniforms[n] = v
                            self.glWidget.setUniform(n, v)
                        except ValueError:
                            pass
                    edit.textChanged.connect(l)
                    self.docklayout.addWidget(edit)
        self.docklayout.addStretch(1)

    def load(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, filter="Fragment shader (*.f)")
        if not filename.isNull():
            self.loadFile(filename)

    def loadFile(self, filename):
        try:
            with open(filename) as f:
                data = f.read()
            self.glWidget.setFragmentShader(data)
            self.updateUniforms(data)
        except:
            err = str(sys.exc_info()[1])
            mb = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Error loading shader",
                                   err[:50] + "...", QtGui.QMessageBox.Ok)
            mb.setDetailedText(err)
            mb.exec_()

    def tick(self):
        if self.timeron and 'time' in self.uniforms:
            self.old = self.old + float(self.time.elapsed())
            self.glWidget.setUniform('time', self.old)
        self.time.start()
        self.glWidget.tick()

    def keyPressEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_W:
                self.glWidget.addSpeed(0, +1)
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.addSpeed(0, -1)
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.addSpeed(-1, 0)
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.addSpeed(+1, 0)
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        if e.key() == QtCore.Qt.Key_Period:
            self.glWidget.zoom(1)
        if e.key() == QtCore.Qt.Key_Comma:
            self.glWidget.zoom(-1)
        if e.key() == QtCore.Qt.Key_P:
            self.timeron = not self.timeron

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_W:
                self.glWidget.addSpeed(0, -1)
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.addSpeed(0, +1)
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.addSpeed(+1, 0)
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.addSpeed(-1, 0)

app = QtGui.QApplication(sys.argv)
win = MainWindow()
win.show()
if len(QtGui.QApplication.arguments()) > 1:
    win.loadFile(QtGui.QApplication.arguments()[1])
sys.exit(app.exec_())
