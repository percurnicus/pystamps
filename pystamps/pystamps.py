# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
import os
from planetaryimage import PDS3Image
from qimage2ndarray import gray2qimage
from glob import glob


class DisplayImages(QtGui.QWidget):
    """Displays images in the main widget window with a border marking them as
    selected (white) or unselected (yellow)"""

    def __init__(self):
        super(DisplayImages, self).__init__()
        grid = QtGui.QGridLayout()
        x = 0.0
        y = 0.0
        self.X = 0
        self.Y = 0
        self.img_dict = {}
        self.posdict = {}
        pdsimages = []
        # TODO Expand the types of extensions to search for
        extensions = ['img', 'IMG']
        for ext in extensions:
            pdsimages = pdsimages + (glob('*%s' % (ext)))
        for file_name in pdsimages:
            pdsimage = PDS3Image.open(file_name)
            image = gray2qimage(pdsimage.data, True)
            pixmap = QtGui.QPixmap.fromImage(image)
            pixmap = pixmap.scaled(200, 200, QtCore.Qt.KeepAspectRatio)
            picture = QtGui.QLabel(self)
            picture.setPixmap(pixmap)
            picture.setStyleSheet("""QLabel {background-color: black;
                                  border: 3px solid rgb(240, 198, 0)}""")
            picture.setScaledContents(True)
            grid.addWidget(picture, x, y, QtCore.Qt.AlignCenter)
            grid.setGeometry(QtCore.QRect(x, y, 200, 200))
            self.posdict[(x, y)] = {'name': file_name, 'pict': picture,
                                    'select': False}
            y += 1.0
            if y == 4.0:
                x += 1.0
                y = 0.0

        self.setLayout(grid)

    def select_image(self, posy, posx):
        """Updates the border indicating selected/not selected"""
        if self.posdict[(posy, posx)]['select']:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("QLabel {border: 3px solid rgb(240, 198, 0)}")
            self.posdict[(posy, posx)]['select'] = False
            return self.posdict
        else:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("QLabel {border: 3px solid rgb(255,255,255)}")
            self.posdict[(posy, posx)]['select'] = True
            return self.posdict


class Pystamps(QtGui.QMainWindow):
    """Holds the tool bars and actions. Makes images clickable."""
    def __init__(self):
        super(Pystamps, self).__init__()
        self.disp = DisplayImages()
        self.pystamps()
        self.all_count = 0

    def pystamps(self):
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
        self.print_image_path = self.addToolBar('Print Selected Filenames')
        self.print_image_path.addAction(printAction)
        self.selectAll = self.addToolBar('Select All/None')
        self.selectAll.addAction(allAction)

        # Create status bar
        self.statusBar()

        self.setCentralWidget(self.disp)
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background, QtCore.Qt.black)
        self.setPalette(palette)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('pdsimage')
        self.show()

    def mousePressEvent(self, QMousEvent):
        # TODO Fix so supports correct clicks when window resized.
        # TODO Make Images Actually Clickable.
        self.X = (QMousEvent.x() - (15+((QMousEvent.x()/200)*10)))/200
        self.Y = (QMousEvent.y() - (15+((QMousEvent.x()/200)*10)))/200
        self.disp.select_image(self.Y, self.X)

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


def main():

    app = QtGui.QApplication(sys.argv)
    ex = Pystamps()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
