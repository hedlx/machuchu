#!/usr/bin/env python

# vim: sw=4 ts=4 sts=4 et:

from __future__ import print_function

import sys, re, signal, time, collections
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtOpenGL import *
from OpenGL import GL
import OpenGL.arrays
import OpenGL.GL.shaders
from preprocessor import preprocess
from updater import Updater

# global TODO: handle input (python code in shader comment, eval it),
#              advanced GUI generation (from comments)


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

    def addSpeed(self, x=0., y=0., z=0.):
        f = lambda v, d: (v[0], v[1]+d, v[2])
        if x: self.x = f(self.x, x)
        if y: self.y = f(self.y, y)
        if z: self.z = f(self.z, z)

    def addPosn(self, x=0., y=0., z=0.):
        f = lambda v, d: (v[0]+d, v[1], v[2])
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


class GLWidget(QGLWidget):
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
        self.vertexShader = GL.shaders.compileShader(self.vertexShaderData,
                                                     GL.GL_VERTEX_SHADER)

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

    def getUniforms(self):
        result = {}
        count = GL.glGetProgramiv(self.program, GL.GL_ACTIVE_UNIFORMS)
        for i in range(count):
            name, size, type_ = GL.glGetActiveUniform(self.program, i)
            loc = GL.glGetUniformLocation(self.program, name)
            name = name.decode()
            if name[0] == '_':  # FIXME: ignore uniforms from vertexShaderData
                continue
            if size == 1 and type_ == GL.GL_INT:
                arr = OpenGL.arrays.GLintArray.zeros(1)
                GL.glGetUniformiv(self.program, loc, arr)
                result[name] = arr[0]
            if size == 1 and type_ == GL.GL_FLOAT:
                arr = OpenGL.arrays.GLfloatArray.zeros(1)
                GL.glGetUniformfv(self.program, loc, arr)
                result[name] = arr[0]
        return result

    def setFragmentShader(self, shader):
        fragmentShader = GL.shaders.compileShader(shader,
                                                  GL.GL_FRAGMENT_SHADER)
        program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(program)
        self.program = program
        self.setUniform("_aspect", float(self.width()) / self.height())
        for name, value in self.coord.items():
            self.setUniform(name, value)

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


class UniformBase(object):
    def __init__(self, parent, name, value):
        self.parent = parent
        self.name = name
        self.value = value

    def init_widgets(self, widgets):
        self.widgets = widgets
        for w in widgets:
            self.parent.docklayout.addWidget(w)

    def hide(self):
        for w in self.widgets: w.hide()

    def show(self):
        for w in self.widgets: w.show()

    def delete(self):
        for w in self.widgets: w.setParent(None)


class LineEditUniform(UniformBase):
    def __init__(self, parent, name, value):
        super(LineEditUniform, self).__init__(parent, name, value)
        label = QLabel(name)
        edit = QLineEdit(str(value))

        def l(text):
            try: self.value = float(text)
            except ValueError: return
            self.parent.glWidget.setUniform(name, self.value)
        edit.textChanged.connect(l)
        self.init_widgets([label, edit])

    def update(self):
        self.parent.glWidget.setUniform(self.name, self.value)


class SliderUniform(UniformBase):
    def __init__(self, parent, name, value, min, max):
        super(SliderUniform, self).__init__(parent, name, value)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setValue(value)
        self.update(min, max)
        self.slider.valueChanged.connect(lambda x: self.setValue(x))
        self.init_widgets([QLabel(name), self.slider])

    def setValue(self, value):
        self.value = value
        self.parent.glWidget.setUniform(self.name, value)

    def update(self, min, max):
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.parent.glWidget.setUniform(self.name, self.value)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle('PyGL')
        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.dock = QDockWidget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        widget = QWidget()
        self.docklayout = QVBoxLayout()
        loadButton = QPushButton("Load", shortcut=Qt.CTRL + Qt.Key_O)
        loadButton.clicked.connect(self.load)
        self.docklayout.addWidget(loadButton)
        widget.setLayout(self.docklayout)
        self.dock.setWidget(widget)
        self.docklayout.addStretch(0)

        self.uniforms = {}
        self.filename = None
        self.updater = None

        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.time = QTime()
        self.time.start()
        self.time_uniform = 0.
        self.timeron = True  # FIXME
        self.cursorLocPos = (0, 0)

    def updateUniforms(self, data, uniforms):
        for uni in self.uniforms.values():
            uni.hide()
        unpragmed = set(uniforms)
        r = re.compile(r'^\s*#\s*pragma\s+machachu\s+(.*)$', re.M)
        for params in r.findall(data):
            params = re.split(r"\s+", params)
            if len(params) == 4 and params[0] == 'slider':
                name = params[1]
                value = uniforms[name]
                min, max = map(int, params[2:4])
                old = self.uniforms.get(name, None)
                if isinstance(old, SliderUniform):
                    old.update(min, max)
                    old.show()
                else:
                    if old is not None:
                        old.delete()
                    self.uniforms[name] = SliderUniform(self, name, value,
                                                        min, max)
                unpragmed.remove(name)

        for name in unpragmed:
            if name == 'time': continue
            value = uniforms[name]
            old = self.uniforms.get(name, None)
            if isinstance(old, LineEditUniform):
                old.update()
                old.show()
            else:
                if old is not None:
                    old.delete()
                self.uniforms[name] = LineEditUniform(self, name, value)

    def load(self):
        filename = QFileDialog.getOpenFileName(self,
                                               filter="Fragment shader (*.f)")
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
            self.updateUniforms(data, self.glWidget.getUniforms())
        except:
            e = sys.exc_info()[1]
            text = str(e)

            if type(e) == RuntimeError and len(e.args) == 3 and \
               e.args[2] == GL.GL_FRAGMENT_SHADER:
                text = e.args[0]

            mb = QMessageBox(QMessageBox.Warning, "Error loading shader",
                             text, QMessageBox.Ok)
            mb.exec_()

    def tick(self):
        if self.updater and self.updater.check():
            self.reload()
        if self.timeron:
            self.time_uniform += float(self.time.elapsed())
            self.glWidget.setUniform('time', self.time_uniform)
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
            if e.key() == Qt.Key_W:
                self.glWidget.coord.add(y=+1)
            if e.key() == Qt.Key_S:
                self.glWidget.coord.add(y=-1)
            if e.key() == Qt.Key_A:
                self.glWidget.coord.add(x=-1)
            if e.key() == Qt.Key_D:
                self.glWidget.coord.add(x=+1)
            if e.key() == Qt.Key_Period:
                self.glWidget.coord.add(z=+1)
            if e.key() == Qt.Key_Comma:
                self.glWidget.coord.add(z=-1)
        if e.key() == Qt.Key_Escape:
            self.close()
        if e.key() == Qt.Key_P:
            self.timeron = not self.timeron
        if e.key() == Qt.Key_F:
            self.toggleDock()
        if e.key() == Qt.Key_C:
            self.glWidget.coord.origin()
        if (e.modifiers() == Qt.CTRL) and (e.key() == Qt.Key_O):
            self.load()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() == Qt.Key_W:
                self.glWidget.coord.add(y=-1)
            if e.key() == Qt.Key_S:
                self.glWidget.coord.add(y=+1)
            if e.key() == Qt.Key_A:
                self.glWidget.coord.add(x=+1)
            if e.key() == Qt.Key_D:
                self.glWidget.coord.add(x=-1)
            if e.key() == Qt.Key_Period:
                self.glWidget.coord.add(z=-1)
            if e.key() == Qt.Key_Comma:
                self.glWidget.coord.add(z=+1)

    def wheelEvent(self, e):
        # TODO: ctrl to zoom
        d = e.angleDelta()
        self.glWidget.coord.update(dx=-d.x()/1000., dy=d.y()/1000.)

    def warpCursor(self):
        cursor = QCursor()
        pos = cursor.pos()
        if self.cursorLocPos[0] <= 0:
            self.cursorLocPos = (self.width()-1+self.cursorLocPos[0], self.cursorLocPos[1])
            cursor.setPos(pos.x()+self.cursorLocPos[0], pos.y())
        elif self.cursorLocPos[0] >= self.width():
            self.cursorLocPos = (1+self.cursorLocPos[0]-self.width(), self.cursorLocPos[1])
            cursor.setPos(pos.x()-self.width()+self.cursorLocPos[0], pos.y())
        elif self.cursorLocPos[1] <= 0:
            self.cursorLocPos = (self.cursorLocPos[0], self.height()-1+self.cursorLocPos[1])
            cursor.setPos(pos.x(), pos.y()+self.cursorLocPos[1])
        elif self.cursorLocPos[1] >= self.height():
            self.cursorLocPos = (self.cursorLocPos[0], 1+self.cursorLocPos[1]-self.height())
            cursor.setPos(pos.x(), pos.y()-self.height()+self.cursorLocPos[1])

    def mousePressEvent(self, e):
        if e.button() == Qt.MidButton or e.button() == Qt.RightButton:
            self.cursorLocPos = (e.pos().x(), e.pos().y())

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MidButton or e.buttons() == Qt.RightButton:
            dx = self.cursorLocPos[0] - e.pos().x()
            dy = e.pos().y() - self.cursorLocPos[1]
            self.cursorLocPos = (e.pos().x(), e.pos().y())
            self.warpCursor()
            zoom = 2./(1.1**self.glWidget.coord.z[0])
            self.glWidget.coord.addPosn(x=zoom*float(dx)/float(self.glWidget.height()))
            self.glWidget.coord.addPosn(y=zoom*float(dy)/float(self.glWidget.height()))


signal.signal(signal.SIGINT, signal.SIG_DFL)
app = QApplication(sys.argv)
win = MainWindow()
win.show()
if len(QApplication.arguments()) > 1:
    win.loadFile(QApplication.arguments()[1])
sys.exit(app.exec_())
