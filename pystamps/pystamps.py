# -*- coding: utf-8 -*-

import sys
from PySide import QtGui, QtCore
import os
from planetaryimage import PDS3Image
from qimage2ndarray import gray2qimage
from glob import glob
import math


# class ImageStamp(object):
#     def __init__(filename):
#         self.file_name = filename
#         self.pdsimage = PDS3Image.open(filename)
#         self.pixmap = ...
#         self.selected = False

#     def __repr__():
#         return self.file_name


# class ImageSet(object):
#     def __init__(inlist):
#         self.images = []
#         for image in inlist:
#             self.images.append(ImageStamp(image))

#     def selected():
#         selected_images = []
#         for image in self.images:
#             if image.selected:
#                 selected_images.append(image)
#         return selected_images


class DisplayImages(QtGui.QGraphicsView):
    """Displays images in the main widget window with a border marking them as
    selected (white) or unselected (yellow)"""

    def __init__(self):
        super(DisplayImages, self).__init__()
        self.scene = QtGui.QGraphicsScene()
        self.grid = QtGui.QGraphicsGridLayout()
        self.yellow_pen = QtGui.QPen(QtCore.Qt.yellow)
        self.white_pen = QtGui.QPen(QtCore.Qt.white)
        self.yellow_pen.setWidth(10)
        self.white_pen.setWidth(10)
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
        for file_name in self.file_names:
            try:
                pdsimage = PDS3Image.open(file_name)
                image = gray2qimage(pdsimage.data, True)
                self.pixmap = QtGui.QPixmap.fromImage(image)
                self.pixmap = self.pixmap.scaled(self.psize, self.psize,
                                                 QtCore.Qt.KeepAspectRatio)
                self.Gpic = QtGui.QLabel()
                self.Gpic.setPixmap(self.pixmap)
                self.Gpic.setStyleSheet("""QLabel {background-color: black;
                                        border: 4px solid rgb(240, 198, 0)}""")
                self.picture = QtGui.QGraphicsProxyWidget()
                self.picture.setWidget(self.Gpic)
                self.picture.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
                self.picture.setMaximumSize(self.psize, self.psize)
                self.picture.setMinimumSize(self.psize, self.psize)
                self.grid.setColumnFixedWidth(0, self.psize)
                self.grid.setRowFixedHeight(0, self.psize)
                self.grid.addItem(self.picture, x, y, QtCore.Qt.AlignCenter)
                self.posdict[(x, y)] = {'name': file_name,
                                        'pict': self.Gpic, 'select': False}
                y += 1
                if y == 4:
                    x += 1
                    y = 0
            except:
                pass
        form = QtGui.QGraphicsWidget()
        form.setLayout(self.grid)
        self.scene.addItem(form)
        self.setScene(self.scene)
        self.setBackgroundBrush(QtCore.Qt.black)
        self.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def select_image(self, posy, posx):
        """Updates the border indicating selected/not selected"""
        if self.posdict[(posy, posx)]['select']:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("""QLabel {background-color: black;
                               border: 4px solid rgb(240, 198, 0)}""")
            self.posdict[(posy, posx)]['select'] = False
        else:
            pict = self.posdict[(posy, posx)]['pict']
            pict.setStyleSheet("""QLabel {background-color: black;
                               border: 4px solid rgb(255, 255, 255)}""")
            self.posdict[(posy, posx)]['select'] = True


class Pystamps(QtGui.QMainWindow):
    """Holds the tool bars and actions. Makes images clickable."""
    def __init__(self):
        super(Pystamps, self).__init__()
        self.disp = DisplayImages()
        self.pystamps()
        self.all_count = 0

    def pystamps(self):
        fwidth = self.disp.frame_width
        psize = self.disp.psize
        tool_bar_w = self.disp.tool_bar_w
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
        psize = int(self.disp.psize)
        self.X = (QMousEvent.x() - (15+((QMousEvent.x()/psize)*10)))/psize
        self.Y = (QMousEvent.y() - (15+((QMousEvent.x()/psize)*10)))/psize
        try:
            self.disp.select_image(self.Y, self.X)
        except:
            pass

    def QGraphicsSceneMouseEvent(self):
        print "Mouse Lcikc"

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