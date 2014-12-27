#!/usr/bin/env python

# vim: sw=4 ts=4 sts=4 et:

from __future__ import print_function, division

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

class GentleLineEdit(QLineEdit):
    def __init__(self, label="", parent=None):
        super(QLineEdit, self).__init__(label, parent)
        self.editingFinished.connect(self.clearFocus)
        self.editingFinished.connect(self.releaseKeyboard)

    def mousePressEvent(self, e):
        self.grabKeyboard()


class CoordUniform(object):
    def __init__(self):
        self.x = self.y = self.z = (0., 0., 0.)
        self.size = (1,1)

    def origin(self):
        self.x = (0.0, 0.0, self.x[2])
        self.y = (0.0, 0.0, self.y[2])

    def add(self, x=0., y=0., z=0.):
        f = lambda v, d: (v[0], v[1], v[2]+d)
        if x: self.x = f(self.x, x)
        if y: self.y = f(self.y, y)
        if z: self.z = f(self.z, z)

    def move(self, x, y):
        z = 2./(1.1**self.z[0])/self.size[1]
        f = lambda v, d: (v[0]+d*z, v[1], v[2])
        self.x = f(self.x, x)
        self.y = f(self.y, y)

    def zoom(self, z, origin = None):
        if origin:
            sx, sy = origin[0]-self.size[0]/2., origin[1]-self.size[1]/2.
        else:
            sx, sy = (0, 0)
        self.move(sx, -sy)
        self.z = (self.z[0]+z, self.z[1], self.z[2])
        self.move(-sx, sy)

    def update(self):
        f = lambda v, s: (v[0]+v[1]/s, (v[1]*15 + v[2])/16, v[2])
        z = 25*1.1**self.z[0]
        self.x = f(self.x, z)
        self.y = f(self.y, z)
        self.z = f(self.z, 2)

    def items(self):
        yield "_x", self.x[0]
        yield "_y", self.y[0]
        yield "_z", 1.1**self.z[0]
        yield "_aspect", self.size[0] / self.size[1]


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
        self.coord.size = (width, height)

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
        uniforms = {}
        types = {}
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
                uniforms[name] = arr[0]
            if size == 1 and type_ == GL.GL_FLOAT:
                arr = OpenGL.arrays.GLfloatArray.zeros(1)
                GL.glGetUniformfv(self.program, loc, arr)
                uniforms[name] = arr[0]
            if size == 1 and type_ == GL.GL_BOOL:
                arr = OpenGL.arrays.GLintArray.zeros(1)
                GL.glGetUniformiv(self.program, loc, arr)
                uniforms[name] = arr[0]
            types[name] = type_
        return uniforms, types

    def setFragmentShader(self, shader):
        fragmentShader = GL.shaders.compileShader(shader,
                                                  GL.GL_FRAGMENT_SHADER)
        program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(program)
        self.program = program
        self.coord.size = (self.width(), self.height())
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
            self.parent.shaderLayout.addWidget(w)

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
        edit = GentleLineEdit(str(value))

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

class CheckBoxUniform(UniformBase):
    def __init__(self, parent, name, value):
        super(CheckBoxUniform, self).__init__(parent, name, value)
        self.checkbox = QCheckBox()
        self.checkbox.setCheckState(Qt.Unchecked if value == 0 else Qt.Checked)
        self.checkbox.stateChanged.connect(lambda x: self.setValue(x))
        self.init_widgets([self.checkbox, QLabel(name)])

    def init_widgets(self, widgets):
        box = QWidget()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft);
        box.setLayout(layout)
        for w in widgets:
            layout.addWidget(w)
        self.parent.shaderLayout.addWidget(box)
        self.widgets = widgets + [box]

    def setValue(self, state):
        self.parent.glWidget.setUniform(self.name,
                                        1 if state == Qt.Checked else 0)

    def update(self):
        self.parent.glWidget.setUniform(self.name, self.value)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle('PyGL')
        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.shaderDock, self.shaderLayout = self.initShaderDock()
        self.addDockWidget(Qt.RightDockWidgetArea, self.shaderDock)

        self.renderDock, self.renderLayout = self.initRenderDock()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.renderDock)

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
        self.cursorLocPos = QPoint(0, 0)

    def initShaderDock(self):
        shaderDock = QDockWidget()
        shaderLayout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(shaderLayout)
        shaderDock.setWidget(widget)

        loadButton = QPushButton("Load")
        loadButton.clicked.connect(self.load)
        shaderLayout.addWidget(loadButton)

        shaderLayout.addStretch(0)
        return shaderDock, shaderLayout

    def initRenderDock(self):
        renderDock = QDockWidget()
        renderLayout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(renderLayout)
        renderDock.setWidget(widget)

        wCoord = QWidget()
        lCoord = QHBoxLayout()
        wCoord.setLayout(lCoord)
        lCoord.setContentsMargins(0,0,0,0)

        renderLayout.addWidget(wCoord)

        wPos = QWidget()
        lPos = QVBoxLayout()
        wPos.setLayout(lPos)
        lPos.setContentsMargins(0,0,0,0)
        posX = GentleLineEdit()
        posY = GentleLineEdit()
        lPos.addWidget(QLabel("Position"))
        lPos.addWidget(posX)
        lPos.addWidget(posY)

        lCoord.addWidget(wPos)

        wSize = QWidget()
        lSize = QVBoxLayout()
        wSize.setLayout(lSize)
        lSize.setContentsMargins(0,0,0,0)
        sizeX = GentleLineEdit()
        sizeY = GentleLineEdit()
        lSize.addWidget(QLabel("Size"))
        lSize.addWidget(sizeX)
        lSize.addWidget(sizeY)

        lCoord.addWidget(wSize)

        wFPS = QWidget()
        lFPS = QHBoxLayout()
        wFPS.setLayout(lFPS)
        lFPS.setContentsMargins(0,0,0,0)
        lFPS.addWidget(QLabel("FPS"))
        fps = GentleLineEdit()
        lFPS.addWidget(fps)

        renderLayout.addWidget(wFPS)

        saveButton = QPushButton("Set output directory...")
        renderLayout.addWidget(saveButton)

        renderButton = QPushButton("Render")
        renderLayout.addWidget(renderButton)

        renderLayout.addStretch(0)
        renderDock.hide()
        return renderDock, renderLayout

    def updateUniforms(self, data, uniforms, types):
        for uni in self.uniforms.values():
            uni.hide()
        unpragmed = set(uniforms)
        unpragmed.discard('time')
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
            value = uniforms[name]
            old = self.uniforms.get(name, None)
            if isinstance(old, LineEditUniform) or isinstance(old, CheckBoxUniform):
                old.update()
                old.show()
            else:
                if old is not None:
                    old.delete()
                if types[name] == GL.GL_BOOL:
                    self.uniforms[name] = CheckBoxUniform(self, name, value)
                else:
                    self.uniforms[name] = LineEditUniform(self, name, value)

    def load(self):
        filename = QFileDialog.getOpenFileName(self,
                                                directory="./shader",
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
            uniforms, types = self.glWidget.getUniforms()
            self.updateUniforms(data, uniforms, types)
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

    def toggleShaderDock(self):
        if self.shaderDock.isVisible():
            self.shaderDock.hide()
        else:
            self.shaderDock.show()

    def toggleRenderDock(self):
        if self.renderDock.isVisible():
            self.renderDock.hide()
        else:
            self.renderDock.show()

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
            self.toggleShaderDock()
        if e.key() == Qt.Key_R:
            self.toggleRenderDock()
        if e.key() == Qt.Key_C:
            self.glWidget.coord.origin()
        if (e.modifiers() == Qt.ControlModifier) and (e.key() == Qt.Key_O):
            self.load()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat() and not self.keyboardGrabber():
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
        d = e.angleDelta()
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            self.glWidget.coord.zoom(d.y()/100, (e.pos().x(), e.pos().y()))
        else:
            self.glWidget.coord.move(x=-d.x(), y=d.y())

    def warpCursor(self):
        cursor = QCursor()
        warp = lambda value, max: (value-1) % (max-2) + 1
        newCursorLocPos = QPoint(warp(self.cursorLocPos.x(), self.width()),
                                 warp(self.cursorLocPos.y(), self.height()))
        if newCursorLocPos != self.cursorLocPos:
            cursor.setPos(cursor.pos() + newCursorLocPos - self.cursorLocPos)
            self.cursorLocPos = newCursorLocPos

    def mousePressEvent(self, e):
        if e.button() == Qt.MidButton or e.button() == Qt.RightButton:
            self.cursorLocPos = e.pos()
        grabber = self.keyboardGrabber()
        if grabber:
            grabber.releaseKeyboard()
            grabber.clearFocus()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MidButton or e.buttons() == Qt.RightButton:
            d = self.cursorLocPos - e.pos()
            self.cursorLocPos = e.pos()
            self.warpCursor()
            self.glWidget.coord.move(d.x(), -d.y())

signal.signal(signal.SIGINT, signal.SIG_DFL)
app = QApplication(sys.argv)
win = MainWindow()
win.show()
if len(QApplication.arguments()) > 1:
    win.loadFile(QApplication.arguments()[1])
sys.exit(app.exec_())
