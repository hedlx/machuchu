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

class CoordUniform:
    def __init__(self):
        self.x = self.y = self.z = (0., 0., 0.)

    def origin(self):
        self.x = (0.0, 0.0, self.x[2])
        self.y = (0.0, 0.0, self.y[2])

    def add(self, x=0., y=0., z=0.):
        f = lambda v, d: (v[0], v[1], v[2]+d)
        if x: self.x = f(self.x, x)
        if y: self.y = f(self.y, y)
        if z: self.z = f(self.z, z)

    def update(self):
        f = lambda v, s: (v[0]+v[1]/s, (v[1]*15 + v[2])/16, v[2])
        z = 25*1.1**self.z[0]
        self.x = f(self.x, z)
        self.y = f(self.y, z)
        self.z = f(self.z, 5)

    def items(self):
        yield "_x", self.x[0]
        yield "_y", self.y[0]
        yield "_z", 1.1**self.z[0]

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
        self.parent = parent
        super(GLWidget, self).__init__(parent)
        self.program = None
        self.times = collections.deque([0], maxlen=10)
        self.coord = CoordUniform()

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

    def getFps(self):
        return len(self.times) / (self.times[-1] - self.times[0])

    def setFragmentShader(self, shader):
        fragmentShader = GL.shaders.compileShader(shader, GL.GL_FRAGMENT_SHADER)
        program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(program)
        self.setUniform("_aspect", float(self.width()) / self.height())
        for name, value in self.coord.items():
            self.setUniform(name, value)
        self.program = program

    def setUniform(self, name, value):
        if self.program is not None:
            loc = GL.glGetUniformLocation(self.program, name)
            if isinstance(value, float): GL.glUniform1f(loc, value)
            if isinstance(value, int): GL.glUniform1i(loc, value)

    def tick(self):
        self.coord.update()
        for name, value in self.coord.items():
            self.setUniform(name, value)
        self.updateGL()
        self.times.append(time.time())

def lineEditUniform(name, value, setUniform):
    label = QtGui.QLabel(name)
    edit = QtGui.QLineEdit(value)
    def l(text, n=name):
        try:
            setUniform(n, float(text))
        except ValueError:
            pass
    edit.textChanged.connect(l)
    return [label, edit]

def sliderUniform(name, value, min, max, setUniform):
    label = QtGui.QLabel(name)
    slider = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)
    slider.setMinimum(min)
    slider.setMaximum(max)
    slider.setValue(value)
    slider.valueChanged.connect(lambda v: setUniform(name, v))
    setUniform(name, slider.value())
    return [label, slider]

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
        loadButton = QtGui.QPushButton("Load", shortcut=QtCore.Qt.CTRL + QtCore.Qt.Key_O)
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

    def setUniform(self, name, value):
        self.uniforms[name] = value
        self.glWidget.setUniform(name, value)

    def setUniformWidgets(self, name, widgets):
        self.uniformWidgets[name] = widgets
        for widget in widgets:
            self.docklayout.addWidget(widget)

    def updateUniforms(self, data):
        r = re.compile(r'uniform\s+(\w+)\s+(\w+)(?:\s+=\s+([^;]+))?')
        for name, widgets in self.uniformWidgets.items():
            for widget in widgets:
                widget.hide()

        uniforms = r.findall(data) # TODO: remove uniform parser
        for type_, name, value in uniforms:
            if type_ != 'float': continue
            if name in self.uniforms:
                self.glWidget.setUniform(name, float(self.uniforms[name]))
                for widget in self.uniformWidgets[name]:
                    widget.show()
            else:
                self.uniforms[name] = value
                if name != 'time':
                    self.setUniformWidgets(name, lineEditUniform(name, value, self.setUniform))

        r = re.compile(r'^\s*#\s*pragma\s+machachu\s+(.*)$', re.M)
        for params in r.findall(data):
            params = re.split("\s+", params)
            if len(params) == 5 and params[0] == 'slider':
                name = params[1]
                value,min,max = map(int, params[2:5])
                if name in self.uniforms: value = self.uniforms[name]
                widgets = sliderUniform(name, value, min, max, self.setUniform)
                self.setUniformWidgets(name, widgets)

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
                self.glWidget.coord.add(y=+1)
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.coord.add(y=-1)
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.coord.add(x=-1)
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.coord.add(x=+1)
            if e.key() == QtCore.Qt.Key_Period:
                self.glWidget.coord.add(z=+1)
            if e.key() == QtCore.Qt.Key_Comma:
                self.glWidget.coord.add(z=-1)
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        if e.key() == QtCore.Qt.Key_P:
            self.timeron = not self.timeron
        if e.key() == QtCore.Qt.Key_F:
            self.toggleDock()
        if e.key() == QtCore.Qt.Key_C:
            self.glWidget.coord.origin()
        if (e.modifiers() == QtCore.Qt.CTRL) and (e.key() == QtCore.Qt.Key_O):
            self.load()



    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == QtCore.Qt.Key_W:
                self.glWidget.coord.add(y=-1)
            if e.key() == QtCore.Qt.Key_S:
                self.glWidget.coord.add(y=+1)
            if e.key() == QtCore.Qt.Key_A:
                self.glWidget.coord.add(x=+1)
            if e.key() == QtCore.Qt.Key_D:
                self.glWidget.coord.add(x=-1)
            if e.key() == QtCore.Qt.Key_Period:
                self.glWidget.coord.add(z=-1)
            if e.key() == QtCore.Qt.Key_Comma:
                self.glWidget.coord.add(z=+1)

signal.signal(signal.SIGINT, signal.SIG_DFL)
app = QtGui.QApplication(sys.argv)
win = MainWindow()
win.show()
if len(QtGui.QApplication.arguments()) > 1:
    win.loadFile(QtGui.QApplication.arguments()[1])
sys.exit(app.exec_())
