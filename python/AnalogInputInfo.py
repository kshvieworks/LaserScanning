"Scanning Position Information Processing with Independent Thread"

import numpy as np
import nidaqmx
from PyQt6 import QtCore

import cv2
from PyQt6 import QtGui


class AnalogInputInformation(QtCore.QThread):
    LabelInfo = QtCore.pyqtSignal(np.ndarray)
    FigureInfo = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None, AnalogInput1 = "Dev1/ai1", AnalogInput2 = "Dev1/ai0"):
        QtCore.QThread.__init__(self)
        self.TaskReadX, self.TaskReadY = nidaqmx.Task(), nidaqmx.Task()
        self.TaskReadX.ai_channels.add_ai_voltage_chan(f"{AnalogInput1}")
        self.TaskReadY.ai_channels.add_ai_voltage_chan(f"{AnalogInput2}")

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            CurrentPosition = np.array([self.TaskReadX.read(), self.TaskReadY.read()])
            self.LabelInfo.emit(CurrentPosition)
            self.FigureInfo.emit(self.ExpectedSpotPositionFigure(CurrentPosition[0], CurrentPosition[1]))

    def ExpectedSpotPositionFigure(self, x=0, y=0, width=800, height=600):
        x = int(28 * x + width / 2)
        y = int(28 * y + height / 2)
        xx, yy = int(max(width, height) / 40), int(max(width, height) / 40)

        ExpectedSpotImage = np.zeros([height, width, 1], dtype=np.uint8)
        ExpectedSpotImage.fill(255)

        ExpectedSpotImage[y, x - xx:x + xx + 1] = 0
        ExpectedSpotImage[y - yy:y + yy + 1, x] = 0

        return ExpectedSpotImage

