#!/usr/bin/env python2

# vim: sw=4:ts=4:sts=4:expandtab

import sys, re, traceback
from PyQt4 import QtCore, QtGui, QtOpenGL
from OpenGL import GL
import OpenGL.GL.shaders

### global TODO: handle input (python code in shader comment, eval it),
###              advanced GUI generation (from comments)

class GLWidget(QtOpenGL.QGLWidget):
    ### TODO: aspect handling
    vertexShaderData = "varying vec4 p;\n"\
                       "\n"\
                       "void main()\n"\
                       "{\n"\
                       "    gl_Position = p = gl_Vertex;\n"\
                       "}\n"

    def __init__(self, parent=None):
        self.parent = parent
        QtOpenGL.QGLWidget.__init__(self, parent)

    def initializeGL(self):
        self.vertexShader = GL.shaders.compileShader(self.vertexShaderData, GL.GL_VERTEX_SHADER)

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)

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

    def setUniform(self, name, value):
        if isinstance(value, float):
            GL.glUniform1f(GL.glGetUniformLocation(self.program, name), value)

    def tick(self):
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

        timer = QtCore.QTimer(self)
        timer.setInterval(20)
        timer.timeout.connect(self.tick)
        timer.start()
        self.time = QtCore.QTime()
        self.time.start()

    def updateUniforms(self, data):
        r = re.compile(r'uniform\s+(\w+)\s+(\w+)(?:\s+=\s+([^;]+))?')
        for type_, name, value in r.findall(data):
            assert(type_ == 'float') ### TODO: hadle uniform type
            if name in self.uniforms:
                self.glWidget.setUniform(name, float(self.uniforms[name]))
            else:
                self.uniforms[name] = value
                if name != 'time':
                    self.docklayout.addWidget(QtGui.QLabel(name))
                    edit = QtGui.QLineEdit(value)
                    def l(text):
                        try:
                            v = float(text)
                            self.uniforms[name] = v
                            self.glWidget.setUniform(name, v)
                        except ValueError:
                            pass
                    edit.textChanged.connect(l)
                    self.docklayout.addWidget(edit)
        self.docklayout.addStretch(1)

    def load(self):
        filename = QtGui.QFileDialog.getOpenFileName(self)
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
        if 'time' in self.uniforms:
            self.glWidget.setUniform('time', float(self.time.elapsed()))
        self.glWidget.tick()

app = QtGui.QApplication(sys.argv)
win = MainWindow()
win.show()
if len(QtGui.QApplication.arguments()) > 1:
    win.loadFile(QtGui.QApplication.arguments()[1])
sys.exit(app.exec_())
