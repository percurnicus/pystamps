# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
import os
from planetaryimage import PDS3Image
from qimage2ndarray import gray2qimage
from glob import glob
import math


class DisplayImages(QtGui.QWidget):
    """Displays images in the main widget window with a border marking them as
    selected (white) or unselected (yellow)"""

    def __init__(self):
        super(DisplayImages, self).__init__()
        self.grid = QtGui.QGridLayout()
        grid = self.grid
        self.setAutoFillBackground(True)
        x = 0
        y = 0
        self.X = 0
        self.Y = 0
        self.img_dict = {}
        self.posdict = {}
        self.pdsimages = []
        # TODO Expand the types of extensions to search for
        extensions = ['img', 'IMG']
        for ext in extensions:
            self.pdsimages = self.pdsimages + (glob('*%s' % (ext)))
        seen = {}
        self.file_names = []
        for image in self.pdsimages:
            if image not in seen:
                seen[image] = 1
                self.file_names.append(image)
        self.screen_width = QtGui.QDesktopWidget().availableGeometry().width()
        self.frame_width = math.sqrt(self.screen_width ** 2. * 0.1)
        self.tool_bar_w = QtGui.QToolBar(self).iconSize().width()
        self.psize = self.frame_width / 4.
        self.setMinimumSize(self.frame_width + self.tool_bar_w * 2.,
                            self.psize + self.tool_bar_w)
        for file_name in self.file_names:
            try:
                hbox = QtGui.QHBoxLayout()
                pdsimage = PDS3Image.open(file_name)
                image = gray2qimage(pdsimage.data, True)
                pixmap = QtGui.QPixmap.fromImage(image)
                pixmap = pixmap.scaled(self.psize, self.psize,
                                       QtCore.Qt.KeepAspectRatio)
                picture = QtGui.QLabel(self)
                picture.setPixmap(pixmap)
                picture.setStyleSheet("""QLabel {background-color: black;
                                      border: 3px solid rgb(240, 198, 0)}""")
                hbox.addWidget(picture, QtCore.Qt.AlignCenter)
                grid.addLayout(hbox, x, y, QtCore.Qt.AlignTop)
                grid.setColumnMinimumWidth(y, self.psize)
                grid.setRowMinimumHeight(x, self.psize)
                self.posdict[(x, y)] = {'name': file_name, 'pict': picture,
                                        'select': False}
                y += 1
                if y == 4:
                    x += 1
                    y = 0
            except:
                pass

        # Fill in the rest of the area if there are less than four pictures
        if y <= 4 and x == 0:
            grid.setColumnMinimumWidth(y, self.psize)
            grid.setColumnStretch(y, 1)

        self.setLayout(grid)

    def select_image(self, posy, posx):
        """Updates the border indicating selected/not selected"""
        if self.posdict[(posy, posx)]['select']:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("QLabel {border: 3px solid rgb(240, 198, 0)}")
            self.posdict[(posy, posx)]['select'] = False
        else:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("QLabel {border: 3px solid rgb(255,255,255)}")
            self.posdict[(posy, posx)]['select'] = True


class Pystamps(QtGui.QMainWindow):
    """Holds the tool bars and actions. Makes images clickable."""
    def __init__(self):
        super(Pystamps, self).__init__()
        self.disp = DisplayImages()
        self.pystamps()
        self.all_count = 0

    def pystamps(self):
        # Create Scroll Bar
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidget(self.disp)
        fwidth = self.disp.frame_width
        psize = self.disp.psize
        rows = self.disp.grid.rowCount()
        tool_bar_w = self.disp.tool_bar_w
        min_frame_size = (fwidth + tool_bar_w * 2. + 30,
                          (psize + tool_bar_w) * 3)
        if rows <= 3:
            scrollArea.setMinimumSize(fwidth + tool_bar_w * 2. + 30,
                                      (psize + tool_bar_w) * rows)
        else:
            scrollArea.setMinimumSize(min_frame_size[0], min_frame_size[1])
        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Set Bakcground to be black
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(palette)

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
        self.setCentralWidget(scrollArea)
        self.show()

    def mousePressEvent(self, QMousEvent):
        psize = int(self.disp.psize)
        self.X = (QMousEvent.x() - (15+((QMousEvent.x()/psize)*10)))/psize
        self.Y = (QMousEvent.y() - (15+((QMousEvent.x()/psize)*10)))/psize
        try:
            self.disp.select_image(self.Y, self.X)
        except:
            pass

    def print_file(self):
        for item in self.disp.posdict:
            if self.disp.posdict[item]['select']:
                print os.path.abspath(self.disp.posdict[item]['name'])
            else:
                pass
        print ""

    def select_all(self):
        if self.all_count % 2 == 0:
            for item in self.disp.posdict:
                self.disp.posdict[item]['select'] = False
                self.disp.select_image(item[0], item[1])
        else:
            for item in self.disp.posdict:
                self.disp.posdict[item]['select'] = True
                self.disp.select_image(item[0], item[1])
        self.all_count += 1

    # TODO make window resizable and wrap images


def main():

    app = QtGui.QApplication(sys.argv)
    ex = Pystamps()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
