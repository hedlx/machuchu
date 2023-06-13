from PySide2.QtCore import QTimer, QTime, QPoint, Qt
from PySide2.QtGui import QIntValidator, QCursor
from PySide2.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
    QOpenGLWidget,
)

import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtWidgets as QtWidgets

__all__ = [
    "QApplication",
    "QCheckBox",
    "QCursor",
    "QDockWidget",
    "QFileDialog",
    "QFrame",
    "QHBoxLayout",
    "QIntValidator",
    "QLabel",
    "QLineEdit",
    "QMainWindow",
    "QMessageBox",
    "QOpenGLWidget",
    "QPoint",
    "QPushButton",
    "QScrollArea",
    "QSlider",
    "QTime",
    "QTimer",
    "QVBoxLayout",
    "QWidget",
    "Qt",
    "QtCore",
    "QtGui",
    "QtWidgets",
]

# TODO: Maybe export all from PyQt5.QtCore.Qt?
#       Because Qt.Key_W is better than Qt.Qt.Key_W
