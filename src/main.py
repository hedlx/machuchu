#!/usr/bin/env python

from html import escape
import collections
import typing
import re
import ctypes
import traceback
import signal
import sys
import time
from OpenGL import GL
from OpenGL.GL import shaders as GL_shaders
import MyGL
from preprocessor import Preprocessor
from updater import Updater
import Qt
import qtpy

# global TODO: handle input (python code in shader comment, eval it),
#              advanced GUI generation (from comments)


_UniformValue = int | bool | float | tuple[float, float, float, float]


class GentleLineEdit(Qt.QLineEdit):
    def __init__(
        self, label: str = "", parent: Qt.QWidget | None = None
    ) -> None:
        super().__init__(label, parent)
        self.editingFinished.connect(self.clearFocus)
        self.editingFinished.connect(self.releaseKeyboard)
        self.setAlignment(Qt.Qt.AlignRight)

    def focusInEvent(self, e: Qt.QtGui.QFocusEvent) -> None:
        super().focusInEvent(e)
        self.grabKeyboard()


class CoordUniform:
    _Fun = typing.Callable[
        [tuple[float, float, float], float], tuple[float, float, float]
    ]

    def __init__(self) -> None:
        self.x = self.y = self.z = (0.0, 0.0, 0.0)
        self.mouse_pressed = False
        self.mouse_i: None | tuple[int, int] = None
        self.mouse_f = self.mouse_f_start = (float("nan"), float("nan"))
        self.size: tuple[int, int] = (1, 1)

    def origin(self) -> None:
        self.x = (0.0, 0.0, self.x[2])
        self.y = (0.0, 0.0, self.y[2])

    def zoom_reset(self) -> None:
        self.z = (0.0, 0.0, 0.0)

    def add(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        f: CoordUniform._Fun = lambda v, d: (v[0], v[1], v[2] + d)
        self.x = f(self.x, x)
        self.y = f(self.y, y)
        self.z = f(self.z, z)

    def move(self, x: float, y: float) -> None:
        z = 2.0 / (1.1 ** self.z[0]) / self.size[1]
        f: CoordUniform._Fun = lambda v, d: (v[0] + d * z, v[1], v[2])
        self.x = f(self.x, x)
        self.y = f(self.y, y)

    def zoom(
        self, z: float, origin: None | tuple[float, float] = None
    ) -> None:
        if origin:
            sx, sy = (
                origin[0] - self.size[0] / 2.0,
                origin[1] - self.size[1] / 2.0,
            )
        else:
            sx, sy = (0, 0)
        self.move(sx, -sy)
        self.z = (self.z[0] + z, self.z[1], self.z[2])
        self.move(-sx, sy)

    def translate(self, x: float, y: float) -> tuple[float, float]:
        z = 2.0 / (1.1 ** self.z[0]) / self.size[1]
        sx = self.x[0] + (x - self.size[0] / 2.0) * z
        sy = self.y[0] - (y - self.size[1] / 2.0) * z
        return sx, sy

    def mouse_down(self, x: int, y: int) -> None:
        self.mouse_pressed = True
        self.mouse_i = (x, y)
        self.mouse_f = self.mouse_f_start = self.translate(x, y)

    def mouse_move(self, x: int, y: int) -> None:
        self.mouse_pressed = True
        self.mouse_i = (x, y)
        self.mouse_f = self.translate(x, y)

    def mouse_up(self) -> None:
        self.mouse_pressed = False

    def update(self) -> None:
        f: CoordUniform._Fun = lambda v, s: (
            v[0] + v[1] / s,
            (v[1] * 15 + v[2]) / 16,
            v[2],
        )
        z = 25 * 1.1 ** self.z[0]
        self.x = f(self.x, z)
        self.y = f(self.y, z)
        self.z = f(self.z, 2)
        if self.mouse_i is not None and self.mouse_pressed:
            self.mouse_f = self.translate(*self.mouse_i)

    def items(self) -> typing.Iterator[tuple[str, _UniformValue]]:
        yield "machuchu_x", self.x[0]
        yield "machuchu_y", self.y[0]
        yield "machuchu_z", 1.1 ** self.z[0]
        yield "machuchu_aspect", self.size[0] / self.size[1]
        yield "machuchu_click", self.mouse_pressed
        yield "machuchu_mouse", (*self.mouse_f, *self.mouse_f_start)


class GLWidget(Qt.QOpenGLWidget):
    vertexShaderData = """
        // #version 130 / #version 300 es
        in vec2 machuchu_position;
        out vec2 p;
        out vec2 machuchu_pos;

        uniform float machuchu_aspect;
        uniform float machuchu_x;
        uniform float machuchu_y;
        uniform float machuchu_z;

        void main() {
            gl_Position = vec4(machuchu_position, 0., 1.);
            machuchu_pos = machuchu_position * 0.5 + vec2(0.5);

            p = machuchu_position;
            p.x *= machuchu_aspect;
            p /= machuchu_z;
            p.x += machuchu_x;
            p.y += machuchu_y;
        }
    """

    def __init__(self, parent: Qt.QWidget | None = None) -> None:
        super().__init__(parent)
        self.program = None

        self._flip = 0
        self._fbo = None
        self._texture = None

        self.times = collections.deque([0.0], maxlen=10)
        self.coord = CoordUniform()

    def initializeGL(self) -> None:
        self._fbo = GL.glGenFramebuffers(1)
        self._texture = GL.glGenTextures(1)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._fbo)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT
        )
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT
        )
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            self._texture,
            0,
        )

    def resizeGL(self, width: int, height: int) -> None:
        GL.glViewport(0, 0, width, height)
        self.coord.size = (width, height)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            width,
            height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )

    def paintGL(self) -> None:
        if self.program is None:
            return

        GL.glBindFramebuffer(
            GL.GL_FRAMEBUFFER, self.defaultFramebufferObject()
        )
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

        if GL.glGetUniformLocation(self.program, "machuchu_tex") != -1:
            GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self._fbo)
            GL.glBlitFramebuffer(
                0,
                0,
                self.coord.size[0],
                self.coord.size[1],
                0,
                0,
                self.coord.size[0],
                self.coord.size[1],
                GL.GL_COLOR_BUFFER_BIT,
                GL.GL_NEAREST,
            )

    def getFps(self) -> float:
        return (len(self.times) - 1) / (self.times[-1] - self.times[0])

    def getUniforms(
        self,
    ) -> tuple[dict[str, int | float], dict[str, GL.Constant]]:
        self.makeCurrent()
        uniforms: dict[str, int | float] = {}
        types = {}
        count = GL.glGetProgramiv(self.program, GL.GL_ACTIVE_UNIFORMS)
        iparams = ctypes.c_int()
        fparams = ctypes.c_float()
        for i in range(count):
            name, _, type_ = GL.glGetActiveUniform(self.program, i)
            loc = GL.glGetUniformLocation(self.program, name)
            if name.startswith(b"machuchu_"):
                continue
            name = name.decode("utf-8")  # TODO: remove?
            if type_ == GL.GL_INT:
                GL.glGetUniformiv(self.program, loc, iparams)
                uniforms[name] = iparams.value
            elif type_ == GL.GL_FLOAT:
                GL.glGetUniformfv(self.program, loc, fparams)
                uniforms[name] = fparams.value
            elif type_ == GL.GL_BOOL:
                GL.glGetUniformiv(self.program, loc, iparams)
                uniforms[name] = iparams.value
            elif type_ == GL.GL_SAMPLER_2D:
                GL.glGetUniformiv(self.program, loc, iparams)
                uniforms[name] = iparams.value
            types[name] = type_
        return uniforms, types

    def setFragmentShader(self, shader: str, version: list[str]) -> None:
        self.makeCurrent()

        fragmentShader = MyGL.compileShader(shader, GL.GL_FRAGMENT_SHADER)
        if version[1:2] == ["es"]:
            vertexShader = "#version 300 es\n" + self.vertexShaderData
        else:
            vertexShader = "#version 130\n" + self.vertexShaderData
        vertexShader = MyGL.compileShader(vertexShader, GL.GL_VERTEX_SHADER)

        program = GL_shaders.compileProgram(
            vertexShader, fragmentShader, validate=False
        )

        GL.glUseProgram(program)
        self.program = program
        self.coord.size = (self.width(), self.height())
        for name, value in self.coord.items():
            self.setUniform(name, value)

        vertices = (ctypes.c_float * 8)(
            -1.0,
            -1.0,
            1.0,
            -1.0,
            -1.0,
            1.0,
            1.0,
            1.0,
        )
        attribute_pos = GL.glGetAttribLocation(
            self.program, "machuchu_position"
        )
        GL.glEnableVertexAttribArray(attribute_pos)
        GL.glVertexAttribPointer(
            attribute_pos, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, vertices
        )

        loc = GL.glGetUniformLocation(self.program, "machuchu_tex")
        if loc != -1:
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture)
            GL.glUniform1i(loc, 0)

    def setUniform(self, name: str, value: _UniformValue) -> None:
        self.makeCurrent()
        if self.program is not None:
            loc = GL.glGetUniformLocation(self.program, name)
            # TODO: coerce value to appropriate type
            if isinstance(value, float):
                GL.glUniform1f(loc, value)
            if isinstance(value, (bool, int)):
                GL.glUniform1i(loc, value)
            if isinstance(value, tuple) and len(value) == 4:
                GL.glUniform4f(loc, *value)

    def tick(self) -> None:
        self.coord.update()
        for name, value in self.coord.items():
            self.setUniform(name, value)
        self.update()
        self.times.append(time.time())


# TODO: UniformBase should inherit QWidget
class UniformBase:
    def __init__(
        self, parent: Qt.QWidget, name: str, value: _UniformValue
    ) -> None:
        self.parent = parent
        self.name = name
        self.value = value

    def init_widgets(self, widgets: list[Qt.QWidget]) -> None:
        self.widgets = widgets
        assert isinstance(self.parent, MainWindow)
        for w in widgets:
            self.parent.shaderLayout.addWidget(w)

    def _set_value(self, value: _UniformValue) -> None:
        self.value = value
        assert isinstance(self.parent, MainWindow)
        self.parent.glWidget.setUniform(self.name, self.value)

    def hide(self) -> None:
        for w in self.widgets:
            w.hide()

    def show(self) -> None:
        for w in self.widgets:
            w.show()

    def delete(self) -> None:
        for w in self.widgets:
            w.setParent(None)


class LineEditUniform(UniformBase):
    def __init__(self, parent: Qt.QWidget, name: str, value: float) -> None:
        super().__init__(parent, name, value)
        label = Qt.QLabel(name)
        edit = GentleLineEdit(str(value))

        def l(text: str) -> None:
            try:
                value = float(text)
            except ValueError:
                return
            self._set_value(value)

        edit.textChanged.connect(l)
        self.init_widgets([label, edit])

    def update(self) -> None:
        assert isinstance(self.parent, MainWindow)
        self.parent.glWidget.setUniform(self.name, self.value)


class SliderUniform(UniformBase):
    def __init__(
        self, parent: Qt.QWidget, name: str, value: int, min: int, max: int
    ) -> None:
        super().__init__(parent, name, value)
        self.slider = Qt.QSlider(Qt.Qt.Horizontal)
        self.slider.setValue(value)
        self.label = Qt.QLabel(f"{name}: {value}")
        self.update(min, max)
        self.slider.valueChanged.connect(lambda x: self._set_value(x))
        self.init_widgets([self.label, self.slider])

    def _set_value(self, x: int) -> None:
        super()._set_value(x)
        self.label.setText(f"{self.name}: {x}")

    def update(self, min: int, max: int) -> None:
        self.slider.setMinimum(min)
        self.slider.setMaximum(max)
        assert isinstance(self.parent, MainWindow)
        self.parent.glWidget.setUniform(self.name, self.value)


class CheckBoxUniform(UniformBase):
    def __init__(self, parent: Qt.QWidget, name: str, value: bool) -> None:
        super().__init__(parent, name, value)
        cbox = Qt.QCheckBox(name)
        cbox.setCheckState(Qt.Qt.Unchecked if value == 0 else Qt.Qt.Checked)
        cbox.stateChanged.connect(lambda _: self._set_value(cbox.isChecked()))
        self.init_widgets([cbox])

    def update(self) -> None:
        assert isinstance(self.parent, MainWindow)
        self.parent.glWidget.setUniform(self.name, self.value)


def format_error(prep: Preprocessor, err_text: str) -> str:
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
                    result.append(f"{prep.fnames[m_fno]}:{m_line}:\n")
                    result.append(f"{m_line:5d} | ")
                    result.append(escape(prep.fcontents[m_fno][m_line - 1]))
                except IndexError:
                    result.append(f"??? {m_fno}:{m_line}")
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
                result.append(f"({escape(m['extra'])})")
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
    def __init__(self) -> None:
        super().__init__()
        self.resize(800, 600)
        self.setWindowTitle("PyGL")
        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)
        self.shaderDock, self.shaderLayout = self.initShaderDock()
        self.addDockWidget(Qt.Qt.RightDockWidgetArea, self.shaderDock)

        self.renderDock, self.renderLayout = self.initRenderDock()
        self.addDockWidget(Qt.Qt.LeftDockWidgetArea, self.renderDock)

        self.label = Qt.QLabel()
        self.label.setParent(self.centralWidget())
        self.label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 127);
            }
            """
        )
        self.label.move(32, 32)
        self.label.setWordWrap(True)
        self.label.hide()

        # call a function on resize
        self.glWidget.resized.connect(
            lambda: self.label.resize(
                self.glWidget.width() - self.label.pos().x() * 2,
                self.glWidget.height() - self.label.pos().y() * 2,
            )
        )

        self.uniforms: dict[str, UniformBase] = {}
        self.filename: str | None = None
        self.updater: Updater | None = None

        self.timer = Qt.QTimer(self)
        self.timer.setInterval(15)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.time = time.time()
        self.time_uniform = 0.0
        self.timeron = True  # FIXME
        self.cursorLocPos = Qt.QPoint(0, 0)

    def initShaderDock(self) -> tuple[Qt.QDockWidget, Qt.QVBoxLayout]:
        shaderDock = Qt.QDockWidget()
        shaderLayout = Qt.QVBoxLayout()
        widget = Qt.QWidget()
        scrollarea = Qt.QScrollArea()

        widget.setLayout(shaderLayout)
        scrollarea.setWidgetResizable(True)
        scrollarea.setFrameShape(Qt.QFrame.NoFrame)
        scrollarea.setWidget(widget)
        shaderDock.setWidget(scrollarea)

        loadButton = Qt.QPushButton("Load")
        loadButton.clicked.connect(self.load)
        shaderLayout.addWidget(loadButton)

        shaderLayout.addStretch(0)
        shaderLayout.setContentsMargins(0, 0, 0, 0)
        shaderLayout.setSpacing(1)
        return shaderDock, shaderLayout

    def initRenderDock(self) -> tuple[Qt.QDockWidget, Qt.QVBoxLayout]:
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

    def updateUniforms(
        self,
        data: str,
        uniforms: dict[str, int | float],
        types: dict[str, GL.Constant],
    ) -> None:
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
                    self.uniforms[name] = SliderUniform(
                        self, name, value, min, max
                    )
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

    def load(self) -> None:
        # https://github.com/spyder-ide/qtpy/issues/432
        kwargs = {}
        if qtpy.PYQT5 or qtpy.PYQT6:
            kwargs = {"directory": "./shader"}
        elif qtpy.PYSIDE2 or qtpy.PYSIDE6:
            kwargs = {"dir": "./shader"}

        filename = Qt.QFileDialog.getOpenFileName(
            self, filter="Fragment shader (*.f)", **kwargs
        )
        if filename[0] != "":
            self.loadFile(filename[0])

    def reload(self) -> None:
        if self.filename:
            self.loadFile(self.filename)

    def loadFile(self, filename: str) -> None:
        self.filename = filename
        self.label.hide()
        prep = None
        try:
            prep = Preprocessor(filename)
            self.updater = Updater(prep.fnames)
            self.glWidget.setFragmentShader(prep.text, prep.version)
            uniforms, types = self.glWidget.getUniforms()
            self.updateUniforms(prep.text, uniforms, types)
        except Exception as e:
            if prep is not None and isinstance(e, MyGL.ShaderCompilationError):
                self.label.setTextFormat(Qt.Qt.RichText)
                self.label.setText(format_error(prep, e.text))
                print(e.text)
            else:
                self.label.setTextFormat(Qt.Qt.PlainText)
                self.label.setText(traceback.format_exc())
                print(traceback.format_exc())
            self.label.show()

    def tick(self) -> None:
        if self.updater and self.updater.check():
            self.reload()
        if self.timeron:
            self.time_uniform += (time.time() - self.time) * 1000
        self.glWidget.setUniform("time", self.time_uniform)
        self.time = time.time()
        self.glWidget.tick()
        self.setWindowTitle(f"{int(round(self.glWidget.getFps()))} fps")

    def timer_reset(self) -> None:
        self.time_uniform = 0.0
        self.glWidget.setUniform("time", self.time_uniform)

    def toggleShaderDock(self) -> None:
        if self.shaderDock.isVisible():
            self.shaderDock.hide()
        else:
            self.shaderDock.show()

    def toggleRenderDock(self) -> None:
        if self.renderDock.isVisible():
            self.renderDock.hide()
        else:
            self.renderDock.show()

    def keyPressEvent(self, e: Qt.QtGui.QKeyEvent) -> None:
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

    def keyReleaseEvent(self, e: Qt.QtGui.QKeyEvent) -> None:
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

    def wheelEvent(self, e: Qt.QtGui.QWheelEvent) -> None:
        d = e.angleDelta()
        if Qt.QApplication.keyboardModifiers() & Qt.Qt.ControlModifier:
            self.glWidget.coord.zoom(d.y() / 100, (e.pos().x(), e.pos().y()))
        else:
            self.glWidget.coord.move(x=-d.x(), y=d.y())

    def warpCursor(self) -> None:
        cursor = Qt.QCursor()

        def warp(value: int, max: int) -> int:
            return (value - 1) % (max - 2) + 1

        newCursorLocPos = Qt.QPoint(
            warp(self.cursorLocPos.x(), self.width()),
            warp(self.cursorLocPos.y(), self.height()),
        )
        if newCursorLocPos != self.cursorLocPos:
            cursor.setPos(cursor.pos() + newCursorLocPos - self.cursorLocPos)
            self.cursorLocPos = newCursorLocPos

    def mousePressEvent(self, e: Qt.QtGui.QMouseEvent) -> None:
        if e.buttons() == Qt.Qt.LeftButton:
            self.glWidget.coord.mouse_down(e.pos().x(), e.pos().y())
        if e.button() == Qt.Qt.MiddleButton or e.button() == Qt.Qt.RightButton:
            self.cursorLocPos = e.pos()
        grabber = self.keyboardGrabber()
        if grabber:
            grabber.releaseKeyboard()
            grabber.clearFocus()

    def mouseReleaseEvent(self, e: Qt.QtGui.QMouseEvent) -> None:
        self.glWidget.coord.mouse_up()

    def mouseMoveEvent(self, e: Qt.QtGui.QMouseEvent) -> None:
        if e.buttons() == Qt.Qt.LeftButton:
            self.glWidget.coord.mouse_move(e.pos().x(), e.pos().y())
        if (
            e.buttons() == Qt.Qt.MiddleButton
            or e.buttons() == Qt.Qt.RightButton
        ):
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
