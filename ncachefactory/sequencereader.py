
from math import ceil, sqrt
from PySide2 import QtCore, QtWidgets, QtGui
from ncachefactory.slider import Slider


POINT_RADIUS = 8
POINT_OFFSET = 4
NOIMAGE_COLORS = {
    "backgroundcolor": "#777777",
    "bordercolor": "#252525",
    "crosscolor": "#ACACAC",
    "textcolor": "#DFDFCC"}
HANDLERS_COLORS = {
    "backgroundcolor": "#00FFFF",
    "backgroundcolor.hovered": "#AAFFFF",
    "bordercolor": "#CCCCCC"}
STATUS_COLORS = {
    "approved": "#99FF99",
    "killed": "red"}
STACKED_IMAGE_TEXTCOLOR = "#ffffff"
COMPARATOR_TITLE = "Compare versions"


class SequenceImageReader(QtWidgets.QWidget):
    def __init__(self, range_, name='', parent=None):
        super(SequenceImageReader, self).__init__(parent, QtCore.Qt.Window)
        self._pixmaps = []
        self.image = ImageViewer(name)
        self.image.set_image(None)
        self.slider = Slider()
        self.slider.minimum = range_[0]
        self.slider.maximum = range_[1]
        self.slider.value = self.slider.minimum
        self.slider.valueChanged.connect(self._call_slider_value_changed)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.image)
        self.layout.addWidget(self.slider)

    def add_pixmap(self, pixmap):
        self._pixmaps.append(pixmap)
        value = len(self._pixmaps) + self.slider.minimum
        self.slider.maximum_settable_value = value
        self.slider.value = self.slider.maximum_settable_value

    def _call_slider_value_changed(self, value):
        self.image.name = str(value)
        self.image.set_image(self._pixmaps[self.slider.position])

    def set_next_image(self):
        if self.slider.value == self.slider.maximum_settable_value:
            self.slider.value = self.slider.minimum
        else:
            self.slider.value += 1

    def kill(self):
        self.image.iskilled = True
        self.image.repaint()

    def finish(self):
        self.image.isdone = True
        self.image.repaint()

    def isfull(self):
        return self.slider.maximum_settable_value >= self.slider.maximum


class ImageViewer(QtWidgets.QWidget):
    imageChanged = QtCore.Signal(QtGui.QPixmap)
    nameChanged = QtCore.Signal(str)

    def __init__(self, image=None, name='', parent=None):
        super(ImageViewer, self).__init__(parent)
        self.image = image
        self.name = name
        self.isdone = False
        self.iskilled = False

    def sizeHint(self):
        return QtCore.QSize(640, 480)

    def set_image(self, image):
        self.image = image
        self.repaint()
        self.imageChanged.emit(image)

    def paintEvent(self, event):
        # if any error append during the paint, all the application freeze
        # to avoid this error, the paint is placed under a global try
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            if self.image is None:
                draw_empty_image(painter, self.rect(), self.name)
            else:
                draw_imageview(painter, self)
        except Exception:
            import traceback
            print(traceback.format_exc())
        finally:
            painter.end()


class SequenceStackedImagesReader(QtWidgets.QWidget):
    def __init__(self, pixmaps1, pixmaps2, frames, names=None, parent=None):
        super(SequenceStackedImagesReader, self).__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle(COMPARATOR_TITLE)
        self.isplaying = False
        self.pixmaps1 = pixmaps1
        self.pixmaps2 = pixmaps2
        self.names = [n for n in map(str, frames)]

        self.timer = QtCore.QBasicTimer()

        self.stacked_imagesview = StackedImagesViewer(names, self)
        pixmap1, pixmap2 = self.pixmaps1[0], self.pixmaps2[0]
        self.stacked_imagesview.set_pixmaps(pixmap1, pixmap2)
        self.stacked_imagesview.name = self.names[0]
        # find the first pixmap which is not None and use is as reference size
        for pixmap in pixmaps1 + pixmaps2:
            if pixmap:
                self.stacked_imagesview.setFixedSize(pixmap.size())
        self.stacked_imagesview.update_geometries()
        self.slider = Slider()
        self.slider.minimum = 0
        self.slider.maximum = len(self.pixmaps1)
        self.slider.maximum_settable_value = self.slider.maximum
        self.slider.value = self.slider.minimum
        self.slider.valueChanged.connect(self._call_slider_value_changed)

        self.blender = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.blender.setMinimum(0)
        self.blender.setMaximum(100)
        self.blender.setTickInterval(1)
        self.blender.setSliderPosition(100)
        self.blender.valueChanged.connect(self._call_blender_value_changed)

        self.playstop = QtWidgets.QPushButton("play")
        self.playstop.released.connect(self._call_playstop)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.stacked_imagesview)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.blender)
        self.layout.addWidget(self.playstop)

    def timerEvent(self, event):
        if self.slider.value == self.slider.maximum_settable_value:
            self.slider.value = self.slider.minimum
        else:
            self.slider.value += 1

    def _call_slider_value_changed(self, value):
        i = self.slider.position
        self.stacked_imagesview.name = self.names[i]
        pixmap1, pixmap2 = self.pixmaps1[i], self.pixmaps2[i]
        self.stacked_imagesview.set_pixmaps(pixmap1, pixmap2)

    def _call_blender_value_changed(self, value):
        self.stacked_imagesview.alpha = value / 100.0

    def _call_playstop(self):
        if self.isplaying is False:
            self.playstop.setText('stop')
            self.isplaying = True
            self.timer.start(47, self)
        else:
            self.playstop.setText('play')
            self.isplaying = False
            self.timer.stop()


class StackedImagesViewer(QtWidgets.QWidget):
    def __init__(self, layernames=None, parent=None):
        super(StackedImagesViewer, self).__init__(parent)
        self.setMouseTracking(True)
        self.layernames = layernames
        self.name = ''
        self._alpha = 1
        self.mouse_pressed = False
        self.pixmap1 = None
        self.pixmap2 = None
        self.image2_rect = None
        self.left_resizer = None
        self.right_resizer = None
        self.top_resizer = None
        self.bottom_resizer = None
        self.handlers = [
            self.left_resizer,
            self.right_resizer,
            self.top_resizer,
            self.bottom_resizer]
        self.handler_hovered = None
        self.handle_direction = None

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value):
        self._alpha = value
        self.repaint()

    def mousePressEvent(self, event):
        self.mouse_pressed = True
        if self.handler_hovered == self.left_resizer:
            self.handle_direction = 'left'
        elif self.handler_hovered == self.right_resizer:
            self.handle_direction = 'right'
        elif self.handler_hovered == self.top_resizer:
            self.handle_direction = 'top'
        elif self.handler_hovered == self.bottom_resizer:
            self.handle_direction = 'bottom'
        else:
            self.handle_direction = None

    def mouseMoveEvent(self, event):
        for handler in self.handlers:
            if handler.contains(event.pos()):
                self.handler_hovered = handler
                break

        conditions = (
            self.mouse_pressed is True and
            self.handle_direction is not None and
            self.rect().contains(event.pos()))
        if not conditions:
            return

        if self.handle_direction == 'left':
            self.image2_rect.setLeft(event.pos().x())
        elif self.handle_direction == 'right':
            self.image2_rect.setRight(event.pos().x())
        elif self.handle_direction == 'top':
            self.image2_rect.setTop(event.pos().y())
        elif self.handle_direction == 'bottom':
            self.image2_rect.setBottom(event.pos().y())

        self.update_geometries()
        self.repaint()

    def mouseReleaseEvent(self, event):
        self.mouse_pressed = False
        self.handler_edited = None

    def update_geometries(self):
        if self.image2_rect is None:
            self.image2_rect = QtCore.QRect(self.rect())
        self.left_resizer = get_left_side_rect(self.image2_rect)
        self.right_resizer = get_right_side_rect(self.image2_rect)
        self.top_resizer = get_top_side_rect(self.image2_rect)
        self.bottom_resizer = get_bottom_side_rect(self.image2_rect)
        self.handlers = [
            self.left_resizer,
            self.right_resizer,
            self.top_resizer,
            self.bottom_resizer]

    def set_pixmaps(self, pixmap1, pixmap2):
        self.pixmap1 = pixmap1
        self.pixmap2 = pixmap2
        self.repaint()

    def paintEvent(self, event):
        if self.image2_rect is None:
            self.update_geometries()
        # if any error append during the paint, all the application freeze
        # to avoid this error, the paint is placed under a global try
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            draw_stacked_imagesview(painter, self, alpha=self._alpha)
        except Exception:
            import traceback
            print(traceback.format_exc())
        finally:
            painter.end()


def draw_stacked_imagesview(painter, stacked_imagesview, alpha=1):
    # Prepare font
    font = QtGui.QFont()
    font.setBold(True)
    font.setItalic(False)
    font.setPixelSize(15)
    painter.setFont(font)
    textflags = QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom
    # Draw the images
    if stacked_imagesview.pixmap1 is not None:
        painter.setBrush(QtGui.QBrush())
        painter.setPen(QtGui.QPen())
        pixmap = stacked_imagesview.pixmap1
        painter.drawPixmap(stacked_imagesview.rect(), pixmap)
    else:
        draw_empty_image(painter, stacked_imagesview.rect())
    if stacked_imagesview.layernames is not None:
        pen = QtGui.QPen(QtGui.QColor(STACKED_IMAGE_TEXTCOLOR))
        painter.setPen(pen)
        textrect = QtCore.QRectF(stacked_imagesview.rect())
        painter.drawText(textrect, textflags, stacked_imagesview.layernames[0])

    painter.setOpacity(alpha)
    if stacked_imagesview.pixmap2 is not None:
        painter.setPen(QtGui.QPen())
        pixmap = stacked_imagesview.pixmap2.copy(stacked_imagesview.image2_rect)
        painter.drawPixmap(stacked_imagesview.image2_rect, pixmap)
    else:
        draw_empty_image(painter, stacked_imagesview.image2_rect)
    if stacked_imagesview.layernames is not None:
        pen = QtGui.QPen(QtGui.QColor(STACKED_IMAGE_TEXTCOLOR))
        painter.setPen(pen)
        textrect = QtCore.QRectF(stacked_imagesview.image2_rect)
        painter.drawText(textrect, textflags, stacked_imagesview.layernames[1])

    painter.setOpacity(1)
    # Draw the border
    pen = QtGui.QPen(QtGui.QColor(HANDLERS_COLORS["bordercolor"]))
    pen.setStyle(QtCore.Qt.DashDotLine)
    pen.setWidthF(0.5)
    painter.setPen(pen)
    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
    painter.setBrush(brush)
    painter.drawRect(stacked_imagesview.image2_rect)
    # Draw handlers
    pen.setColor(QtGui.QColor(0, 0, 0, 0))
    painter.setPen(pen)
    hoveredcolor = QtGui.QColor(HANDLERS_COLORS["backgroundcolor.hovered"])
    normalcolor = QtGui.QColor(HANDLERS_COLORS["backgroundcolor"])
    for rect in stacked_imagesview.handlers:
        hovered = rect == stacked_imagesview.handler_hovered
        color = hoveredcolor if hovered else normalcolor
        brush = QtGui.QBrush(QtGui.QColor(color))
        painter.setBrush(brush)
        painter.drawRect(rect)
    # draw frames
    pen = QtGui.QPen(QtGui.QColor(STACKED_IMAGE_TEXTCOLOR))
    painter.setPen(pen)
    flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom
    textrect = QtCore.QRectF(stacked_imagesview.rect())
    painter.drawText(textrect, flags, stacked_imagesview.name)


def draw_imageview(painter, imageview):
    rect = imageview.rect()
    painter.drawPixmap(rect, imageview.image)
    font = QtGui.QFont()
    font.setBold(True)
    font.setItalic(False)
    font.setPixelSize(15)
    painter.setFont(font)
    flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom
    textrect = QtCore.QRectF(rect)
    painter.drawText(textrect, flags, imageview.name)

    if not imageview.isdone and not imageview.iskilled:
        return

    font = QtGui.QFont()
    font.setBold(True)
    font.setItalic(False)
    size = ceil(sqrt((rect.width() ** 2) + (rect.width() ** 2)) / 15)
    font.setPixelSize(size)
    flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
    painter.setFont(font)
    colorname = "approved" if imageview.isdone is True else "killed"
    text = "V" if imageview.isdone is True else "X"
    pen = QtGui.QPen(QtGui.QColor(STATUS_COLORS[colorname]))
    painter.setPen(pen)
    status_rect = get_status_rect(imageview.rect())
    painter.drawText(status_rect, flags, text)


def get_status_rect(rect):
    size = ceil(sqrt((rect.width() ** 2) + (rect.width() ** 2)) / 15)
    topleft = QtCore.QPointF(
        rect.bottomRight().x() - size,
        rect.bottomRight().y() - size)
    return QtCore.QRectF(topleft, rect.bottomRight())


def draw_empty_image(painter, rect, name=''):
    color = QtGui.QColor(NOIMAGE_COLORS["backgroundcolor"])
    brush = QtGui.QBrush(color)
    color = QtGui.QColor(NOIMAGE_COLORS["bordercolor"])
    pen = QtGui.QPen(color)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawRect(rect)
    color = QtGui.QColor(NOIMAGE_COLORS["crosscolor"])
    pen.setColor(color)
    painter.setPen(pen)
    painter.drawLine(QtCore.QLine(rect.bottomLeft(), rect.topRight()))
    painter.drawLine(QtCore.QLine(rect.topLeft(), rect.bottomRight()))
    color = QtGui.QColor(NOIMAGE_COLORS["textcolor"])
    pen.setColor(color)
    painter.setPen(pen)
    font = QtGui.QFont()
    font.setBold(True)
    font.setItalic(False)
    size = ceil(sqrt((rect.width() ** 2) + (rect.width() ** 2)) / 15)
    font.setPixelSize(size)
    painter.setFont(font)
    flags = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
    painter.drawText(QtCore.QRectF(rect), flags, "No Image")

    font = QtGui.QFont()
    font.setBold(True)
    font.setItalic(False)
    font.setPixelSize(15)
    painter.setFont(font)
    flags = QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom
    textrect = QtCore.QRectF(rect)
    painter.drawText(textrect, flags, name)


def get_left_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |*                       |
       |________________________|
    """
    if not rect:
        return None
    x = rect.left()
    y = rect.top() + (rect.height() / 2.0) - (POINT_RADIUS / 2.0)
    point = QtCore.QPointF(x, y)
    point2 = QtCore.QPointF(point.x() + POINT_RADIUS, point.y() + POINT_RADIUS)
    return QtCore.QRectF(point, point2)


def get_right_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                       *|
       |________________________|
    """
    if not rect:
        return None
    x = rect.right()
    y = rect.top() + (rect.height() / 2.0) - (POINT_RADIUS / 2.0)
    point = QtCore.QPointF(x, y)
    point2 = QtCore.QPointF(point.x() - POINT_RADIUS, point.y() + POINT_RADIUS)
    return QtCore.QRectF(point, point2)


def get_top_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |            *           |
       |                        |
       |________________________|
    """
    if not rect:
        return None
    x = rect.left() + (rect.width() / 2.0) - (POINT_RADIUS / 2.0)
    y = rect.top()
    point = QtCore.QPointF(x, y)
    point2 = QtCore.QPointF(point.x() + POINT_RADIUS, point.y() + POINT_RADIUS)
    return QtCore.QRectF(point, point2)


def get_bottom_side_rect(rect):
    """
    this function return a manipulator rect for the transform
    handler.
       __________________________
       |                        |
       |                        |
       |____________*___________|
    """
    if not rect:
        return None
    x = rect.left() + (rect.width() / 2.0) - (POINT_RADIUS / 2.0)
    y = rect.bottom()
    point = QtCore.QPointF(x, y)
    point2 = QtCore.QPointF(point.x() + POINT_RADIUS, point.y() - POINT_RADIUS)
    return QtCore.QRectF(point, point2)

