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

import CustomUtility_PyQt6 as util
import sys
import numpy as np
from PyQt6 import QtGui
from PyQt6 import QtWidgets
from PyQt6 import QtCore
import cv2
from operator import itemgetter

ConfigurationVariables = {'xVmin': -10, 'xVmax': 10, 'nX': 10, 'yVmin': -10, 'yVmax': 10, 'nY': 10, 'dt': 1,
                          'XWrite': 'Dev1/ao0', 'YWrite': 'Dev1/ao1', 'XRead': 'Dev1/ai0', 'YRead': 'Dev1/ai1'}

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.window = MainWindow(self)
        self.setCentralWidget(self.window)
        self.setWindowTitle("LaserScanning")
        self.show()

    def closeEvent(self, event):
        self.window.Preview.Video.Camera.image_acquisition_thread.stop()
        self.window.Preview.Video.Camera.image_acquisition_thread._mono_to_color_sdk.dispose()
        self.window.Preview.Video.Camera.image_acquisition_thread._mono_to_color_processor.dispose()
        del self.window.Preview.Video
        del self.window.GeneralTab


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent):
        super(MainWindow, self).__init__(parent)
    # Import Utility
        self.FuncUtil = util.WidgetFunction()
        self.CustomFunction = util.CustomFunction()

    # Define Layout
        PageLayout = QtWidgets.QHBoxLayout()
        PreviewLayout = QtWidgets.QVBoxLayout()
        ConfigLayout = QtWidgets.QVBoxLayout()

        self.init_Layout(PageLayout, PreviewLayout, ConfigLayout)
        self.setLayout(PageLayout)

    def init_Layout(self, PageLayout, PreviewLayout, ConfigLayout):
        PageLayout.addLayout(PreviewLayout)
        PageLayout.addLayout(ConfigLayout)

        self.init_Preview(PreviewLayout)
        self.init_ConfigureTab(ConfigLayout)

    # Define Configuration Tab Define
    def init_Preview(self, PreviewLayout):
        self.Preview = PreviewWidget()
        PreviewLayout.addWidget(self.Preview)

    def init_ConfigureTab(self, ConfigLayout):
        self.TabHolder = QtWidgets.QTabWidget()
        self.GeneralTab = GeneralWidget()
        ConfigureTab = ConfigurationWidget()
        DeviceConnectionTab = DeviceConnectionWidget()
        self.TabHolder.addTab(self.GeneralTab, "Laser Scan")
        self.TabHolder.addTab(ConfigureTab, "Configuration")
        self.TabHolder.addTab(DeviceConnectionTab, "Device")
        ConfigLayout.addWidget(self.TabHolder)

        self.TabHolder.tabBarClicked.connect(lambda checked=False: self.FuncUtil.tabClicked(ConfigureTab))
        ConfigureTab.VarList.connect(self.UpdateConfigureVariable)
        self.TabHolder.tabBarClicked.connect(lambda checked=False: self.FuncUtil.tabClicked(DeviceConnectionTab))
        DeviceConnectionTab.VarList.connect(self.UpdateConfigureVariable)

        self.TabHolder.tabBarClicked.connect(lambda checked=False: self.UpdateDAQInfo(ConfigurationVariables))

    def UpdateConfigureVariable(self, VarList):
        for k in VarList:
            ConfigurationVariables[k] = VarList[k]

    def UpdateDAQInfo(self, Infos):
        self.GeneralTab.AnalogOutput.UpdateDAQInfo(Infos)


class PreviewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(PreviewWidget, self).__init__(parent)

        self.DesignUtil = util.WidgetDesign()
        self.CustomFunction = util.CustomFunction()

        PreviewLayout = QtWidgets.QVBoxLayout()

        self.initUI(PreviewLayout)
        self.setLayout(PreviewLayout)

        self.VideoThread()

    def initUI(self, Layout):

        self.UI_Component()
        self.UI_Layout(Layout)
        self.EventProcess()

    def UI_Layout(self, Layout):
        PreviewStackLayout = QtWidgets.QStackedLayout()
        PreviewStackLayout.addWidget(self.PreviewLabel)
        Layout.addLayout(PreviewStackLayout)
        Layout.addWidget(self.PauseResume_Button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

    def UI_Component(self):

        self.PreviewLabel = QtWidgets.QLabel()

        self.PauseResume_Button = QtWidgets.QPushButton()
        self.PauseResume_Button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
        self.PauseResume_Button.setFixedSize(100, 40)

        # self.PauseResume_Button.clicked.connect(lambda checked=False: self.AOAutoScanActiveControl())
    def EventProcess(self):
        self.PauseResume_Button.clicked.connect(lambda checked=False: self.VideoActiveControl(self.PauseResume_Button))

    def VideoThread(self):
        self.Video = AP.getFrame()
        QtCore.QCoreApplication.processEvents()
        self.Video.FrameUpdate.connect(self.FrameUpdateSlot)
        self.Video.start()

    def FrameUpdateSlot(self, Image):
        qtImage = self.CustomFunction.cv2qt(Image)
        self.PreviewLabel.setPixmap(qtImage)

    def VideoActiveControl(self, BTN):
        if self.Video.ThreadActive == False:
            BTN.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
            self.Video.ThreadActive = True
            self.Video.start()
        else:
            BTN.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
            self.Video.ThreadActive = False
            # self.AOAutoScanStatus = False


class GeneralWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GeneralWidget, self).__init__(parent)

        self.DesignUtil = util.WidgetDesign()
        self.CustomFunction = util.CustomFunction()

        Layout = QtWidgets.QVBoxLayout()

        self.initUI(Layout)
        self.setLayout(Layout)

        self.AnalogInputThreadInit()
        self.AnalogOutputThreadInit()

    def initUI(self, Layout):

        self.UI_Component()
        self.UI_Layout(Layout)
        self.EventProcess()

    def UI_Layout(self, Layout):

        Layout.addWidget(self.Up_Button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        Layout.addLayout(self.DesignUtil.Layout_Widget((self.Left_Button, self.Right_Button), 'Horizontal'))
        Layout.addWidget(self.Down_Button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        Layout.addLayout(self.DesignUtil.Layout_Widget((self.RasterScan_Button, self.PauseResume_Button, self.Initialization_Button), 'Horizontal'))
        Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_Label, self.x_Position_Label), 'Horizontal'))
        Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_Label, self.y_Position_Label), 'Horizontal'))

        Layout.addLayout(self.DesignUtil.Layout_Widget(self.ExpectedSpotLabel, 'Stacked'))

    def UI_Component(self):

        self.Up_Button = QtWidgets.QToolButton()
        self.Up_Button.setArrowType(QtCore.Qt.ArrowType.UpArrow)
        self.Up_Button.setFixedSize(150, 40)
        QtWidgets.QAbstractButton.setAutoRepeat(self.Up_Button, True)

        self.Left_Button = QtWidgets.QToolButton()
        self.Left_Button.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
        self.Left_Button.setFixedSize(150, 40)
        QtWidgets.QAbstractButton.setAutoRepeat(self.Left_Button, True)

        self.Right_Button = QtWidgets.QToolButton()
        self.Right_Button.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        self.Right_Button.setFixedSize(150, 40)
        QtWidgets.QAbstractButton.setAutoRepeat(self.Right_Button, True)

        self.Down_Button = QtWidgets.QToolButton()
        self.Down_Button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        self.Down_Button.setFixedSize(150, 40)
        QtWidgets.QAbstractButton.setAutoRepeat(self.Down_Button, True)

        self.RasterScan_Button = QtWidgets.QPushButton("Raster Scanning")
        self.RasterScan_Button.setFixedSize(100, 40)

        self.PauseResume_Button = QtWidgets.QPushButton()
        self.PauseResume_Button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
        self.PauseResume_Button.setFixedSize(100, 40)

        self.Initialization_Button = QtWidgets.QPushButton("Initialization")
        self.Initialization_Button.setFixedSize(100, 40)

        self.x_Label = QtWidgets.QLabel("x Position:")
        self.x_Label.setFixedSize(180, 40)
        self.x_Position_Label = QtWidgets.QLabel()
        self.x_Position_Label.setFixedSize(120, 40)

        self.y_Label = QtWidgets.QLabel("y Position:")
        self.y_Label.setFixedSize(180, 40)
        self.y_Position_Label = QtWidgets.QLabel()
        self.y_Position_Label.setFixedSize(120, 40)

        self.ExpectedSpotLabel = QtWidgets.QLabel()

    def EventProcess(self):
        self.Up_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("UP"))
        self.Left_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("LEFT"))
        self.Right_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("RIGHT"))
        self.Down_Button.clicked.connect(lambda checked=False: self.AnalogOutput.ManualScan("DOWN"))
        self.RasterScan_Button.clicked.connect(lambda checked=False: self.AnalogOutput.start())
        self.Initialization_Button.clicked.connect(lambda checked=False: self.AnalogOutput.Initialization())
        self.PauseResume_Button.clicked.connect(lambda checked=False: self.AutoScanActiveControl(self.PauseResume_Button))

    def AutoScanActiveControl(self, BTN):
        if self.AnalogOutput.ScanningLib.ThreadActive == False:
            BTN.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause))
            self.AnalogOutput.start()
        else:
            BTN.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
            self.AnalogOutput.Pause()

    def AnalogInputThreadInit(self):

        # self.Thread2 = QtCore.QThread()
        self.AnalogInput = AI.AnalogInputInformation(AnalogInput1=ConfigurationVariables['XRead'],
                                                     AnalogInput2=ConfigurationVariables['YRead'])
        QtCore.QCoreApplication.processEvents()
        self.AnalogInput.LabelInfo.connect(self.UpdateAnalogInputLabel)
        self.AnalogInput.FigureInfo.connect(self.UpdateAnalogInputFigure)
        # self.AnalogInput.moveToThread(self.Thread2)
        # self.AnalogInput.Finished.connect(self.Thread2.quit)
        # self.Thread2.started.connect(self.AnalogInput.run)
        self.AnalogInput.start()

    def AnalogOutputThreadInit(self):
        self.AnalogOutput = AO.Scanning()

    def UpdateAnalogInputLabel(self, AnalogInput):

        x = np.round(2 * AnalogInput[0], 2)
        y = np.round(2 * AnalogInput[1], 2)
        self.x_Position_Label.setText(f"{x}" + u' \N{DEGREE SIGN}')
        self.y_Position_Label.setText(f"{y}" + u' \N{DEGREE SIGN}')
        self.x_Position_Label.repaint()

    def UpdateAnalogInputFigure(self, AnalogInput):
        qtImage = self.CustomFunction.cv2qt(np.flip(AnalogInput, axis=0))
        self.ExpectedSpotLabel.setPixmap(qtImage)


class ConfigurationWidget(QtWidgets.QWidget):
    VarList = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ConfigurationWidget, self).__init__(parent)

        self.DesignUtil = util.WidgetDesign()

        ConfigLayout = QtWidgets.QVBoxLayout()

        self.initUI(ConfigLayout)
        self.setLayout(ConfigLayout)

    def BindConfigurationVariables(self):
        Vars = {'xVmin': float(self.x_Vmin_Entry.text()),
                'xVmax': float(self.x_Vmax_Entry.text()),
                'nX': float(self.x_TotalStep_Entry.text()),
                'yVmin': float(self.y_Vmin_Entry.text()),
                'yVmax': float(self.y_Vmax_Entry.text()),
                'nY': float(self.y_TotalStep_Entry.text()),
                'dt': float(self.TimeStep_Entry.text())}

        self.VarList.emit(Vars)

    def initUI(self, Layout):
        self.UI_Component()
        self.UI_Layout(Layout)

    def UI_Layout(self, Layout):

        Mid_Layout = QtWidgets.QVBoxLayout()
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_Vmin_Label, self.x_Vmin_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_Vmax_Label, self.x_Vmax_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_TotalStep_Label, self.x_TotalStep_Entry), 'Horizontal'))
        self.DesignUtil.Layout_Frame_Layout(Layout, Mid_Layout, 'x-Axis Configuration')

        Mid_Layout = QtWidgets.QVBoxLayout()
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_Vmin_Label, self.y_Vmin_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_Vmax_Label, self.y_Vmax_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_TotalStep_Label, self.y_TotalStep_Entry), 'Horizontal'))
        self.DesignUtil.Layout_Frame_Layout(Layout, Mid_Layout, 'y-Axis Configuration')

        Mid_Layout = QtWidgets.QVBoxLayout()
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.TimeStep_Label, self.TimeStep_Entry), 'Horizontal'))
        self.DesignUtil.Layout_Frame_Layout(Layout, Mid_Layout, 'Time Step Configuration')

    def UI_Component(self):

        LabelSize = (150, 30)
        EntrySize = (200, 30)

        self.x_Vmin_Label = QtWidgets.QLabel("Vmin [V]")
        self.x_Vmin_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.x_Vmin_Entry = QtWidgets.QLineEdit(placeholderText='Avaliable Minimum Voltage: -10V', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.x_Vmin_Entry, str(ConfigurationVariables['xVmin']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.x_Vmax_Label = QtWidgets.QLabel("Vmax [V]")
        self.x_Vmax_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.x_Vmax_Entry = QtWidgets.QLineEdit(placeholderText='Avaliable Maximum Voltage: 10V', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.x_Vmax_Entry, str(ConfigurationVariables['xVmax']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.x_TotalStep_Label = QtWidgets.QLabel("# of Steps")
        self.x_TotalStep_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.x_TotalStep_Entry = QtWidgets.QLineEdit(clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.x_TotalStep_Entry, str(ConfigurationVariables['nX']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.y_Vmin_Label = QtWidgets.QLabel("Vmin [V]")
        self.y_Vmin_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.y_Vmin_Entry = QtWidgets.QLineEdit(placeholderText='Avaliable Minimum Voltage: -10V', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.y_Vmin_Entry, str(ConfigurationVariables['yVmin']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.y_Vmax_Label = QtWidgets.QLabel("Vmax [V]")
        self.y_Vmax_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.y_Vmax_Entry = QtWidgets.QLineEdit(placeholderText='Avaliable Maximum Voltage: 10V', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.y_Vmax_Entry, str(ConfigurationVariables['yVmax']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.y_TotalStep_Label = QtWidgets.QLabel("# of Steps")
        self.y_TotalStep_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.y_TotalStep_Entry = QtWidgets.QLineEdit(clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.y_TotalStep_Entry, str(ConfigurationVariables['nY']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.TimeStep_Label = QtWidgets.QLabel("Time Step [s]")
        self.TimeStep_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.TimeStep_Entry = QtWidgets.QLineEdit(clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.TimeStep_Entry, str(ConfigurationVariables['dt']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)


class DeviceConnectionWidget(QtWidgets.QWidget):
    VarList = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(DeviceConnectionWidget, self).__init__(parent)

        self.DesignUtil = util.WidgetDesign()

        ConfigLayout = QtWidgets.QVBoxLayout()

        self.initUI(ConfigLayout)
        self.setLayout(ConfigLayout)

    def BindConfigurationVariables(self):
        Vars = {'XRead': self.x_Input_Entry.text(),
                'XWrite': self.x_Output_Entry.text(),
                'YRead': self.y_Input_Entry.text(),
                'YWrite': self.y_Output_Entry.text()}

        self.VarList.emit(Vars)

    def initUI(self, ConfigLayout):
        self.UI_Component()
        self.UI_Layout(ConfigLayout)

    def UI_Layout(self, ConfigLayout):

        Mid_Layout = QtWidgets.QVBoxLayout()
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_Input_Label, self.x_Input_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.x_Output_Label, self.x_Output_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_Input_Label, self.y_Input_Entry), 'Horizontal'))
        Mid_Layout.addLayout(self.DesignUtil.Layout_Widget((self.y_Output_Label, self.y_Output_Entry), 'Horizontal'))
        self.DesignUtil.Layout_Frame_Layout(ConfigLayout, Mid_Layout, 'Device Connection Configuration')

    def UI_Component(self):

        LabelSize = (150, 30)
        EntrySize = (200, 30)

        self.x_Input_Label = QtWidgets.QLabel("x-Axis Input Port")
        self.x_Input_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.x_Input_Entry = QtWidgets.QLineEdit(placeholderText=f'Monitoring Signal Connected to ...', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.x_Input_Entry, str(ConfigurationVariables['XRead']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.x_Output_Label = QtWidgets.QLabel("x-Axis Output Port")
        self.x_Output_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.x_Output_Entry = QtWidgets.QLineEdit(placeholderText='Applying Signal Connected to ...', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.x_Output_Entry, str(ConfigurationVariables['XWrite']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.y_Input_Label = QtWidgets.QLabel("y-Axis Input Port")
        self.y_Input_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.y_Input_Entry = QtWidgets.QLineEdit(placeholderText='Monitoring Signal Connected to ...', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.y_Input_Entry, str(ConfigurationVariables['YRead']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)

        self.y_Output_Label = QtWidgets.QLabel("y-Axis Output Port")
        self.y_Output_Label.setFixedSize(LabelSize[0], LabelSize[1])
        self.y_Output_Entry = QtWidgets.QLineEdit(placeholderText='Applying Signal Connected to ...', clearButtonEnabled=True)
        self.DesignUtil.Init_Entry(self.y_Output_Entry, str(ConfigurationVariables['YWrite']), EntrySize, QtCore.Qt.AlignmentFlag.AlignRight)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    window = App()
    app.exec()

