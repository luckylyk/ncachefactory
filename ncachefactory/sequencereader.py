
from math import sqrt, ceil
from PySide2 import QtCore, QtWidgets, QtGui


SLIDER_COLORS = {
    "bordercolor": "#111159",
    "backgroundcolor.filled": "#25AA33",
    "backgroundcolor.empty": "#334455",
    "framelinecolor": "#FFCC33"}
NOIMAGE_COLORS = {
    "backgroundcolor": "#777777",
    "bordercolor": "#252525",
    "crosscolor": "#ACACAC",
    "textcolor": "#DFDFCC"}
STATUS_COLORS = {
    "approved": "#99FF99",
    "killed": "red"}


class SequenceImageReader(QtWidgets.QWidget):
    def __init__(self, range_, name='', parent=None):
        super(SequenceImageReader, self).__init__(parent, QtCore.Qt.Window)
        self._pixmaps = []
        self.image = ImageViewer(name)
        self.slider = SequenceImageSlider()
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
        self.slider.maximum_settable_value = len(self._pixmaps) + self.slider.minimum
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
                draw_empty_imageview(painter, self)
            else:
                draw_imageview(painter, self)
        except Exception:
            import traceback
            print(traceback.format_exc())
        finally:
            painter.end()


class SequenceImageSlider(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(SequenceImageSlider, self).__init__(parent)
        self.setFixedHeight(10)
        self._minimum = None
        self._maximum = None
        self._value = 0
        self._maximum_settable_value = None
        self._mouse_is_pressed = False

        self.filled_rect = None
        self.value_line = None

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        self._minimum = value
        self.compute_shapes()
        self.repaint()

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        self._maximum = value
        self.compute_shapes()
        self.repaint()

    @property
    def value(self):
        return self._value

    @property
    def position(self):
        return self._value - self._minimum - 1

    @value.setter
    def value(self, value):
        if self._mouse_is_pressed is True:
            return
        self._value = value
        self.compute_shapes()
        self.repaint()
        self.valueChanged.emit(value)

    @property
    def maximum_settable_value(self):
        return self._maximum_settable_value

    @maximum_settable_value.setter
    def maximum_settable_value(self, value):
        self._maximum_settable_value = value
        self.compute_shapes()
        self.repaint()

    def compute_shapes(self):
        values = [self.minimum, self.maximum, self.maximum_settable_value]
        if all([v is not None for v in values]) is False:
            return
        self.filled_rect = get_filled_rect(self)
        self.value_line = get_value_line(self)

    def mousePressEvent(self, event):
        if self._value is None:
            return
        self._mouse_is_pressed = True
        self.set_value_from_point(event.pos())

    def resizeEvent(self, _):
        self.compute_shapes()
        self.repaint()

    def mouseMoveEvent(self, event):
        if self._value is None:
            return
        self._mouse_is_pressed = True
        self.set_value_from_point(event.pos())

    def mouseReleaseEvent(self, event):
        self._mouse_is_pressed = False

    def set_value_from_point(self, point):
        if not all([self.filled_rect, self.value_line]):
            self.compute_shapes()
        if not self.rect().bottom() < point.y() < self.rect().top():
            point.setY(self.rect().top())
        if not self.rect().contains(point):
            return
        self._value = get_value_from_point(self, point)
        self.compute_shapes()
        self.repaint()
        self.valueChanged.emit(self._value)

    def paintEvent(self, event):
        if not all([self.filled_rect, self.value_line]):
            self.compute_shapes()
        # if any error append during the paint, all the application freeze
        # to avoid this error, the paint is placed under a global try
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            drawslider(painter, self)
        except Exception:
            import traceback
            print(traceback.format_exc())
        finally:
            painter.end()


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


def draw_empty_imageview(painter, imageview):
    rect = imageview.rect()
    color = QtGui.QColor(NOIMAGE_COLORS["backgroundcolor"])
    brush = QtGui.QBrush(color)
    color = QtGui.QColor(NOIMAGE_COLORS["bordercolor"])
    pen = QtGui.QPen(color)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawRect(imageview.rect())
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
    textrect = QtCore.QRectF(imageview.rect())
    painter.drawText(textrect, flags, imageview.name)


def drawslider(painter, slider, colors=None):
    colors = get_colors(colors)
    transparent = QtGui.QColor(0, 0, 0, 0)
    # draw background
    backgroundcolor = QtGui.QColor(colors['backgroundcolor.empty'])
    pen = QtGui.QPen(transparent)
    brush = QtGui.QBrush(backgroundcolor)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawRect(slider.rect())
    # draw filled
    if slider.filled_rect:
        backgroundcolor = QtGui.QColor(colors['backgroundcolor.filled'])
        pen.setColor(transparent)
        brush.setColor(backgroundcolor)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRect(slider.filled_rect)
    # draw current
    if slider.value_line:
        pen.setWidth(3)
        linecolor = QtGui.QColor(colors['framelinecolor'])
        pen.setColor(linecolor)
        brush.setColor(transparent)
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawLine(slider.value_line)
    # draw border
    pen.setWidth(5)
    bordercolor = QtGui.QColor(colors['bordercolor'])
    pen.setColor(bordercolor)
    brush.setColor(transparent)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawRect(slider.rect())


def get_value_line(slider):
    rect = slider.rect()
    horizontal_divisor = float(slider.maximum - slider.minimum)
    horizontal_unit_size = rect.width() / horizontal_divisor
    left = (slider.value - slider.minimum) * horizontal_unit_size
    start = QtCore.QPoint(left, rect.top())
    end = QtCore.QPoint(left, rect.bottom())
    return QtCore.QLine(start, end)


def get_filled_rect(slider):
    if slider.maximum_settable_value == slider.minimum:
        return None
    rect = slider.rect()
    horizontal_divisor = float(slider.maximum - slider.minimum)
    horizontal_unit_size = rect.width() / horizontal_divisor
    width = (slider.maximum_settable_value - slider.minimum) * horizontal_unit_size
    return QtCore.QRectF(rect.left(), rect.top(), width, rect.height())


def get_value_from_point(slider, point):
    if not slider.filled_rect.contains(point):
        return slider.maximum_settable_value
    horizontal_divisor = float(slider.maximum - slider.minimum)
    horizontal_unit_size = slider.rect().width() / horizontal_divisor
    value = 0
    x = 0
    while x < point.x():
        value += 1
        x += horizontal_unit_size
    return value + slider.minimum


def get_status_rect(rect):
    size = ceil(sqrt((rect.width() ** 2) + (rect.width() ** 2)) / 15)
    topleft = QtCore.QPointF(
        rect.bottomRight().x() - size,
        rect.bottomRight().y() - size)
    return QtCore.QRectF(topleft, rect.bottomRight())


def get_colors(colors):
    colorscopy = SLIDER_COLORS.copy()
    if colors is not None:
        colorscopy.update(colors)
    return colorscopy
