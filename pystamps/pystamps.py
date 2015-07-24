# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
import os
from planetaryimage import PDS3Image
from qimage2ndarray import gray2qimage
from glob import glob
import math
import re


app = QtGui.QApplication(sys.argv)

# Create Global Constants
# Dimensions
SCREEN_WIDTH = QtGui.QDesktopWidget().availableGeometry().width()
FRAME_WIDTH = math.sqrt(SCREEN_WIDTH ** 2. * 0.1)
TOOL_BAR_WIDTH = QtGui.QToolBar().iconSize().width()
PSIZE = FRAME_WIDTH / 4.

# Styles
NOT_SELECTED = (
    "QLabel {background-color: black; border: 3px solid rgb(240, 198, 0)}"
                )
SELECTED = (
    "QLabel {background-color: black; border: 3px solid rgb(255, 255, 255)}"
            )
TOOLBAR = "QToolBar {background-color: gray}"
TITLE_SELECTED = "QLabel{color: white; background-color: black}"
TITLE_NOT_SELECTED = "QLabel{color: rgb(240, 198, 0); background-color: black}"


class ImageStamp(object):
    """Assign each image attributes below"""
    def __init__(self, filename, row, column):
        self.file_name = filename
        self.row = row
        self.column = column
        try:
            self.pdsimage = PDS3Image.open(filename)
            self.position = (row, column)
            self.selected = False
            self.pds_compatible = True
        except:
            self.pds_compatible = False

    def __repr__(self):
        return self.file_name


class ImageSet(object):
    """Create set of images to be displayed"""
    def __init__(self, path='*'):
        row = 0
        column = 0
        if '*' in path:
            self.names = glob('%s' % (path))
        else:
            self.names = glob(os.path.join('%s' % (path), '*'))

        # Remove any duplicates
        seen = {}
        self.inlist = []
        for name in self.names:
            if name not in seen:
                seen[name] = 1
                self.inlist.append(name)

        # Create image objects with attributes set in ImageStamp
        self.images = []
        for image in self.inlist:
            image_stamp = ImageStamp(image, row, column)
            if image_stamp.pds_compatible:
                self.images.append(image_stamp)
                column += 1
                if column == 4:
                    row += 1
                    column = 0

    def selected(self):
        selected_images = []
        for image in self.images:
            if image.selected:
                selected_images.append(image)
        return selected_images


class ImageSetView(QtGui.QGraphicsView):
    """Displays images in the main widget window with a border marking them as
    selected (white) or unselected (yellow)"""

    def __init__(self, path='*'):
        super(ImageSetView, self).__init__()
        # Initialize Objects
        self.image_set = ImageSet(path)

        # Set Scene and Layout
        self.scene = QtGui.QGraphicsScene()
        self.grid = QtGui.QGraphicsGridLayout()

        # Set Images in Grid
        for image in self.image_set.images:

            # Create invisible button and signal to select iamge
            image.button = QtGui.QPushButton(str(image.position))
            image.mapper = QtCore.QSignalMapper(self)
            image.mapper.setMapping(image.button, str(image.position))
            self.connect(
                image.button, QtCore.SIGNAL('clicked()'), image.mapper,
                QtCore.SLOT("map()")
                        )
            self.connect(
                image.mapper, QtCore.SIGNAL("mapped(const QString &)"),
                self.select_image
                        )
            image.button.setStyleSheet(
                "QPushButton {background-color: transparent}"
                                        )
            # Create pixmap image
            qimage = gray2qimage(image.pdsimage.data, True)
            pixmap_temp = QtGui.QPixmap.fromImage(qimage)
            pixmap = pixmap_temp.scaled(
                PSIZE, PSIZE, QtCore.Qt.KeepAspectRatio
                                        )

            # Create container to place in grid, set button as parent
            image.container = QtGui.QLabel(image.button)
            image.container.setPixmap(pixmap)
            image.container.setStyleSheet(NOT_SELECTED)
            image.container.setFixedSize(PSIZE, PSIZE)

            # Make Title for each image as the file name, set button as parent
            image.title = QtGui.QLabel(image.file_name, image.button)
            image.title.setFont(QtGui.QFont('Helvetica'))
            image.title.setStyleSheet(TITLE_NOT_SELECTED)
            image.title.setAlignment(QtCore.Qt.AlignTop)
            image.title.setFixedWidth(PSIZE)

            # Set image button in proxy widget to add to grid.
            # Because button is image's parent, adding button as image
            image.picture = QtGui.QGraphicsProxyWidget()
            image.picture.setWidget(image.button)
            image.picture.setMinimumSize(PSIZE, PSIZE + image.title.height())

            # Make image title fit in space by decreasing font size
            title_width = image.title.fontMetrics()
            title_width = title_width.boundingRect(image.title.text()).width()
            font_size = 13
            while title_width > PSIZE:
                image.title.setFont(QtGui.QFont('Helvetica', font_size))
                title_text = image.title.text()
                title_width = image.title.fontMetrics()
                title_width = title_width.boundingRect(title_text).width()
                font_size -= 1

            # Add picture to grid, move image/button down so room for title
            self.grid.addItem(
                image.picture, image.row, image.column)
            image.container.move(0, image.title.height())
            image.title.setAlignment(QtCore.Qt.AlignCenter)
            self.grid.setMinimumWidth(PSIZE)

        # Set grid in view and MainWindow
        layout_container = QtGui.QGraphicsWidget()
        layout_container.setLayout(self.grid)
        self.scene.addItem(layout_container)
        self.setScene(self.scene)
        self.setBackgroundBrush(QtCore.Qt.black)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

    def select_image(self, position):
        """Updates the border indicating selected/not selected"""
        find_pos = re.findall(r'\d+', position)
        pos = (int(find_pos[0]), int(find_pos[1]))
        for image in self.image_set.images:
            if image.position == pos and image.selected:
                image.container.setStyleSheet(NOT_SELECTED)
                image.title.setStyleSheet(TITLE_NOT_SELECTED)
                image.selected = False
            elif image.position == pos and not(image.selected):
                image.container.setStyleSheet(SELECTED)
                image.title.setStyleSheet(TITLE_SELECTED)
                image.selected = True


class MainWindow(QtGui.QMainWindow):
    """Holds the tool bars and actions. Makes images clickable."""
    def __init__(self, path='*'):
        super(MainWindow, self).__init__()
        self.columns = 4
        self.view = ImageSetView(path)
        self.image_set = self.view.image_set
        self.main_window_set()
        self.selected_all_toggle = True

    def main_window_set(self):
        """Create the main window of GUI with toolbars"""
        min_frame_size = (FRAME_WIDTH + TOOL_BAR_WIDTH * 2. + 30,
                          (PSIZE + TOOL_BAR_WIDTH) * 3)

        # Create Actions for tool bar
        exitAction = QtGui.QAction('&Exit', self)
        exitAction.triggered.connect(self.close)
        printAction = QtGui.QAction('&Print Selected Filenames', self)
        printAction.triggered.connect(self.print_file)
        allAction = QtGui.QAction('&Select All/None', self)
        allAction.triggered.connect(self.select_all)

        # Assign actions to the tool bar object
        self.exit = self.addToolBar('Exit')
        self.exit.addAction(exitAction)
        self.exit.setStyleSheet(TOOLBAR)
        self.exit.setParent(self)
        self.print_image_path = self.addToolBar('Print Selected Filenames')
        self.print_image_path.addAction(printAction)
        self.print_image_path.setStyleSheet(TOOLBAR)
        self.print_image_path.setParent(self)
        self.selectAll = self.addToolBar('Select All/None')
        self.selectAll.addAction(allAction)
        self.selectAll.setStyleSheet(TOOLBAR)
        self.selectAll.setParent(self)

        # Set window to appear in the cebter of the screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Display Window
        self.resize(min_frame_size[0], min_frame_size[1])
        self.setMinimumWidth(min_frame_size[0])
        self.setWindowTitle('Pystamps')
        self.setCentralWidget(self.view)
        self.show()

        # Set Bakcground to be black
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(palette)

    def print_file(self):
        """Print the selected file absolute paths"""
        space = False
        for image in self.view.image_set.images:
            if image.selected:
                print os.path.abspath(image.file_name)
                space = True
            else:
                pass
        if space:
            print ""

    def select_all(self):
        """Toggle between selecting all images and none"""
        if self.selected_all_toggle:
            for image in self.view.image_set.images:
                image.selected = False
                self.view.select_image(str(image.position))
                self.selected_all_toggle = False
        else:
            for image in self.view.image_set.images:
                image.selected = True
                self.view.select_image(str(image.position))
                self.selected_all_toggle = True

    def resizeEvent(self, resizeEvent):
        """Wrap images when a resize event occurs"""
        images = self.image_set.images
        FRAME_WIDTH = self.width()
        column = int(FRAME_WIDTH/PSIZE)

        # When frame size increased, wrap to next available column
        if int(column) > self.columns:
            self.columns = int(column)
            for n in range(self.columns-1, len(images)):
                image = images[n]
                if image.row > 0 and images[n].column == 0:
                    image.row = image.row - 1
                    image.column = n
                    image.position = (image.row, image.column)
                    image.button.setText(str(image.position))
                    image.mapper.setMapping(image.button, str(image.position))
                    image.picture.setWidget(image.button)
                    self.view.grid.addItem(
                        image.picture, image.row, image.column
                                            )
                else:
                    image.column = image.column - 1
                    image.position = (image.row, image.column)
                    image.button.setText(str(image.position))
                    image.mapper.setMapping(image.button, str(image.position))
                    image.picture.setWidget(image.button)
                    self.view.grid.addItem(
                        image.picture, image.row, image.column
                                            )

        # When frame size decreased wrap underneath
        elif int(column) < self.columns:
            self.columns = int(column)
            grid_row = 0
            grid_column = 0
            for n in range(0, len(images)):
                image = images[n]
                image.row = grid_row
                image.column = grid_column
                image.position = (grid_row, grid_column)
                grid_column += 1
                if grid_column == self.columns:
                    grid_row += 1
                    grid_column = 0
            for m in reversed(range(self.columns, len(images))):
                image = images[m]
                image.button.setText(str(image.position))
                image.mapper.setMapping(image.button, str(image.position))
                image.picture.setWidget(image.button)
                self.view.grid.addItem(
                        image.picture, image.row, image.column
                                            )


def pystamps(path='*'):
    display = MainWindow(path)
    sys.exit(app.exec_())


if __name__ == '__main__':
    pystamps()
