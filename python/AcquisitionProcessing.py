"""
Camera Acquisition Processing
"""
import threading
import queue
import sys
import numpy as np
import cv2
# import pytictoc
from PIL import Image
from PyQt6 import QtCore

# Add Thorlabs Scientific Camera Interface Library
try:
    from AddLibraryPath import configure_path
    configure_path()
except ImportError:
    configure_path = None

# Find Available Thorlabs Cameras
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK


class ImageAcquisitionThread(threading.Thread):

    def __init__(self, camera):
        # type: (TLCamera) -> ImageAcquisitionThread
        super(ImageAcquisitionThread, self).__init__()
        self._camera = camera
        self._previous_timestamp = 0

        # setup color processing if necessary
        if self._camera.camera_sensor_type != SENSOR_TYPE.BAYER:
            # Sensor type is not compatible with the color processing library
            self._is_color = False
        else:
            self._mono_to_color_sdk = MonoToColorProcessorSDK()
            self._image_width = self._camera.image_width_pixels
            self._image_height = self._camera.image_height_pixels
            self._mono_to_color_processor = self._mono_to_color_sdk.create_mono_to_color_processor(
                SENSOR_TYPE.BAYER,
                self._camera.color_filter_array_phase,
                self._camera.get_color_correction_matrix(),
                self._camera.get_default_white_balance_matrix(),
                self._camera.bit_depth
            )
            self._is_color = True

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 0  # Do not want to block for long periods of time
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()

    def get_output_queue(self):
        # type: (type(None)) -> queue.Queue
        return self._image_queue

    def stop(self):
        self._stop_event.set()

    def _get_color_image(self, frame):
        # type: (Frame) -> Image
        # verify the image size
        width = frame.image_buffer.shape[1]
        height = frame.image_buffer.shape[0]
        if (width != self._image_width) or (height != self._image_height):
            self._image_width = width
            self._image_height = height
            print("Image dimension change detected, image acquisition thread was updated")
        # color the image. transform_to_24 will scale to 8 bits per channel
        color_image_data = self._mono_to_color_processor.transform_to_24(frame.image_buffer,
                                                                         self._image_width,
                                                                         self._image_height)
        color_image_data = color_image_data.reshape(self._image_height, self._image_width, 3)
        # return PIL Image object
        return Image.fromarray(color_image_data, mode='RGB')

    def _get_image(self, frame):
        # type: (Frame) -> Image
        # no coloring, just scale down image to 8 bpp and place into PIL Image object
        scaled_image = frame.image_buffer >> (self._bit_depth - 8)
        return Image.fromarray(scaled_image)

    def run(self):
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    if self._is_color:
                        pil_image = self._get_color_image(frame)
                    else:
                        pil_image = self._get_image(frame)
                    self._image_queue.put_nowait(pil_image)
            except queue.Full:
                # No point in keeping this image around when the queue is full, let's skip to the next one
                pass
            except Exception as error:
                print("Encountered error: {error}, image acquisition will stop.".format(error=error))
                break
        print("Image acquisition has stopped")
        if self._is_color:
            self._mono_to_color_processor.dispose()
            self._mono_to_color_sdk.dispose()


class ImageAcquisition:
    def __init__(self, sdk):
        self.sdk = sdk
        self.CameraOpen()
        self.CameraInit()
        # self.FigureOpen()
        # self.t = pytictoc.TicToc()
        # self.t.tic()
        self.FrameAcquisition()


    def CameraOpen(self):
        self.camera_list = self.sdk.discover_available_cameras()
        if len(self.camera_list) < 1:
            print("No Camera Detected")
            sys.exit()

        self.camera = self.sdk.open_camera(self.camera_list[0])
        print(f"{self.camera_list[0]} Camera Open")

        self.image_acquisition_thread = ImageAcquisitionThread(self.camera)
        self.image_queue = self.image_acquisition_thread.get_output_queue()

    def CameraInit(self):
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.arm(2)
        self.camera.issue_software_trigger()
        self.image_acquisition_thread.start()

    def FigureOpen(self):
        self.fig = cv2.namedWindow('img', cv2.WINDOW_NORMAL)

    def FrameAcquisition(self):
        cvimage = np.array([])
        while cvimage.size == 0:

            try:
                image = self.image_queue.get_nowait()
                cvimage = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                # rotateimage = cv2.rotate(cvimage, cv2.ROTATE_90_CLOCKWISE)
                self.cvimage = cvimage.copy()
                # cv2.imshow("img", self.cvimage)
                cv2.waitKey(1)
                # self.t.toc()
            except queue.Empty:
                # print("except")
                pass

class getFrame(QtCore.QThread):
    FrameUpdate = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        # super().__init__(parent)
        QtCore.QObject.__init__(self)
        self.Camera = ImageAcquisition(TLCameraSDK())

    def run(self):
        self.ThreadActive = True
        while self.ThreadActive:
            self.Camera.FrameAcquisition()
            Pic = self.Camera.cvimage
            self.FrameUpdate.emit(Pic)
