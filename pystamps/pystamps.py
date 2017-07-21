#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import math
import argparse
from glob import glob
from functools import wraps

from qtpy import QT_VERSION
from planetaryimage import PDS3Image
from matplotlib.figure import Figure
from qtpy import QtWidgets, QtCore, QtGui

try:
    from pdsview import pdsview
    PDSVIEW_INSTALLED = True
except ImportError:
    PDSVIEW_INSTALLED = False

try:
    from pdsspect import pdsspect
    PDSSPECT_INSTALLED = True
except ImportError:
    PDSSPECT_INSTALLED = False

qt_ver = int(QT_VERSION[0])
if qt_ver == 4:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
elif qt_ver == 5:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

# Create Global Constants
# Dimensions
SCREEN_WIDTH = QtWidgets.QDesktopWidget().availableGeometry().width()
FRAME_WIDTH = math.sqrt(SCREEN_WIDTH ** 2. * 0.15)
TOOL_BAR_WIDTH = QtWidgets.QToolBar().iconSize().width()
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


class ImageStamp(object):
    """An image object that will be used to display the image in ImageSetView.

    Parameters
    ----------
    file_name: string
        A file and its relative path from the current working directory
    row: int
        The row the image will be in by default
    column: int
        The column the image will be in by default

    Attributes
    ----------
    file_name : string
        The filename of the image given
    abspath : string
        The absolute path of given filename
    basename : string
        The name of image
    row : int
        The row the image is in
    column : int
        The column the image is in
    pds_image : planetaryimage object
        A planetaryimage object
    size : tuple
        The size of the image (this will be the same for every image)
    selected : bool
        Indicate that the image is selected (True) or not (False)
    pds_compatible: bool
        Indicates whether planetaryimage can open the file
    """

    size = (PSIZE, PSIZE)

    def __init__(self, file_name, row, column):
        self.file_name = file_name
        self.abspath = os.path.abspath(file_name)
        self.basename = os.path.basename(file_name)
        self.row = row
        self.column = column
        self._selected = False
        self.button = None
        self.container = None
        self.title = None
        self.proxy_widget = None
        try:
            self.pds_image = PDS3Image.open(file_name)
            self.pds_compatible = True
        except Exception:
            self.pds_image = None
            self.pds_compatible = False

        if self.pds_compatible:
            self._create_button()
            self._create_title()
            self._create_proxy_widget()

    def __must_be_pds_compatible(func):
        @wraps(func)
        def wrapper(self):
            if not self.pds_compatible:
                raise RuntimeError("Image not pds compatible")
            return func(self)
        return wrapper

    @__must_be_pds_compatible
    def display_selected(self):
        """Change the border to white"""
        self.container.setStyleSheet(SELECTED)
        self.title.setStyleSheet(TITLE_SELECTED)

    @__must_be_pds_compatible
    def display_not_selected(self):
        """Change the border yellow"""
        self.container.setStyleSheet(NOT_SELECTED)
        self.title.setStyleSheet(TITLE_NOT_SELECTED)

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, selected_state):
        state_changed = self._selected != selected_state
        if not state_changed:
            return
        self._selected = selected_state
        if self._selected and self.pds_compatible:
            self.display_selected()
        elif not self._selected and self.pds_compatible:
            self.display_not_selected()

    @__must_be_pds_compatible
    def _create_button(self):
        """Create the button and set in the container"""
        self.button = ImageButton(self)

        # Create image container to create border, set button as parent
        self.container = QtWidgets.QLabel()
        self.container.setParent(self.button)
        self.container.setStyleSheet(NOT_SELECTED)

    @__must_be_pds_compatible
    def _create_title(self):
        """Create images title"""
        # Make Title for each image as the file name, set button as parent
        self.title = QtWidgets.QLabel(self.basename, self.button)
        self.title.setFont(QtGui.QFont('Helvetica', 12))
        self.title.setStyleSheet(TITLE_NOT_SELECTED)
        self.title.setAlignment(QtCore.Qt.AlignTop)
        self.title.setFixedWidth(PSIZE)

        # Make image title fit in space by decreasing font size
        title_metrics = self.title.fontMetrics()
        title_width = title_metrics.boundingRect(self.title.text()).width()
        font_size = 12
        while title_width > PSIZE:
            self.title.setFont(QtGui.QFont('Helvetica', font_size))
            title_text = self.title.text()
            title_metrics = self.title.fontMetrics()
            title_width = title_metrics.boundingRect(title_text).width()
            font_size -= 1

    @__must_be_pds_compatible
    def _create_proxy_widget(self):
        """Set image button in proxy widget to add to graphics grid"""
        self.proxy_widget = QtWidgets.QGraphicsProxyWidget()
        self.proxy_widget.setWidget(self.button)
        self.proxy_widget.setMinimumSize(PSIZE, PSIZE)
        self.proxy_widget.setPalette(QtGui.QPalette(QtCore.Qt.black))

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
    columns : int
        Number of columns the grid layout has
    selected_images : list
        List of ImageStamp that are selected
    """
    def __init__(self, filepaths):
        self._views = set()

        # Remove any duplicates while maintaining order
        seen = {}
        inlist = []
        for filepath in filepaths:
            if filepath not in seen:
                seen[filepath] = 1
                inlist.append(filepath)

        # Create image objects with attributes set in ImageStamp
        self.images = []
        self.columns = 4
        row = 0
        column = 0
        for image in inlist:
            image_stamp = ImageStamp(image, row, column)
            if image_stamp.pds_compatible:
                self.images.append(image_stamp)
                column += 1
                if column == self.columns:
                    row += 1
                    column = 0
        self.selected_images = []

    def register(self, view):
        self._views.add(view)

    def unregister(self, view):
        self._views.remove(view)

    def set_image_selected(self, image):
        """Set the image as selected, add to list, and display selection"""
        image.selected = True
        if image not in self.selected_images:
            self.selected_images.append(image)
        # for view in self._views:
        #     view.display_selected(image)

    def set_image_not_selected(self, image):
        """Set image as not selected, remove from list, display unselection"""
        image.selected = False
        if image in self.selected_images:
            self.selected_images.remove(image)
        # for view in self._views:
        #     view.display_not_selected(image)

    def set_images_positions(self):
        """Assign the positions based on columns and display in grid"""
        row = 0
        column = 0
        for image in self.images:
            # Reassign position only if different than before
            image.row = row
            image.column = column
            column += 1
            if column == self.columns:
                row += 1
                column = 0

        for view in self._views:
            view.set_grid_layout()


class ImageSetController(object):
    """ImageSet controller

    Parameters
    ----------
    model : ImageSet
    view : object
        Associated view with the model
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view

    def select_image(self, image):
        """Set image as selected or not selected"""
        if image.selected:
            self.model.set_image_not_selected(image)
        else:
            self.model.set_image_selected(image)

    def select_all(self):
        """Set all images as selected"""
        for image in self.model.images:
            self.model.set_image_selected(image)

    def unselect_all(self):
        """Set all images as not selected"""
        for image in self.model.images:
            self.model.set_image_not_selected(image)

    def wrap_images(self, new_columns):
        """Given new columns, reposition images"""
        if new_columns != self.model.columns:
            self.model.columns = new_columns
            self.model.set_images_positions()


class ImageButton(FigureCanvasQTAgg):
    """Button containing the image

    Parameters
    ----------
    image_stamp : ImageStamp
    parent : QtQWidgets.QWidget
    """

    clicked = QtCore.Signal(object)

    def __init__(self, image_stamp, parent=None):
        self.parent = parent
        self.image_stamp = image_stamp
        fig = Figure(figsize=(1, 1))
        fig.subplots_adjust(
            left=0.0, right=1.0, top=1.0, bottom=0.0, wspace=0.0,
            hspace=0.0)
        super(ImageButton, self).__init__(fig)
        self._figure = fig
        self._ax = fig.add_subplot(111)
        if len(image_stamp.pds_image.image.shape) == 1:
            shape = image_stamp.pds_image.image.shape
            data = image_stamp.pds_image.image.reshape((shape[0], 1))
        else:
            data = image_stamp.pds_image.image
        imgplot = self._ax.imshow(data)
        if image_stamp.pds_image.bands != 3:
            imgplot.set_cmap('gray')
        self._figure.set_facecolor('black')
        self._ax.axis('off')
        self.setFixedSize(PSIZE, PSIZE)

    def mouseReleaseEvent(self, event):
        self.clicked.emit(self.image_stamp)


class ImageSetView(QtWidgets.QGraphicsView):
    """The scene and grid layout where the pictures are displayed

    Parameters
    ----------
    image_set: ImageSet
    """

    def __init__(self, image_set):
        super(ImageSetView, self).__init__()
        # Initialize Objects
        self.image_set = image_set
        self.image_set.register(self)
        self.controller = ImageSetController(image_set, self)
        self.images = image_set.images

        # Set Scene and Layout
        scene = QtWidgets.QGraphicsScene()
        self.grid = QtWidgets.QGraphicsGridLayout()
        self.grid.setMaximumWidth(PSIZE)

        for image in self.images:
            image.button.clicked.connect(self.select_image)
            self.grid.addItem(
                image.proxy_widget, image.row, image.column)
            image.container.move(0, image.title.height())
            image.title.setAlignment(QtCore.Qt.AlignCenter)
            image.container.setFixedSize(PSIZE, PSIZE - image.title.height())

        # Set grid in view and MainWindow
        self.layout_container = QtWidgets.QGraphicsWidget()
        self.layout_container.setLayout(self.grid)
        scene.addItem(self.layout_container)
        self.setScene(scene)
        self.setBackgroundBrush(QtCore.Qt.black)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

    def set_grid_layout(self):
        self.grid = QtWidgets.QGraphicsGridLayout()
        for image in self.images:
            self.grid.addItem(image.proxy_widget, image.row, image.column)
        self.layout_container.setLayout(self.grid)

    def select_image(self, image_stamp):
        """Updates the border indicating selected/not selected"""
        self.controller.select_image(image_stamp)


class MainWindow(QtWidgets.QMainWindow):
    """Holds the tool bars and their actions
    Parameters
    ----------
    image_set: ImageSet
    """

    def __init__(self, image_set):
        super(MainWindow, self).__init__()
        self.image_set = image_set
        self.set_view = ImageSetView(image_set)
        self.images = self.set_view.images
        self.toolbar = None
        self.select_all_action = None
        self.view_action = None
        self.not_installed_action = None
        self.print_action = None
        self.exit_action = None
        self.main_window_set()
        self.selected_all_toggle = False
        self.selected = self.image_set.selected_images
        self._pdsviewer = None

    def main_window_set(self):
        """Create the main window of GUI with tool bars"""
        min_frame_width = FRAME_WIDTH + TOOL_BAR_WIDTH * 2.
        title_height = 13
        min_frame_height = (PSIZE + title_height + TOOL_BAR_WIDTH) * 3
        min_frame_size = (min_frame_width, min_frame_height)
        self.toolbar = self.addToolBar('PyStamps')
        self.toolbar.setStyleSheet(TOOLBAR)
        self.toolbar.setParent(self)

        # Create select all tool bar button
        self.select_all_action = QtWidgets.QAction('&Select All/None', self)
        self.select_all_action.triggered.connect(self.select_all)
        self.toolbar.addAction(self.select_all_action)

        # Create a open in pdsview tool bar button
        self.view_action = QtWidgets.QAction('&Open Selected in pdsview', self)
        self.view_action.triggered.connect(self.open_pdsview)
        self.not_installed_action = QtWidgets.QAction(
            '&Open Selected in pdsview', self)
        self.not_installed_action.triggered.connect(
            self.pdsview_not_installed_window)
        if PDSVIEW_INSTALLED:
            self.toolbar.addAction(self.view_action)
        else:
            self.toolbar.addAction(self.not_installed_action)

        # Create a open in pdsspect tool bar button
        self.spect_action = QtWidgets.QAction(
            '&Open Selected in pdsspect', self)
        self.spect_action.triggered.connect(self.open_pdsspect)
        self.spect_not_installed_action = QtWidgets.QAction(
            '&Open Selected in pdsspect', self)
        self.spect_not_installed_action.triggered.connect(
            self.pdsview_not_installed_window)
        if PDSSPECT_INSTALLED:
            self.toolbar.addAction(self.spect_action)
        else:
            self.toolbar.addAction(self.spect_not_installed_action)

        # Create a print select images tool bar button
        self.print_action = QtWidgets.QAction(
            '&Print Selected Filenames', self)
        self.print_action.triggered.connect(self.print_file)
        self.toolbar.addAction(self.print_action)

        # Create an close tool bar button
        self.exit_action = QtWidgets.QAction('&Close', self)
        self.exit_action.triggered.connect(self.close)
        self.toolbar.addAction(self.exit_action)

        # Display Window
        self.setWindowTitle('Pystamps')
        self.setCentralWidget(self.set_view)
        self.resize(min_frame_size[0], min_frame_size[1])
        self.show()

        # Set window to appear in the center of the screen
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_all(self):
        """Toggle between selecting all images and none"""
        if self.selected_all_toggle:
            self.set_view.controller.unselect_all()
            self.selected_all_toggle = False
        else:
            self.set_view.controller.select_all()
            self.selected_all_toggle = True

    def open_pdsview(self):
        """Open selected images in pdsview"""
        if len(self.image_set.selected_images) > 0:
            # TODO: When there is a remove method in pdsview.ImageSet, do not
            # recreate the viewer each time. Only change the image_set
            image_set = pdsview.ImageSet(
                [image.file_name for image in
                 self.image_set.selected_images]
            )
            self._pdsviewer = pdsview.PDSViewer(image_set)
            self._pdsviewer.resize(self.width(), self.height())
            self._pdsviewer.show()
        else:
            print("Must select images first")

    def pdsview_not_installed_window(self):
        """A Message box appears explaining that pdsview is not installed"""
        QtWidgets.QMessageBox.warning(
            self, 'pdsview', "pdsview is not installed"
        )

    def open_pdsspect(self):
        """Open selected images in pdsspect"""
        if len(self.image_set.selected_images) > 0:
            images = [
                image.file_name for image in self.image_set.selected_images
            ]
            pdsspect.open_pdsspect(app, images)
        else:
            print("Must select images first")

    def pdsspect_not_installed_window(self):
        """A Message box appears explaining that pdsspect is not installed"""
        QtWidgets.QMessageBox.warning(
            self, 'pdsspect', "pdsspect is not installed"
        )

    def print_file(self):
        """Print the selected file absolute paths"""
        images_have_been_selected = len(self.image_set.selected_images) > 0
        if images_have_been_selected:
            for image in self.image_set.selected_images:
                print(image.abspath)
            print("")
        else:
            print("No Images Selected")

    def resizeEvent(self, resizeEvent):
        """Wrap images when a resize event occurs"""
        FRAME_WIDTH = self.width()
        new_columns = int(FRAME_WIDTH / PSIZE)
        self.set_view.controller.wrap_images(new_columns)


def pystamps(inlist=None):
    """Run pystamps from python shell or command line with arguments

    Examples
    --------

    From the command line:

    To view all images from current directory

    pystamps

    To view all images in a different directory

    pystamps path/to/different/directory/

    This is the same as:

    pystamps path/to/different/directory/*

    To view a specific image or types of images

    pystamps 1p*img

    To view images from multiple directories:

    pystamps * path/to/other/directory/

    From the (i)python command line:

    >>> from pystamps.pystamps import pystamps
    >>> pystamps()
    Displays all of the images from current directory
    >>> pystamps('path/to/different/directory')
    Displays all of the images in the different directory
    >>> pystamps ('1p*img')
    Displays all of the images that follow the glob pattern
    >>> pystamps ('a1.img, b*.img, example/path/x*img')
    You can display multiple images, globs, and paths in one window by
    separating each item by a command
    >>> pystamps (['a1.img, b3.img, c1.img, d*img'])
    You can also pass in a list of files/globs

    You can also access attributes of the selected images after the window
    is closed:

    >>> from pystamps.pystamps import pystamps
    >>> example = pystamps()
    # Select some images
    >>> example
    [list, of, selected, images]
    >>> example[#].attribute
    return information stored in that attribute
    # See ImageStamp for accessible attributes
    >>> example[#].pds_image.pds_attribute
    Access pds attributes
    # See planetaryimage documentation on accessible pds_iamge attributes
    """
    files = []
    if isinstance(inlist, list):
        if inlist:
            for item in inlist:
                files += arg_parser(item)
        else:
            files = glob('*')
    elif isinstance(inlist, str):
        names = inlist.split(',')
        for name in names:
            files = files + arg_parser(name.strip())
    elif inlist is None:
        files = glob('*')

    image_set = ImageSet(files)
    display = MainWindow(image_set)
    try:
        sys.exit(app.exec_())
    except Exception:
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
    pystamps(args.file)
