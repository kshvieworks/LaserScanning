"Scanning Position Controlling Processing with Independent Thread"

import numpy as np
import time
import nidaqmx
from PyQt6 import QtCore, QtTest


class AnalogOutputInformation(QtCore.QThread):

    def __init__(self, parent=None, AnalogOutput1 = "Dev1/ao1", AnalogOutput2 = "Dev1/ao0", dx=2, dy=2, Vmin=-10, Vmax=10, ExposureTime=1):
        QtCore.QThread.__init__(self)
        self.dx, self.dy, self.Vmin, self.Vmax, self.ExposureTime = dx, dy, Vmin, Vmax, ExposureTime
        self.DAQInit(AnalogOutput1, AnalogOutput2)

        self.Vx, self.Vy = 0, 0
        self.xBufferSize, self.yBufferSize = (Vmax - Vmin) / dx + 1, (Vmax - Vmin) / dy + 1
        self.FramePerSecond = 1 / (self.ExposureTime * self.xBufferSize * self.yBufferSize)  # in Hertz

    def DAQInit(self, XW, YW):

        self.TaskWriteX, self.TaskWriteY = nidaqmx.Task(), nidaqmx.Task()
        self.TaskWriteX.ao_channels.add_ao_voltage_chan(f"{XW}", "", self.Vmin, self.Vmax)
        self.TaskWriteY.ao_channels.add_ao_voltage_chan(f"{YW}", "", self.Vmin, self.Vmax)
        self.TaskWriteX.start(), self.TaskWriteY.start()

    def UpdateDAQ(self, TaskX, TaskY, XValue, YValue):

        TaskX.write(XValue)
        TaskY.write(YValue)

    def Initialization(self):

        self.Vy = 0
        self.Vx = 0
        self.UpdateDAQ(self.TaskWriteX, self.TaskWriteY, self.Vx, self.Vy)

    def ManualScan(self, direction):

        self.Vy = self.Vy + self.dy if direction == "UP" else self.Vy - self.dy if direction == "DOWN" else self.Vy
        self.Vx = self.Vx - self.dx if direction == "LEFT" else self.Vx + self.dx if direction == "RIGHT" else self.Vx

        self.UpdateDAQ(self.TaskWriteX, self.TaskWriteY, self.Vx, self.Vy)

    def RasterScan(self):
        if not self.TaskWriteX.is_task_done():
            self.TaskWriteX.stop()
        if not self.TaskWriteY.is_task_done():
            self.TaskWriteY.stop()

        for k in np.linspace(self.Vmin, self.Vmax, int(self.yBufferSize)):
            QtCore.QCoreApplication.processEvents()
            self.Vy = k

            for j in np.linspace(self.Vmin, self.Vmax, int(self.xBufferSize)):
                # QtCore.QCoreApplication.processEvents()
                self.Vx = j

                self.UpdateDAQ(self.TaskWriteX, self.TaskWriteY, self.Vx, self.Vy)
                QtTest.QTest.qWait(1000*self.ExposureTime)

    def run(self):
        pass
