"""
Laser Scanning Graphic User Interface by PyQt
"""

try:
    from AddLibraryPath import configure_path
    configure_path()
except ImportError:
    configure_path = None

import AcquisitionProcessing as AP
import AnalogInputInfo as AI
import AnalogOutputInfo as AO

import sys
import numpy as np
from PyQt6 import QtGui
from PyQt6 import QtWidgets
from PyQt6 import QtCore
import cv2

XWrite, YWrite, XRead, YRead = 'Dev1/ao1', 'Dev1/ao0', 'Dev1/ai1', 'Dev1/ai0'
Vmin, Vmax = -10, 10
dx, dy = 2, 2 # in Volt
ExposureTime = 1 # in Second


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # self.Timer = QtCore.QTimer(self)
        # self.Timer.setInterval(ExposureTime*1000)

        PageLayout = QtWidgets.QHBoxLayout()
        PreviewLayout = QtWidgets.QStackedLayout()
        ConfigLayout = QtWidgets.QVBoxLayout()
        ArrowLeftRightLayout = QtWidgets.QHBoxLayout()
        ScanFunctionLayout = QtWidgets.QHBoxLayout()
        xPositionLayout = QtWidgets.QHBoxLayout()
        yPositionLayout = QtWidgets.QHBoxLayout()
        ExpectedSpotPositionLayout = QtWidgets.QStackedLayout()

        self.initUI(PageLayout, PreviewLayout, ConfigLayout, ArrowLeftRightLayout, ScanFunctionLayout, xPositionLayout, yPositionLayout, ExpectedSpotPositionLayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(PageLayout)
        self.setCentralWidget(widget)

        self.VideoThread()
        self.AnalogInputThreadInit()
        self.AnalogOutputThreadInit()

    def VideoThread(self):

        self.Video = AP.getFrame()
        QtCore.QCoreApplication.processEvents()
        self.Video.FrameUpdate.connect(self.FrameUpdateSlot)
        self.Video.start()

    def AnalogInputThreadInit(self):

        # self.Thread2 = QtCore.QThread()
        self.AnalogInput = AI.AnalogInputInformation(AnalogInput1=XRead, AnalogInput2=YRead)
        QtCore.QCoreApplication.processEvents()
        self.AnalogInput.LabelInfo.connect(self.UpdateAnalogInputLabel)
        self.AnalogInput.FigureInfo.connect(self.UpdateAnalogInputFigure)
        # self.AnalogInput.moveToThread(self.Thread2)
        # self.AnalogInput.Finished.connect(self.Thread2.quit)
        # self.Thread2.started.connect(self.AnalogInput.run)
        self.AnalogInput.start()

    def AnalogOutputThreadInit(self):
        self.AnalogOutput = AO.AnalogOutputInformation(AnalogOutput1=XWrite, AnalogOutput2=YWrite, dx=dx, dy=dy, Vmin=Vmin, Vmax=Vmax, ExposureTime=ExposureTime)
        self.AnalogOutput.start()

    def UpdateAnalogInputLabel(self, AnalogInput):

        x = np.round(2 * AnalogInput[0], 2)
        y = np.round(2 * AnalogInput[1], 2)
        self.x_Position_Label.setText(f"{x}" + u' \N{DEGREE SIGN}')
        self.y_Position_Label.setText(f"{y}" + u' \N{DEGREE SIGN}')
        self.x_Position_Label.repaint()

    def UpdateAnalogInputFigure(self, AnalogInput):

        qtImage = self.cv2qt(np.flip(AnalogInput, axis=0))
        self.ExpectedSpotLabel.setPixmap(qtImage)

    def FrameUpdateSlot(self, Image):
        qtImage = self.cv2qt(Image)
        self.PreviewLabel.setPixmap(qtImage)

    def initUI(self, PageLayout, PreviewLayout, ConfigLayout, ArrowLeftRightLayout, ScanFunctionLayout, xPositionLayout, yPositionLayout, ExpectedSpotPositionLayout):

        PageLayout.addLayout(PreviewLayout)
        PageLayout.addLayout(ConfigLayout)

        self.UI_Preview_Component(PreviewLayout)
        self.UI_Configure_Component(ConfigLayout, ArrowLeftRightLayout, ScanFunctionLayout, xPositionLayout, yPositionLayout, ExpectedSpotPositionLayout)

    def UI_Preview_Component(self, PreviewLayout):

        self.PreviewLabel = QtWidgets.QLabel()
        PreviewLayout.addWidget(self.PreviewLabel)

    def UI_Configure_Component(self, ConfigLayout, ArrowLeftRightLayout, ScanFunctionLayout, xPositionLayout, yPositionLayout, ExpectedSpotPositionLayout):

        self.Up_Button = QtWidgets.QToolButton()
        self.Up_Button.setArrowType(QtCore.Qt.ArrowType.UpArrow)
        self.Up_Button.setFixedSize(150, 40)
        self.Up_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("UP"))
        QtWidgets.QAbstractButton.setAutoRepeat(self.Up_Button, True)

        self.Left_Button = QtWidgets.QToolButton()
        self.Left_Button.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
        self.Left_Button.setFixedSize(150, 40)
        self.Left_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("LEFT"))
        QtWidgets.QAbstractButton.setAutoRepeat(self.Left_Button, True)

        self.Right_Button = QtWidgets.QToolButton()
        self.Right_Button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.Right_Button.setFixedSize(150, 40)
        self.Right_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("RIGHT"))
        QtWidgets.QAbstractButton.setAutoRepeat(self.Right_Button, True)

        self.Down_Button = QtWidgets.QToolButton()
        self.Down_Button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        self.Down_Button.setFixedSize(150, 40)
        self.Down_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("DOWN"))
        QtWidgets.QAbstractButton.setAutoRepeat(self.Down_Button, True)

        self.RasterScan_Button = QtWidgets.QPushButton("Raster Scanning")
        self.RasterScan_Button.setFixedSize(150, 40)
        self.RasterScan_Button.clicked.connect(lambda checked=False: self.AnalogOutput.RasterScan())

        self.Initialization_Button = QtWidgets.QPushButton("Initialization")
        self.Initialization_Button.setFixedSize(150, 40)
        self.Initialization_Button.clicked.connect(lambda checked=False: self.AnalogOutput.Initialization())

        self.x_Label = QtWidgets.QLabel("x Position:")
        self.x_Label.setFixedSize(180, 40)
        self.x_Position_Label = QtWidgets.QLabel()
        self.x_Position_Label.setFixedSize(120, 40)

        self.y_Label = QtWidgets.QLabel("y Position:")
        self.y_Label.setFixedSize(180, 40)
        self.y_Position_Label = QtWidgets.QLabel()
        self.y_Position_Label.setFixedSize(120, 40)

        self.ExpectedSpotLabel = QtWidgets.QLabel()

        ConfigLayout.addWidget(self.Up_Button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.EmbedLayoutIncludingWidget(ConfigLayout, ArrowLeftRightLayout, (self.Left_Button, self.Right_Button))
        ConfigLayout.addWidget(self.Down_Button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.EmbedLayoutIncludingWidget(ConfigLayout, ScanFunctionLayout, (self.RasterScan_Button, self.Initialization_Button))
        self.EmbedLayoutIncludingWidget(ConfigLayout, xPositionLayout, (self.x_Label, self.x_Position_Label))
        self.EmbedLayoutIncludingWidget(ConfigLayout, yPositionLayout, (self.y_Label, self.y_Position_Label))
        self.EmbedLayoutIncludingWidget(ConfigLayout, ExpectedSpotPositionLayout, self.ExpectedSpotLabel)

    def EmbedLayoutIncludingWidget(self, L1, L2, Widgets):

        try:
            for Widget_k in Widgets:
                L2.addWidget(Widget_k)

        except TypeError:
            L2.addWidget(Widgets)

        L1.addLayout(L2)

    def cv2qt(self, cvimage):
        """Convert from an opencv image to QPixmap"""
        cvimage = cv2.resize(cvimage, dsize=(0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        rgb_image = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        p = convert_to_Qt_format
        # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)

    def closeEvent(self, event):
        tasks = (self.AnalogOutput.TaskWriteX, self.AnalogOutput.TaskWriteY, self.AnalogInput.TaskReadX, self.AnalogInput.TaskReadY)
        for task in tasks:
            task.close()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

