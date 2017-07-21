#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from functools import wraps

import pytest
from qtpy import QtWidgets, QtCore

from pystamps import pystamps

FILE_1 = os.path.join(
    'tests', 'mission_data', '2m132591087cfd1800p2977m2f1.img')
FILE_2 = os.path.join(
    'tests', 'mission_data', '2p129641989eth0361p2600r8m1.img')
FILE_3 = os.path.join(
    'tests', 'mission_data', '1p190678905erp64kcp2600l8c1.img')
FILE_4 = os.path.join(
    'tests', 'mission_data', 'r01090al.img')
FILE_5 = os.path.join(
    'tests', 'mission_data', '1p134482118erp0902p2600r8m1.img')
FILE_6 = os.path.join(
    'tests', 'mission_data', 'h58n3118.img')
FILE_7 = os.path.join(
    'tests', 'mission_data', '0047MH0000110010100214C00_DRCL.IMG')
TEST_DIR = [FILE_1, FILE_2, FILE_3, FILE_4, FILE_5, FILE_6, FILE_7]


class TestImageStamp(object):

    stamp1 = pystamps.ImageStamp(FILE_2, 0, 1)
    stamp2 = pystamps.ImageStamp(FILE_7, 10, 342)

    def test_ImageStamp_1(self):
        stamp = self.stamp1
        assert stamp.file_name == FILE_2
        assert stamp.row == 0
        assert stamp.column == 1
        assert not stamp._selected
        assert stamp.pds_compatible
        assert stamp.basename == os.path.basename(FILE_2)
        assert stamp.abspath == os.path.abspath(FILE_2)
        assert isinstance(stamp.button, pystamps.ImageButton)
        assert isinstance(stamp.container, QtWidgets.QLabel)
        assert isinstance(stamp.title, QtWidgets.QLabel)
        assert isinstance(stamp.proxy_widget, QtWidgets.QGraphicsProxyWidget)

    def test_ImageStamp_2(self):
        stamp = self.stamp2
        assert stamp.file_name == FILE_7
        assert stamp.row == 10
        assert stamp.column == 342
        assert not stamp.pds_compatible
        assert not stamp._selected
        assert stamp.pds_image is None
        assert stamp.basename == os.path.basename(FILE_7)
        assert stamp.abspath == os.path.abspath(FILE_7)
        assert stamp.button is None
        assert stamp.container is None
        assert stamp.title is None
        assert stamp.proxy_widget is None

    def test_display_selected(self):
        stamp = self.stamp1
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        stamp.display_selected()
        assert stamp.container.styleSheet() == pystamps.SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_SELECTED
        stamp.container.setStyleSheet(pystamps.NOT_SELECTED)
        stamp.title.setStyleSheet(pystamps.TITLE_NOT_SELECTED)
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED

        with pytest.raises(RuntimeError):
            self.stamp2.display_selected()

    def test_display_not_selected(self):
        stamp = self.stamp1
        stamp.container.setStyleSheet(pystamps.SELECTED)
        stamp.title.setStyleSheet(pystamps.TITLE_SELECTED)
        assert stamp.container.styleSheet() == pystamps.SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_SELECTED
        stamp.display_not_selected()
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED

        with pytest.raises(RuntimeError):
            self.stamp2.display_not_selected()

    def test_selected(self):
        stamp = self.stamp1
        assert stamp.selected == stamp._selected
        assert not stamp.selected
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        stamp.selected = True
        assert stamp.container.styleSheet() == pystamps.SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_SELECTED
        stamp.selected = False
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED

    def test_create_button(self):
        stamp = self.stamp1
        stamp._create_button()
        assert isinstance(stamp.button, pystamps.ImageButton)
        assert isinstance(stamp.container, QtWidgets.QLabel)
        assert stamp.container.parent() == stamp.button
        assert stamp.container.styleSheet() == pystamps.NOT_SELECTED

        with pytest.raises(RuntimeError):
            self.stamp2._create_button()

    def test_create_title(self):
        stamp = self.stamp1
        stamp._create_title()
        assert isinstance(stamp.title, QtWidgets.QLabel)
        assert stamp.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        assert stamp.title.parent() == stamp.button
        assert stamp.title.font().family() == 'Helvetica'
        title_text = stamp.title.text()
        title_metrics = stamp.title.fontMetrics()
        title_width = title_metrics.boundingRect(title_text).width()
        assert title_width <= pystamps.PSIZE

        with pytest.raises(RuntimeError):
            self.stamp2._create_title()

    def test_create_proxy_widget(self):
        stamp = self.stamp1
        stamp._create_proxy_widget()
        assert isinstance(stamp.proxy_widget, QtWidgets.QGraphicsProxyWidget)
        assert stamp.proxy_widget.widget() == stamp.button

        with pytest.raises(RuntimeError):
            self.stamp2._create_proxy_widget()


class TestImageSet(object):
    image_set = pystamps.ImageSet(TEST_DIR)

    def test_init(self):
        assert self.image_set._views == set()
        assert isinstance(self.image_set.images, list)
        assert len(self.image_set.images) == 5
        assert isinstance(self.image_set.images[0], pystamps.ImageStamp)
        assert self.image_set.columns == 4
        assert isinstance(self.image_set.selected_images, list)
        assert len(self.image_set.selected_images) == 0
        assert self.image_set.images[0].row == 0
        assert self.image_set.images[0].column == 0
        assert self.image_set.images[3].row == 0
        assert self.image_set.images[3].column == 3
        assert self.image_set.images[4].row == 1
        assert self.image_set.images[4].column == 0

    def test_set_image_selected(self):
        assert not self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 0
        self.image_set.set_image_selected(self.image_set.images[0])
        assert self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 1
        self.image_set.set_image_selected(self.image_set.images[1])
        assert self.image_set.images[0].selected
        assert self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 2
        self.image_set.images[0].selected = False
        self.image_set.images[1].selected = False
        self.image_set.selected_images = []
        assert not self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 0

    def test_set_image_not_selected(self):
        self.image_set.images[0].selected = True
        self.image_set.images[1].selected = True
        self.image_set.selected_images = self.image_set.images[:2]
        assert self.image_set.images[0].selected
        assert self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 2
        self.image_set.set_image_not_selected(self.image_set.images[0])
        assert not self.image_set.images[0].selected
        assert self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 1
        self.image_set.set_image_not_selected(self.image_set.images[1])
        assert not self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 0

    @pytest.mark.parametrize(
        "columns, expected_positions",
        [
            (4, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)]),
            (3, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]),
            (2, [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]),
            (1, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]),
            (4, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)]),
        ])
    def test_set_images_positions(self, columns, expected_positions):
        self.image_set.columns = columns
        self.image_set.set_images_positions()
        for image, pos in zip(self.image_set.images, expected_positions):
            assert (image.row, image.column) == pos


class TestImageSetController(object):
    image_set = pystamps.ImageSet(TEST_DIR)
    controller = pystamps.ImageSetController(image_set, None)

    def test_init(self):
        assert self.controller.model == self.image_set
        assert self.controller.view is None

    def test_select_image(self):
        assert not self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 0
        self.controller.select_image(self.image_set.images[0])
        assert self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 1
        self.controller.select_image(self.image_set.images[1])
        assert self.image_set.images[0].selected
        assert self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 2
        self.controller.select_image(self.image_set.images[0])
        assert not self.image_set.images[0].selected
        assert self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 1
        self.controller.select_image(self.image_set.images[1])
        assert not self.image_set.images[0].selected
        assert not self.image_set.images[1].selected
        assert len(self.image_set.selected_images) == 0

    def test_select_all_unselect_all(self):
        def check_selected(expected_state, expected_length):
            for image in self.image_set.images:
                assert image.selected is expected_state
            assert len(self.image_set.selected_images) == expected_length

        check_selected(False, 0)
        self.controller.select_all()
        check_selected(True, 5)
        self.controller.select_all()
        check_selected(True, 5)
        self.controller.unselect_all()
        check_selected(False, 0)
        self.controller.unselect_all()
        check_selected(False, 0)

    @pytest.mark.parametrize(
        "new_columns, expected_positions",
        [
            (4, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)]),
            (3, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)]),
            (2, [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]),
            (1, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]),
            (4, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)]),
        ])
    def test_wrap_images(self, new_columns, expected_positions):
        self.controller.wrap_images(new_columns)
        for image, pos in zip(self.image_set.images, expected_positions):
            assert (image.row, image.column) == pos


class TestImageButton(object):
    stamp = pystamps.ImageStamp(FILE_2, 0, 1)
    button = pystamps.ImageButton(stamp)
    __mouse_press_cought = False

    def test_init(self):
        assert self.button.parent is None
        assert self.button.image_stamp == self.stamp
        size = QtCore.QSize(int(pystamps.PSIZE), int(pystamps.PSIZE))
        assert self.button.size() == size

    def check_catch_button_press(self, image_stamp):
        assert isinstance(image_stamp, pystamps.ImageStamp)
        assert image_stamp == self.stamp
        assert image_stamp == self.button.image_stamp
        self.__mouse_press_cought = True

    def test_mouseReleaseEvent(self, qtbot):
        self.__mouse_press_cought = False
        qtbot.addWidget(self.button)
        self.button.clicked.connect(self.check_catch_button_press)
        qtbot.mouseClick(self.button, QtCore.Qt.LeftButton)
        assert self.__mouse_press_cought


class TestImageSetView(object):
    image_set = pystamps.ImageSet(TEST_DIR)
    view = pystamps.ImageSetView(image_set)

    def test_init(self):
        assert self.view.image_set == self.image_set
        assert self.view in self.image_set._views
        assert isinstance(self.view.controller, pystamps.ImageSetController)
        assert self.view.images == self.image_set.images
        # assert isinstance(self.view.scene, QtWidgets.QGraphicsScene)
        assert isinstance(self.view.grid, QtWidgets.QGraphicsGridLayout)
        assert self.view.grid.maximumWidth() == pystamps.PSIZE
        assert isinstance(
            self.view.layout_container, QtWidgets.QGraphicsWidget)
        assert self.view.layout_container.layout() == self.view.grid
        assert self.view.layout_container in self.view.scene().items()
        assert self.view.backgroundBrush() == QtCore.Qt.black

    def test_select_image(self, qtbot):
        self.view.show()
        qtbot.addWidget(self.view)
        image1 = self.image_set.images[0]
        assert not image1.selected
        assert image1.container.styleSheet() == pystamps.NOT_SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        qtbot.mouseClick(image1.button, QtCore.Qt.LeftButton)
        assert image1.selected
        assert image1.container.styleSheet() == pystamps.SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_SELECTED
        qtbot.mouseClick(image1.button, QtCore.Qt.LeftButton)
        assert not image1.selected
        assert image1.container.styleSheet() == pystamps.NOT_SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        image5 = self.image_set.images[4]
        assert not image5.selected
        assert image5.container.styleSheet() == pystamps.NOT_SELECTED
        assert image5.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        qtbot.mouseClick(image5.button, QtCore.Qt.LeftButton)
        assert image5.selected
        assert image5.container.styleSheet() == pystamps.SELECTED
        assert image5.title.styleSheet() == pystamps.TITLE_SELECTED
        assert not image1.selected
        assert image1.container.styleSheet() == pystamps.NOT_SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        qtbot.mouseClick(image1.button, QtCore.Qt.LeftButton)
        assert image5.selected
        assert image5.container.styleSheet() == pystamps.SELECTED
        assert image5.title.styleSheet() == pystamps.TITLE_SELECTED
        assert image1.selected
        assert image1.container.styleSheet() == pystamps.SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_SELECTED
        qtbot.mouseClick(image5.button, QtCore.Qt.LeftButton)
        assert not image5.selected
        assert image5.container.styleSheet() == pystamps.NOT_SELECTED
        assert image5.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        assert image1.selected
        assert image1.container.styleSheet() == pystamps.SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_SELECTED
        qtbot.mouseClick(image1.button, QtCore.Qt.LeftButton)
        assert not image5.selected
        assert image5.container.styleSheet() == pystamps.NOT_SELECTED
        assert image5.title.styleSheet() == pystamps.TITLE_NOT_SELECTED
        assert not image1.selected
        assert image1.container.styleSheet() == pystamps.NOT_SELECTED
        assert image1.title.styleSheet() == pystamps.TITLE_NOT_SELECTED

    def test_set_grid_layout(self):
        def check_grid(positions):
            for pos, image in zip(positions, self.image_set.images):
                row, col = pos
                assert self.view.grid.itemAt(row, col) == image.proxy_widget
        check_grid([(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)])
        # wrap_images will eventually call set_grid_layout
        self.view.controller.wrap_images(3)
        check_grid([(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)])
        self.view.controller.wrap_images(2)
        check_grid([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)])
        self.view.controller.wrap_images(1)
        check_grid([(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)])
        self.view.controller.wrap_images(5)
        check_grid([(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)])
        self.view.controller.wrap_images(4)
        check_grid([(0, 0), (0, 1), (0, 2), (0, 3), (1, 0)])


class TestMainWindow(object):
    image_set = pystamps.ImageSet(TEST_DIR)
    window = pystamps.MainWindow(image_set)

    def add_window_wrapper(func):
        @wraps(func)
        def wrapper(self, qtbot):
            self.window.show()
            qtbot.addWidget(self.window)
            return func(self, qtbot)
        return wrapper

    @add_window_wrapper
    def test_select_all(self, qtbot):
        def check_selected(expected_state, expected_length):
            for image in self.image_set.images:
                assert image.selected is expected_state
            assert len(self.image_set.selected_images) == expected_length

        select_all_widget = self.window.toolbar.widgetForAction(
            self.window.select_all_action)

        check_selected(False, 0)
        assert not self.window.selected_all_toggle
        qtbot.mouseClick(select_all_widget, QtCore.Qt.LeftButton)
        assert self.window.selected_all_toggle
        check_selected(True, 5)
        qtbot.mouseClick(select_all_widget, QtCore.Qt.LeftButton)
        assert not self.window.selected_all_toggle
        check_selected(False, 0)
        qtbot.mouseClick(select_all_widget, QtCore.Qt.LeftButton)
        assert self.window.selected_all_toggle
        check_selected(True, 5)
        qtbot.mouseClick(select_all_widget, QtCore.Qt.LeftButton)
        assert not self.window.selected_all_toggle
        check_selected(False, 0)

    @pytest.mark.skipif(not pystamps.PDSVIEW_INSTALLED,
                        reason="PDSView not installed")
    @add_window_wrapper
    def test_open_pdsview(self, qtbot):
        open_pdsview_widget = self.window.toolbar.widgetForAction(
            self.window.view_action)

        assert self.window._pdsviewer is None
        qtbot.addWidget(self.window.set_view)
        qtbot.mouseClick(
            self.window.set_view.images[0].button, QtCore.Qt.LeftButton)
        qtbot.mouseClick(open_pdsview_widget, QtCore.Qt.LeftButton)
        assert self.window._pdsviewer is not None
        qtbot.addWidget(self.window._pdsviewer)
        self.window._pdsviewer.close()
        qtbot.mouseClick(
            self.window.set_view.images[0].button, QtCore.Qt.LeftButton)

    @add_window_wrapper
    def test_resizeEvent(self, qtbot):
        default_width = self.window.width()
        images = self.window.images
        # Travis automatically resizes the window and then deletes the window
        # so resizing cannot test on Travis
        if (images[4].row, images[4].column) == (0, 4):
            pass
        else:
            # Test that items are correct before resize
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[4].row, images[4].column) == (1, 0)
            # Test items move to the right place after resizing window larger
            self.window.resize(
                default_width + default_width / 4, self.window.height())
            assert self.window.width() > default_width
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[4].row, images[4].column) == (0, 4)
            self.window.resize(
                self.window.width() + default_width / 4, self.window.height())
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[4].row, images[4].column) == (0, 4)
            # Test items move to right place after resizing window smaller
            self.window.resize(
                self.window.width() - default_width / 4, self.window.height())
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[4].row, images[4].column) == (0, 4)
            self.window.resize(
                self.window.width() - 3 * (default_width / 4),
                self.window.height())
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[1].row, images[1].column) == (0, 1)
            assert (images[2].row, images[2].column) == (1, 0)
            assert (images[3].row, images[3].column) == (1, 1)
            assert (images[4].row, images[4].column) == (2, 0)
            self.window.resize(default_width, self.window.height())
            assert (images[0].row, images[0].column) == (0, 0)
            assert (images[1].row, images[1].column) == (0, 1)
            assert (images[2].row, images[2].column) == (0, 2)
            assert (images[3].row, images[3].column) == (0, 3)
            assert (images[4].row, images[4].column) == (1, 0)
