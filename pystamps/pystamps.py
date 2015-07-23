# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
import os
from planetaryimage import PDS3Image
from qimage2ndarray import gray2qimage
from glob import glob
import math


class Dimensions(object):
    def __init__(self):
        self.screen_width = QtGui.QDesktopWidget().availableGeometry().width()
        self.frame_width = math.sqrt(self.screen_width ** 2. * 0.1)
        self.tool_bar_w = QtGui.QToolBar().iconSize().width()
        self.psize = self.frame_width / 4.


class ImageStamp(object):
    def __init__(self, filename, x, y):
        dim = Dimensions()
        self.file_name = filename
        self.x = x
        self.y = y
        try:
            pdsimage = PDS3Image.open(filename)
            qimage = gray2qimage(pdsimage.data, True)
            self.position = (x, y)
            self.selected = False
            pixmap = QtGui.QPixmap.fromImage(qimage)
            self.pixmap = pixmap.scaled(dim.psize, dim.psize,
                                        QtCore.Qt.KeepAspectRatio)
            self.lbl = QtGui.QLabel()
            self.lbl.setPixmap(self.pixmap)
            self.lbl.setStyleSheet("""QLabel {background-color: black;
                                    border: 4px solid rgb(240, 198, 0)}""")
            y += 1
            if y == 4:
                x += 1
                y = 0
        except:
            pass

    def __repr__(self):
        return self.file_name


class ImageSet(object):
    def __init__(self):
        x = 0
        y = 0
        names = []
        extensions = ['img', 'IMG']
        for ext in extensions:
            names = names + (glob('*%s' % (ext)))
        seen = {}
        inlist = []
        for name in names:
            if name not in seen:
                seen[name] = 1
                inlist.append(name)
        self.images = []
        for image in inlist:
            self.images.append(ImageStamp(image, x, y))
            y += 1
            if y == 4:
                x += 1
                y = 0

    def selected(self):
        selected_images = []
        for image in self.images:
            if image.selected:
                selected_images.append(image)
        return selected_images


class DisplayImages(QtGui.QGraphicsView):
    """Displays images in the main widget window with a border marking them as
    selected (white) or unselected (yellow)"""

    def __init__(self):
        super(DisplayImages, self).__init__()
        # Initialize Objects
        self.image_set = ImageSet()
        dim = Dimensions()

        # Set Scene and Layout
        self.scene = QtGui.QGraphicsScene()
        self.grid = QtGui.QGraphicsGridLayout()

        # Set Images in Grid
        for image in self.image_set.images:
            try:
                self.picture = QtGui.QGraphicsProxyWidget()
                self.picture.setWidget(image.lbl)
                self.picture.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
                self.picture.setMaximumSize(dim.psize, dim.psize)
                self.picture.setMinimumSize(dim.psize, dim.psize)
                self.grid.setColumnFixedWidth(0, dim.psize)
                self.grid.setRowFixedHeight(0, dim.psize)
                self.grid.addItem(self.picture, image.x, image.y,
                                  QtCore.Qt.AlignCenter)
            except:
                pass

        form = QtGui.QGraphicsWidget()
        form.setLayout(self.grid)
        self.scene.addItem(form)
        self.setScene(self.scene)
        self.setBackgroundBrush(QtCore.Qt.black)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def select_image(self, pos):
        """Updates the border indicating selected/not selected"""
        for image in self.image_set.images:
            if image.position == pos and image.selected:
                pict = image.lbl
                pict.setStyleSheet("""QLabel {background-color: black;
                                   border: 4px solid rgb(240, 198, 0)}""")
                image.selected = False
            elif image.position == pos and not(image.selected):
                pict = image.lbl
                pict.setStyleSheet("""QLabel {background-color: black;
                                   border: 4px solid rgb(255, 255, 255)}""")
                image.selected = True


class Pystamps(QtGui.QMainWindow):
    """Holds the tool bars and actions. Makes images clickable."""
    def __init__(self):
        super(Pystamps, self).__init__()
        self.image_set = ImageSet()
        self.disp = DisplayImages()
        self.dim = Dimensions()
        self.pystamps()
        self.all_count = 0

    def pystamps(self):
        fwidth = self.dim.frame_width
        psize = self.dim.psize
        tool_bar_w = self.dim.tool_bar_w
        min_frame_size = (fwidth + tool_bar_w * 2. + 30,
                          (psize + tool_bar_w) * 3)

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
        self.exit.setStyleSheet("QToolBar {background-color: gray}")
        self.print_image_path = self.addToolBar('Print Selected Filenames')
        self.print_image_path.addAction(printAction)
        self.print_image_path.setStyleSheet("""QToolBar
                                            {background-color: gray}""")
        self.selectAll = self.addToolBar('Select All/None')
        self.selectAll.addAction(allAction)
        self.selectAll.setStyleSheet("QToolBar {background-color: gray}")

        # Set window to appear in the cebter of the screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Display Window
        self.resize(min_frame_size[0], min_frame_size[1])
        self.setWindowTitle('Pystamps')
        self.setCentralWidget(self.disp)
        self.show()

        # Set Bakcground to be black
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(palette)

    def mousePressEvent(self, QMousEvent):
        psize = int(self.dim.psize)
        self.X = (QMousEvent.x() - (15+((QMousEvent.x()/psize)*10)))/psize
        self.Y = (QMousEvent.y() - (15+((QMousEvent.x()/psize)*10)))/psize
        try:
            self.disp.select_image((self.Y, self.X))
        except:
            pass

    def print_file(self):
        space = False
        for image in self.disp.image_set.images:
            if image.selected:
                print image.file_name
                space = True
            else:
                pass
        if space:
            print ""

    def select_all(self):
        if self.all_count % 2 == 0:
            for item in self.disp.image_set.images:
                item.selected = False
                self.disp.select_image(item.position)
        else:
            for item in self.disp.image_set.images:
                item.selected = True
                self.disp.select_image(item.position)
        self.all_count += 1

    # TODO make window resizable and wrap images


def main():
    app = QtGui.QApplication(sys.argv)
    stamps = Pystamps()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()