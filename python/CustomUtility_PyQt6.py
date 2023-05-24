import numpy as np
from PyQt6 import QtGui
from PyQt6 import QtWidgets
from PyQt6 import QtCore
import cv2

class WidgetDesign:

    def Layout_Widget(self, Widgets, Orientation='Vertical'):
        Layout = QtWidgets.QVBoxLayout()
        if Orientation == 'Horizontal':
            Layout = QtWidgets.QHBoxLayout()
        elif Orientation == 'Stacked':
            Layout = QtWidgets.QStackedLayout()

        try:
            for Widget_k in Widgets:
                Layout.addWidget(Widget_k)
        except TypeError:
            Layout.addWidget(Widgets)

        return Layout

    def Layout_Frame_Layout(self, UpperLayout, LowerLayout, Title):
        GroupBox = QtWidgets.QGroupBox(Title)
        GroupBox.setLayout(LowerLayout)
        UpperLayout.addWidget(GroupBox)
        del LowerLayout

    def Init_Entry(self, Entry, DefaultVal, Size=(200, 30), AlignPos=QtCore.Qt.AlignmentFlag.AlignCenter):
        Entry.setAlignment(AlignPos)
        Entry.setText(str(DefaultVal))
        Entry.setFixedSize(Size[0], Size[1])

class WidgetFunction:
    def tabClicked(self, Tab):
        Tab.BindConfigurationVariables()


class CustomFunction:

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
