"Scanning Position Controlling Processing with Independent Thread"

import numpy as np
import time
import nidaqmx
from operator import itemgetter
from PyQt6 import QtCore, QtTest

DefaultValue = {'xVmin': -10, 'xVmax': 10, 'nX': 10, 'yVmin': -10, 'yVmax': 10, 'nY': 10, 'dt': 1,
                 'XWrite': 'Dev1/ao0', 'YWrite': 'Dev1/ao1', 'XRead': 'Dev1/ai0', 'YRead': 'Dev1/ai1'}


class DAQControl:

    def __init__(self, parent=None, Infos=DefaultValue):
        # QtCore.QThread.__init__(self)

        self.V1min, self.V1max, self.n1, self.V2min, self.V2max, self.n2, self.dt, self.AO1, self.AO2\
            = itemgetter('xVmin', 'xVmax', 'nX', 'yVmin', 'yVmax', 'nY', 'dt', 'XWrite', 'YWrite')(Infos)

        self.V1, self.V2 = 0, 0
        self.DAQInit(self.AO1, self.AO2, self.V1min, self.V1max, self.n1, self.V2min, self.V2max, self.n2)

    def DAQInit(self, Dev1, Dev2, From1, to1, N1, From2, to2, N2):

        self.d1 = (to1 - From1)/(N1-1)
        self.d2 = (to2 - From2)/(N2-1)

        self.Task1Write, self.Task2Write = nidaqmx.Task(), nidaqmx.Task()
        self.Task1Write.ao_channels.add_ao_voltage_chan(f"{Dev1}", "", From1, to1)
        self.Task2Write.ao_channels.add_ao_voltage_chan(f"{Dev2}", "", From2, to2)
        self.Task1Write.start(), self.Task2Write.start()

    def UpdateDAQ(self, Task1, Task2, Val1, Val2):
        Task1.write(Val1)
        Task2.write(Val2)
    def UpdateInfo(self, Infos):
        self.V1min, self.V1max, self.n1, self.V2min, self.V2max, self.n2, self.dt, self.AO1, self.AO2\
            = itemgetter('xVmin', 'xVmax', 'nX', 'yVmin', 'yVmax', 'nY', 'dt', 'XWrite', 'YWrite')(Infos)
    def SetCurrentValue(self, V1, V2):
        self.V1 = V1
        self.V2 = V2
    def Init_CurrentValue(self):
        self.SetCurrentValue(0, 0)

    def GetCurrentValue(self):
        return self.V1, self.V2

class Scanning(QtCore.QThread):
    def __init__(self, parent=None, Infos=DefaultValue):
        QtCore.QThread.__init__(self)
        self.DAQ = DAQControl(Infos)
        self.ScanningLib = ScanFunction()

    def Initialization(self):
        self.DAQ.Init_CurrentValue()
        self.DAQ.UpdateDAQ(self.DAQ.Task1Write, self.DAQ.Task2Write, self.DAQ.V1, self.DAQ.V2)

    def UpdateDAQInfo(self, Infos):
        del self.DAQ
        self.DAQ = DAQControl(Infos)

    def ManualScan(self, direction):
        V1 = self.DAQ.GetCurrentValue()[0] - self.DAQ.d1 if direction == "UP" else self.DAQ.GetCurrentValue()[0] + self.DAQ.d1 if direction == "DOWN" else self.DAQ.GetCurrentValue()[0]
        V2 = self.DAQ.GetCurrentValue()[1] - self.DAQ.d2 if direction == "LEFT" else self.DAQ.GetCurrentValue()[1] + self.DAQ.d2 if direction == "RIGHT" else self.DAQ.GetCurrentValue()[1]

        V1 = self.DAQ.V1min if V1 < self.DAQ.V1min else self.DAQ.V1max if V1 > self.DAQ.V1max else V1
        V2 = self.DAQ.V2min if V2 < self.DAQ.V2min else self.DAQ.V2max if V2 > self.DAQ.V2max else V2

        self.DAQ.SetCurrentValue(V1, V2)
        self.DAQ.UpdateDAQ(self.DAQ.Task1Write, self.DAQ.Task2Write, self.DAQ.V1, self.DAQ.V2)

    def Pause(self):

        self.ScanningLib.PauseScan()

        if not self.DAQ.Task1Write.is_task_done():
            self.DAQ.Task1Write.stop()

        if not self.DAQ.Task2Write.is_task_done():
            self.DAQ.Task2Write.stop()

    def run(self):
        self.ScanningLib.RedoScan()
        self.ScanningLib.RasterScan(self.DAQ)
        if self.ScanningLib.ScanState == 'Finished':
            self.Initialization()


class ScanFunction:
    def __init__(self):
        self.ThreadActive = True
        self.ScanState = 'Finished'

    def RasterScan(self, DAQ):
        QtCore.QCoreApplication.processEvents()

        V1, V2 = DAQ.V1min, DAQ.V2min if self.ScanState == 'Finished' else DAQ.GetCurrentValue()

        while (self.ThreadActive == True and V1 <= DAQ.V1max):
            # DAQ.SetCurrentValue(V1, V2)
            while (self.ThreadActive == True and V2 <= DAQ.V2max):
                DAQ.SetCurrentValue(V1, V2)
                DAQ.UpdateDAQ(DAQ.Task1Write, DAQ.Task2Write, DAQ.V1, DAQ.V2)
                QtTest.QTest.qWait(int(1000*DAQ.dt))
                V2 = DAQ.GetCurrentValue()[1] + DAQ.d2

            V1, V2 = DAQ.GetCurrentValue()[0] + DAQ.d1, DAQ.V2min

        if self.ThreadActive == True:
            self.FinishScan()

    def PauseScan(self):
        self.ThreadActive = False
        self.ScanState = 'Pending'

    def RedoScan(self):
        self.ThreadActive = True

    def FinishScan(self):
        self.ScanState = 'Finished'
