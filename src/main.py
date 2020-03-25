#!/usr/bin/env python

# vim: sw=4 ts=4 sts=4 et:

from __future__ import print_function, division

from html import escape
import collections
import re
import signal
import sys
import time
from OpenGL import GL
import OpenGL.GL.shaders
import MyGL
from preprocessor import Preprocessor
from updater import Updater
import Qt

# global TODO: handle input (python code in shader comment, eval it),
#              advanced GUI generation (from comments)


class GentleLineEdit(Qt.QLineEdit):
    def __init__(self, label="", parent=None):
        super(GentleLineEdit, self).__init__(label, parent)
        self.editingFinished.connect(self.clearFocus)
        self.editingFinished.connect(self.releaseKeyboard)
        self.setAlignment(Qt.Qt.AlignRight)

    def focusInEvent(self, e):
        super(GentleLineEdit, self).focusInEvent(e)
        self.grabKeyboard()


class CoordUniform(object):
    def __init__(self):
        self.x = self.y = self.z = (0.0, 0.0, 0.0)
        self.size = (1, 1)

    def origin(self):
        self.x = (0.0, 0.0, self.x[2])
        self.y = (0.0, 0.0, self.y[2])

    def zoom_reset(self):
        self.z = (0.0, 0.0, 0.0)

    def add(self, x=0.0, y=0.0, z=0.0):
        f = lambda v, d: (v[0], v[1], v[2] + d)
        self.x = f(self.x, x)
        self.y = f(self.y, y)
        self.z = f(self.z, z)

    def move(self, x, y):
        z = 2.0 / (1.1 ** self.z[0]) / self.size[1]
        f = lambda v, d: (v[0] + d * z, v[1], v[2])
        self.x = f(self.x, x)
        self.y = f(self.y, y)

    def zoom(self, z, origin=None):
        if origin:
            sx, sy = origin[0] - self.size[0] / 2.0, origin[1] - self.size[1] / 2.0
        else:
            sx, sy = (0, 0)
        self.move(sx, -sy)
        self.z = (self.z[0] + z, self.z[1], self.z[2])
        self.move(-sx, sy)

    def update(self):
        f = lambda v, s: (v[0] + v[1] / s, (v[1] * 15 + v[2]) / 16, v[2])
        z = 25 * 1.1 ** self.z[0]
        self.x = f(self.x, z)
        self.y = f(self.y, z)
        self.z = f(self.z, 2)

    def items(self):
        yield "_x", self.x[0]
        yield "_y", self.y[0]
        yield "_z", 1.1 ** self.z[0]
        yield "_aspect", self.size[0] / self.size[1]


class GLWidget(Qt.QGLWidget):
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
        self.vertexShader = MyGL.compileShader(
            self.vertexShaderData, GL.GL_VERTEX_SHADER
        )

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        self.coord.size = (width, height)

    def paintGL(self):
        GL.glBegin(GL.GL_TRIANGLE_STRIP)
        GL.glVertex3f(-1.0, -1.0, 0.0)
        GL.glVertex3f(1.0, -1.0, 0.0)
        GL.glVertex3f(-1.0, 1.0, 0.0)
        GL.glVertex3f(1.0, 1.0, 0.0)
        GL.glEnd()

    def getFps(self):
        return (len(self.times) - 1) / (self.times[-1] - self.times[0])

    def getUniforms(self):
        uniforms = {}
        types = {}
        count = GL.glGetProgramiv(self.program, GL.GL_ACTIVE_UNIFORMS)
        for i in range(count):
            name, size, type_ = GL.glGetActiveUniform(self.program, i)
            name = bytes(name).split(b"\x00")[0].decode()
            loc = GL.glGetUniformLocation(self.program, name)
            if name[0] == "_":  # FIXME: ignore uniforms from vertexShaderData
                continue
            if size == 1 and type_ == GL.GL_INT:
                arr = OpenGL.arrays.GLintArray.zeros([1])
                GL.glGetUniformiv(self.program, loc, arr)
                uniforms[name] = arr[0]
            if size == 1 and type_ == GL.GL_FLOAT:
                arr = OpenGL.arrays.GLfloatArray.zeros([1])
                GL.glGetUniformfv(self.program, loc, arr)
                uniforms[name] = arr[0]
            if size == 1 and type_ == GL.GL_BOOL:
                arr = OpenGL.arrays.GLintArray.zeros([1])
                GL.glGetUniformiv(self.program, loc, arr)
                uniforms[name] = arr[0]
            types[name] = type_
        return uniforms, types

    def setFragmentShader(self, shader):
        fragmentShader = MyGL.compileShader(shader, GL.GL_FRAGMENT_SHADER)
        program = GL.shaders.compileProgram(self.vertexShader, fragmentShader)
        GL.glUseProgram(program)
        self.program = program
        self.coord.size = (self.width(), self.height())
        for name, value in self.coord.items():
            self.setUniform(name, value)

    def setUniform(self, name, value):
        if self.program is not None:
            loc = GL.glGetUniformLocation(self.program, name)
            # TODO: coerce value to appropriate type
            if isinstance(value, float):
                GL.glUniform1f(loc, value)
            if isinstance(value, (bool, int)):
                GL.glUniform1i(loc, value)

    def tick(self):
        self.coord.update()
        for name, value in self.coord.items():
            self.setUniform(name, value)
        self.updateGL()
        self.times.append(time.time())


# TODO: UniformBase should inherit QWidget
class UniformBase(object):
    def __init__(self, parent, name, value):
        self.parent = parent
        self.name = name
        self.value = value

    def init_widgets(self, widgets):
        self.widgets = widgets
        for w in widgets:
            self.parent.shaderLayout.addWidget(w)

    def _set_value(self, value):
        self.value = value
        self.parent.glWidget.setUniform(self.name, self.value)

    def hide(self):
        for w in self.widgets:
            w.hide()

    def show(self):
        for w in self.widgets:
            w.show()

    def delete(self):
        for w in self.widgets:
            w.setParent(None)


class LineEditUniform(UniformBase):
    def __init__(self, parent, name, value):
        super(LineEditUniform, self).__init__(parent, name, value)
        label = Qt.QLabel(name)
        edit = GentleLineEdit(str(value))

        def l(text):
            try:
                value = float(text)
            except ValueError:
                return
            self._set_value(value)

        edit.textChanged.connect(l)
        self.init_widgets([label, edit])

    def update(self):
        self.parent.glWidget.setUniform(self.name, self.value)


class SliderUniform(UniformBase):
    def __init__(self, parent, name, value, min, max):
        super(SliderUniform, self).__init__(parent, name, value)
        self.slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.slider.setValue(value)
        self.update(min, max)
        self.slider.valueChanged.connect(lambda x: self._set_value(x))
        self.init_widgets([Qt.QLabel(name), self.slider])

    def update(self, min, max):
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        self.parent.glWidget.setUniform(self.name, self.value)


class CheckBoxUniform(UniformBase):
    def __init__(self, parent, name, value):
        super(CheckBoxUniform, self).__init__(parent, name, value)
        cbox = Qt.QCheckBox(name)
        cbox.setCheckState(Qt.Qt.Unchecked if value == 0 else Qt.Qt.Checked)
        cbox.stateChanged.connect(lambda _: self._set_value(cbox.isChecked()))
        self.init_widgets([cbox])

    def update(self):
        self.parent.glWidget.setUniform(self.name, self.value)


def format_error(prep, err_text):
    re_err_intel = re.compile(
        r"""^
        (?P<fno> [0-9]+):(?P<line> [0-9]+ )
        \( (?P<extra> [0-9]+ ) \):\ # column?
        (?P<kind> [^:]* ):\ #
        (?P<text> .* )
        $""",
        re.X,
    )
    re_err_nvidia = re.compile(
        r"""^
        (?P<fno> [0-9]+)
        \( (?P<line> [0-9]+ ) \)
        \ :\ (?P<kind> warning | error )\ #
        (?P<extra> C[0-9]+ ):\ # Error code
        (?P<text> .* )
        $""",
        re.X,
    )
    result = []
    prev = None
    for err_line in err_text.split("\n"):
        m = re_err_intel.match(str(err_line))
        if not m:
            m = re_err_nvidia.match(str(err_line))
        if m:
            m = m.groupdict()
            m_fno, m_line = int(m["fno"]), int(m["line"])
            curr = (m_fno, m_line)
            if prev != curr:
                prev = curr
                result.append("\n")
                try:
                    result.append("{}:{}:\n".format(escape(prep.fnames[m_fno]), m_line))
                    result.append("%5d | " % (m_line,))
                    result.append(escape(prep.fcontents[m_fno][m_line - 1]))
                except IndexError:
                    result.append("??? {}:{}".format(m_fno, m_line))
                result.append("\n")
            if m["kind"] == "error":
                result.append("<font color='#CC0000'>")
            elif m["kind"] == "warning":
                result.append("<font color='#75507B'>")
            else:
                result.append("<font>")
            result.append(escape(m["kind"]))
            result.append("</font>")
            if "extra" in m:
                result.append("(%s)" % escape(m["extra"]))
            result.append(": " + escape(m["text"]) + "\n")
        else:
            result.append(escape(err_line) + "\n")
    result = "<pre>" + "".join(result) + "</pre>"
    return result


# TODO: remove this
# prep = Preprocessor("./shader/shadertoy/ltSyRm_Sliding_mandelbrot.f")
# print(format_error(prep, "0:6(24): error: `blablabla' undeclared"))
# print()
# print(format_error(prep, '0(6) : error C1008: undefined variable "blabla"'))
# sys.exit(0)


class MainWindow(Qt.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle("PyGL")
        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.shaderDock, self.shaderLayout = self.initShaderDock()
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, self.shaderDock)

        self.renderDock, self.renderLayout = self.initRenderDock()
        self.addDockWidget(Qt.Qt.LeftDockWidgetArea, self.renderDock)

        self.uniforms = {}
        self.filename = None
        self.updater = None

        self.timer = Qt.QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.time = Qt.QTime()
        self.time.start()
        self.time_uniform = 0.0
        self.timeron = True  # FIXME
        self.cursorLocPos = Qt.QPoint(0, 0)

    def initShaderDock(self):
        shaderDock = Qt.QDockWidget()
        shaderLayout = Qt.QVBoxLayout()
        widget = Qt.QWidget()
        widget.setLayout(shaderLayout)
        shaderDock.setWidget(widget)

        loadButton = Qt.QPushButton("Load")
        loadButton.clicked.connect(self.load)
        shaderLayout.addWidget(loadButton)

        shaderLayout.addStretch(0)
        return shaderDock, shaderLayout

    def initRenderDock(self):
        renderDock = Qt.QDockWidget()
        renderLayout = Qt.QVBoxLayout()
        widget = Qt.QWidget()
        widget.setLayout(renderLayout)
        renderDock.setWidget(widget)

        wCoord = Qt.QWidget()
        lCoord = Qt.QHBoxLayout()
        wCoord.setLayout(lCoord)
        lCoord.setContentsMargins(0, 0, 0, 0)

        renderLayout.addWidget(wCoord)

        wPos = Qt.QWidget()
        lPos = Qt.QVBoxLayout()
        wPos.setLayout(lPos)
        lPos.setContentsMargins(0, 0, 0, 0)
        posX = GentleLineEdit()
        posX.setValidator(Qt.QIntValidator())
        posY = GentleLineEdit()
        posY.setValidator(Qt.QIntValidator())
        lPos.addWidget(Qt.QLabel("Position"))
        lPos.addWidget(posX)
        lPos.addWidget(posY)

        lCoord.addWidget(wPos)

        wSize = Qt.QWidget()
        lSize = Qt.QVBoxLayout()
        wSize.setLayout(lSize)
        lSize.setContentsMargins(0, 0, 0, 0)
        sizeX = GentleLineEdit()
        sizeX.setValidator(Qt.QIntValidator())
        sizeY = GentleLineEdit()
        sizeY.setValidator(Qt.QIntValidator())
        lSize.addWidget(Qt.QLabel("Size"))
        lSize.addWidget(sizeX)
        lSize.addWidget(sizeY)

        lCoord.addWidget(wSize)

        wFPS = Qt.QWidget()
        lFPS = Qt.QHBoxLayout()
        wFPS.setLayout(lFPS)
        lFPS.setContentsMargins(0, 0, 0, 0)
        lFPS.addWidget(Qt.QLabel("FPS"))
        fps = GentleLineEdit()
        fps.setValidator(Qt.QIntValidator())
        lFPS.addWidget(fps)

        renderLayout.addWidget(wFPS)

        saveButton = Qt.QPushButton("Set output directory...")
        renderLayout.addWidget(saveButton)

        renderButton = Qt.QPushButton("Render")
        renderLayout.addWidget(renderButton)

        renderLayout.addStretch(0)
        renderDock.hide()
        return renderDock, renderLayout

    def updateUniforms(self, data, uniforms, types):
        for uni in self.uniforms.values():
            uni.hide()
        unpragmed = set(uniforms)
        unpragmed.discard("time")
        r = re.compile(r"^\s*#\s*pragma\s+machuchu\s+(.*)$", re.M)
        for params in r.findall(data):
            params = re.split(r"\s+", params)
            if len(params) == 4 and params[0] == "slider":
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
                    self.uniforms[name] = SliderUniform(self, name, value, min, max)
                unpragmed.remove(name)

        for name in unpragmed:
            value = uniforms[name]
            old = self.uniforms.get(name, None)
            if isinstance(old, (LineEditUniform, CheckBoxUniform)):
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
        filename = Qt.QFileDialog.getOpenFileName(
            self, directory="./shader", filter="Fragment shader (*.f)"
        )
        if filename[0] != "":
            self.loadFile(filename[0])

    def reload(self):
        if self.filename:
            self.loadFile(self.filename)

    def loadFile(self, filename):
        self.filename = filename
        try:
            prep = Preprocessor(filename)
            self.updater = Updater(prep.fnames)
            self.glWidget.setFragmentShader(prep.text)
            uniforms, types = self.glWidget.getUniforms()
            self.updateUniforms(prep.text, uniforms, types)
        except Exception as e:
            if isinstance(e, MyGL.ShaderCompilationError):
                text = format_error(prep, e.text)
                print(e.text)
            else:
                text = escape(str(e))
            mb = Qt.QMessageBox(
                Qt.QMessageBox.Warning, "Error loading shader", text, Qt.QMessageBox.Ok
            )
            mb.setTextFormat(Qt.Qt.RichText)
            mb.exec_()

    def tick(self):
        if self.updater and self.updater.check():
            self.reload()
        if self.timeron:
            self.time_uniform += float(self.time.elapsed())
            self.glWidget.setUniform("time", self.time_uniform)
        self.time.start()
        self.glWidget.tick()
        self.setWindowTitle("{:d} fps".format(int(round(self.glWidget.getFps()))))

    def timer_reset(self):
        self.time_uniform = 0.0
        self.glWidget.setUniform("time", self.time_uniform)

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
        if not e.isAutoRepeat() and not self.keyboardGrabber():
            if e.key() == Qt.Qt.Key_W:
                self.glWidget.coord.add(y=+1)
            if e.key() == Qt.Qt.Key_S:
                self.glWidget.coord.add(y=-1)
            if e.key() == Qt.Qt.Key_A:
                self.glWidget.coord.add(x=-1)
            if e.key() == Qt.Qt.Key_D:
                self.glWidget.coord.add(x=+1)
            if e.key() == Qt.Qt.Key_Period:
                self.glWidget.coord.add(z=+1)
            if e.key() == Qt.Qt.Key_Comma:
                self.glWidget.coord.add(z=-1)
        if e.key() == Qt.Qt.Key_F10:
            self.timer_reset()
        if e.key() == Qt.Qt.Key_Escape:
            self.close()
        if e.key() == Qt.Qt.Key_P:
            self.timeron = not self.timeron
        if e.key() == Qt.Qt.Key_F:
            self.toggleShaderDock()
        if e.key() == Qt.Qt.Key_R:
            self.toggleRenderDock()
        if e.key() == Qt.Qt.Key_C:
            self.glWidget.coord.origin()
        if e.key() == Qt.Qt.Key_V:
            self.glWidget.coord.zoom_reset()
        if e.modifiers() == Qt.Qt.ControlModifier and e.key() == Qt.Qt.Key_O:
            self.load()

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat() and not self.keyboardGrabber():
            if e.key() == Qt.Qt.Key_W:
                self.glWidget.coord.add(y=-1)
            if e.key() == Qt.Qt.Key_S:
                self.glWidget.coord.add(y=+1)
            if e.key() == Qt.Qt.Key_A:
                self.glWidget.coord.add(x=+1)
            if e.key() == Qt.Qt.Key_D:
                self.glWidget.coord.add(x=-1)
            if e.key() == Qt.Qt.Key_Period:
                self.glWidget.coord.add(z=-1)
            if e.key() == Qt.Qt.Key_Comma:
                self.glWidget.coord.add(z=+1)

    def wheelEvent(self, e):
        d = e.angleDelta()
        if Qt.QApplication.keyboardModifiers() & Qt.Qt.ControlModifier:
            self.glWidget.coord.zoom(d.y() / 100, (e.pos().x(), e.pos().y()))
        else:
            self.glWidget.coord.move(x=-d.x(), y=d.y())

    def warpCursor(self):
        cursor = Qt.QCursor()
        warp = lambda value, max: (value - 1) % (max - 2) + 1
        newCursorLocPos = Qt.QPoint(
            warp(self.cursorLocPos.x(), self.width()),
            warp(self.cursorLocPos.y(), self.height()),
        )
        if newCursorLocPos != self.cursorLocPos:
            cursor.setPos(cursor.pos() + newCursorLocPos - self.cursorLocPos)
            self.cursorLocPos = newCursorLocPos

    def mousePressEvent(self, e):
        if e.button() == Qt.Qt.MidButton or e.button() == Qt.Qt.RightButton:
            self.cursorLocPos = e.pos()
        grabber = self.keyboardGrabber()
        if grabber:
            grabber.releaseKeyboard()
            grabber.clearFocus()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.Qt.MidButton or e.buttons() == Qt.Qt.RightButton:
            d = self.cursorLocPos - e.pos()
            self.cursorLocPos = e.pos()
            self.warpCursor()
            self.glWidget.coord.move(d.x(), -d.y())


signal.signal(signal.SIGINT, signal.SIG_DFL)
app = Qt.QApplication(sys.argv)
win = MainWindow()
win.show()
if len(Qt.QApplication.arguments()) > 1:
    win.loadFile(Qt.QApplication.arguments()[1])
sys.exit(app.exec_())
