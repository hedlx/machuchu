#!/usr/bin/env python2

import sys, re
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
        timer = QtCore.QTimer(self)
        timer.setInterval(20)
        timer.timeout.connect(self.tick)
        timer.start()

    def initializeGL(self):
        self.vertexShader = GL.shaders.compileShader(self.vertexShaderData, GL.GL_VERTEX_SHADER)

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)

    def paintGL(self):
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        GL.glVertex3f(-1., -1., 0.)
        GL.glVertex3f(1., -1., 0.);
        GL.glVertex3f(-1., 1., 0.);
        GL.glVertex3f(1., 1., 0.);
        GL.glEnd()

    def setFragmentShader(self, shader):
        fragmentShader = GL.shaders.compileShader(shader, GL.GL_FRAGMENT_SHADER)
        self.program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(self.program)

    def setUniform(self, name, value):
        try:
            GL.glUniform1f(GL.glGetUniformLocation(self.program, name), float(value))
        except ValueError:
            pass

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
        self.makeDock(None)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)

    def makeDock(self, data):
        widget = QtGui.QWidget()
        layout = QtGui.QVBoxLayout()
        loadButton = QtGui.QPushButton("Load")
        loadButton.clicked.connect(self.load)
        layout.addWidget(loadButton)
        if(data):
            ### TODO: hadle uniform type
            r = re.compile(r'uniform\s+\w+\s+(\w+)(?:\s+=\s+([^;]+))?')
            for match in r.findall(data):
                layout.addWidget(QtGui.QLabel(match[0]))
                edit = QtGui.QLineEdit(match[1])
                edit.textChanged.connect(lambda text: self.glWidget.setUniform(match[0], text))
                layout.addWidget(edit)
        layout.addStretch(1)
        widget.setLayout(layout)
        self.dock.setWidget(widget)

    def load(self):
        filename = QtGui.QFileDialog.getOpenFileName(self)
        self.loadFile(filename)

    def loadFile(self, filename):
        try:
            with open(filename) as f:
                data = f.read()
            self.glWidget.setFragmentShader(data)
            self.makeDock(data)
        except:
            err = str(sys.exc_info()[1])
            mb = QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Error loading shader",
                                   err[:50] + "...", QtGui.QMessageBox.Ok)
            mb.setDetailedText(err)
            mb.exec_()

app = QtGui.QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec_())
