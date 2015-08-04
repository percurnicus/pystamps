#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ginga.qtw.QtHelp import QtGui, QtCore
from ginga.qtw.ImageViewCanvasQt import ImageViewCanvas
from ginga.BaseImage import BaseImage
import os
from planetaryimage import PDS3Image
from glob import glob
import math
import re
import argparse
try:
    from pdsview import pdsview
    PDSVIEW_INSTALLED = True
except:
    PDSVIEW_INSTALLED = False

app = QtGui.QApplication.instance()
if not app:
    app = QtGui.QApplication(sys.argv)

# Create Global Constants
# Dimensions
SCREEN_WIDTH = QtGui.QDesktopWidget().availableGeometry().width()
FRAME_WIDTH = math.sqrt(SCREEN_WIDTH ** 2. * 0.15)
TOOL_BAR_WIDTH = QtGui.QToolBar().iconSize().width()
PSIZE = FRAME_WIDTH / 4.

# Styles
NOT_SELECTED = (
    "QLabel {color: transparent; border: 3px solid rgb(240, 198, 0)}"
                )
SELECTED = (
    "QLabel {color: transparent; border: 3px solid rgb(255, 255, 255)}"
            )
TOOLBAR = "QToolBar {background-color: gray}"
TITLE_SELECTED = "QLabel{color: white; background-color: black}"
TITLE_NOT_SELECTED = "QLabel{color: rgb(240, 198, 0); background-color: black}"


class ImageStamp(BaseImage):
    """An image object that will be used to display the image in ImageSetView.

    Parameters
    ----------
    filename: string
        A file and its relative path from the current working directory
    row: int
        The row the image will be in by default
    column: int
        The column the image will be in by default

    Attributes
    ----------
    file_name : string
        The filename of the image
    row : int
        The row the image is in
    column : int
        The column the image is in
    pds_image : planetaryimage object
        A planetaryimage object
    position : tuple
        The grid position of the image
    selected : bool
        Indicate that the image is selected (True) or not (False)
    pds_compatible: bool
        Indicates whether planetaryimage can open the file
    """
    def __init__(self, filename, row, column, data_np=None, metadata=None,
                 logger=None):
        BaseImage.__init__(self, data_np=data_np, metadata=metadata,
                           logger=logger)
        self.file_name = filename
        self.row = row
        self.column = column
        try:
            self.pds_image = PDS3Image.open(filename)
            self.set_data(self.pds_image.data)
            self.position = (row, column)
            self.selected = False
            self.pds_compatible = True
        except:
            self.pds_compatible = False

    def __repr__(self):
        return self.file_name


class ImageSet(object):
    """A set of PDS images to be displayed in Pystamps.

    Parameters
    ----------
    filepaths: list
        A list of file paths to pass through ImageStamp

    Attribute
    ---------
    images: list
        A list of ginga images with attributes set in ImageStamp that can be
        displayed in Pystmaps
    """
    def __init__(self, filepaths):
        row = 0
        column = 0

        # Remove any duplicates
        seen = {}
        self.inlist = []
        for filepath in filepaths:
            if filepath not in seen:
                seen[filepath] = 1
                self.inlist.append(filepath)

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
        self.selected = []


class ImageSetView(QtGui.QGraphicsView):
    """The scene and grid layout where the pictures are displayed

    Parameters
    ----------
    image_list: list
        A list of image objects with attributes set in ImageStamp"""

    def __init__(self, image_list):
        super(ImageSetView, self).__init__()
        # Initialize Objects
        self.images = image_list

        # Set Scene and Layout
        self.scene = QtGui.QGraphicsScene()
        self.grid = QtGui.QGraphicsGridLayout()
        self.selected = []

        # Set Images in Grid
        for image in self.images:
            # Create an invisible button and signal to select image
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
                "QPushButton {background-color: transparent}")

            # Create the image
            pds_view = ImageViewCanvas(render='widget')
            pds_view.set_image(image)
            pds_view.set_window_size(PSIZE, PSIZE)
            pds_view.zoom_fit()
            pds_view.set_bg(0, 0, 0)
            pdsview_widget = pds_view.get_widget()
            pdsview_widget.setParent(image.button)
            pdsview_widget.resize(PSIZE, PSIZE)
            pds_view.rotate(180)

            # Create image container to create border, set button as parent
            image.container = QtGui.QLabel()
            image.container.setParent(image.button)
            image.container.setStyleSheet(NOT_SELECTED)
            image.container.setFixedSize(PSIZE, PSIZE)

            # Make Title for each image as the file name, set button as parent
            image.title = QtGui.QLabel(
                os.path.basename(image.file_name), image.button)
            image.title.setFont(QtGui.QFont('Helvetica'))
            image.title.setStyleSheet(TITLE_NOT_SELECTED)
            image.title.setAlignment(QtCore.Qt.AlignTop)
            image.title.setFixedWidth(PSIZE)

            # Set image button in proxy widget to add to graphics grid.
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
            pdsview_widget.move(0, image.title.height())
            image.title.setAlignment(QtCore.Qt.AlignCenter)
            self.grid.setMaximumWidth(PSIZE)

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
        for image in self.images:
            if image.position == pos and image.selected:
                image.container.setStyleSheet(NOT_SELECTED)
                image.title.setStyleSheet(TITLE_NOT_SELECTED)
                image.selected = False
                if image.file_name in self.selected:
                    self.selected.remove(image)

            elif image.position == pos and not(image.selected):
                image.container.setStyleSheet(SELECTED)
                image.title.setStyleSheet(TITLE_SELECTED)
                image.selected = True
                if image.file_name not in self.selected:
                    self.selected.append(image)


class MainWindow(QtGui.QMainWindow):
    """Holds the tool bars and their actions
    Parameters
    ----------
    image_list: list
        A list of image objects with attributes set in ImageStamp"""
    def __init__(self, image_list):
        super(MainWindow, self).__init__()
        self.columns = 4
        self.view = ImageSetView(image_list)
        self.images = self.view.images
        self.main_window_set()
        self.selected_all_toggle = True
        self.selected = self.view.selected

    def main_window_set(self):
        """Create the main window of GUI with tool bars"""
        min_frame_width = FRAME_WIDTH + TOOL_BAR_WIDTH * 2.
        title_height = self.images[0].title.height()
        min_frame_height = (PSIZE + title_height + TOOL_BAR_WIDTH) * 3
        min_frame_size = (min_frame_width, min_frame_height)

        # Create select all tool bar button
        allAction = QtGui.QAction('&Select All/None', self)
        allAction.triggered.connect(self.select_all)
        self.selectAll = self.addToolBar('Select All/None')
        self.selectAll.addAction(allAction)
        self.selectAll.setStyleSheet(TOOLBAR)
        self.selectAll.setParent(self)

        # Create a open in pdsview tool bar button
        viewAction = QtGui.QAction('&Open Selected in pdsview', self)
        viewAction.triggered.connect(self.open_pdsview)
        not_installed = QtGui.QAction('&Open Selected in pdsview', self)
        not_installed.triggered.connect(self.pdsview_not_installed_window)
        self.image_pdsview = self.addToolBar('Open Selected in pdsview')
        if PDSVIEW_INSTALLED:
            self.image_pdsview.addAction(viewAction)
        else:
            self.image_pdsview.addAction(not_installed)
        self.image_pdsview.setStyleSheet(TOOLBAR)
        self.image_pdsview.setParent(self)

        # Create a print select images tool bar button
        printAction = QtGui.QAction('&Print Selected Filenames', self)
        printAction.triggered.connect(self.print_file)
        self.print_image_path = self.addToolBar('Print Selected Filenames')
        self.print_image_path.addAction(printAction)
        self.print_image_path.setStyleSheet(TOOLBAR)
        self.print_image_path.setParent(self)

        # Create an close tool bar button
        exitAction = QtGui.QAction('&Close', self)
        exitAction.triggered.connect(self.close)
        self.exit = self.addToolBar('Close')
        self.exit.addAction(exitAction)
        self.exit.setStyleSheet(TOOLBAR)
        self.exit.setParent(self)

        # Display Window
        self.show()
        self.resize(min_frame_size[0], min_frame_size[1])
        self.setWindowTitle('Pystamps')
        self.setCentralWidget(self.view)

        # Set window to appear in the center of the screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_all(self):
        """Toggle between selecting all images and none"""
        if self.selected_all_toggle:
            for image in self.images:
                image.selected = False
                self.view.select_image(str(image.position))
                self.selected_all_toggle = False
        else:
            for image in self.images:
                image.selected = True
                self.view.select_image(str(image.position))
                self.selected_all_toggle = True

    def open_pdsview(self):
        """Open selected images in pdsview"""
        selected = []
        for image in self.images:
            if image.selected:
                selected.append(image.file_name)
        if len(selected) > 0:
            self.image_set = pdsview.ImageSet(selected)
            viewer = pdsview.PDSViewer(self.image_set)
            viewer.resize(self.width(), self.height())
            viewer.show()
        else:
            print("Must select images first")

    def pdsview_not_installed_window(self):
        """A Message box appears explaining that pdsview is not installed"""
        # There is a bug in QMessageBox right now and prints an error message
        # This does not cause the program to crash so not to worry
        QtGui.QMessageBox.information(
            self, 'pdsview', "pdsview is not installed"
            )

    def print_file(self):
        """Print the selected file absolute paths"""
        space = False
        none_select = True
        for image in self.images:
            if image.selected:
                print(os.path.abspath(image.file_name))
                space = True
                none_select = False
            else:
                pass
        if space:
            print("")
        if none_select:
            print("No Images Selected")

    def resizeEvent(self, resizeEvent):
        """Wrap images when a resize event occurs"""
        images = self.images
        FRAME_WIDTH = self.width()
        column = int(FRAME_WIDTH/PSIZE)
        if column != self.columns:
            grid_row = 0
            grid_column = 0
            for n in range(0, len(self.images)):
                image = images[n]
                # Reassign position only if different than before
                if image.row != grid_row or image.column != grid_column:
                    image.row = grid_row
                    image.column = grid_column
                    image.position = (grid_row, grid_column)
                    self.wrap = True
                else:
                    self.wrap = False
                grid_column += 1
                if grid_column == column:
                    grid_row += 1
                    grid_column = 0
            # Set images in order if frame is larger
            if column > self.columns:
                for w in (range(self.columns-1, len(self.images))):
                    self.wrap_images(w)
            # Set images in reversed order if frame is smaller
            elif column < self.columns:
                for w in reversed(range(self.columns-1, len(self.images))):
                    self.wrap_images(w)
            self.columns = column

    def wrap_images(self, w):
        "Wrap images based on size event"
        image = self.images[w]
        if self.wrap:
            image.button.setText(str(image.position))
            image.mapper.setMapping(image.button, str(image.position))
            image.picture.setWidget(image.button)
            self.view.grid.addItem(image.picture, image.row, image.column)


def pystamps(args=None):
    """Run pystamps from python shell or command line with arguments"""
    try:
        if len(args.file) > 0:
            files = []
            for arg in args.file:
                if os.path.isdir(arg):
                    files += glob(os.path.join(str(arg), '*'))
                elif os.path.isfile(arg):
                    files += glob(str(arg))
        else:
            files = glob('*')
    except AttributeError:
        files = []
        if isinstance(args, list):
            for arg in args:
                files += arg_parser(arg)
        elif isinstance(args, str):
            if ',' in args:
                names = args.split(',')
                for name in names:
                    files = files + arg_parser(name.strip())
            else:
                files = arg_parser(args)

    image_set = ImageSet(files)
    display = MainWindow(image_set.images)
    try:
        sys.exit(app.exec_())
    except:
        pass
    return display.selected


def arg_parser(args):
    if os.path.isdir(args):
            files = glob(os.path.join('%s' % (args), '*'))
    elif args:
        files = glob(args)
    else:
        files = glob('*')
    return files


def cli():
    """Give pystamps ability to run from command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file', nargs='*',
        help="Input filename or glob for files with certain extensions"
        )
    args = parser.parse_args()
    pystamps(args)
