===============================
pystamps
===============================

.. image:: https://img.shields.io/travis/pbvarga1/pystamps.svg
        :target: https://travis-ci.org/pbvarga1/pystamps

.. image:: https://img.shields.io/pypi/v/pystamps.svg
        :target: https://pypi.python.org/pypi/pystamps


pystamps is the python equivalnlent of mer_stamps in idl

* Free software: BSD license
* Documentation: https://pystamps.readthedocs.org.

Features
--------

* This is a still a work in progress

* Current available features:

    * Display Images

    * Select Images

    * Print Image paths

    * Resize window and wrap images

    * Command Line arguments

        * pystamps

            * Displays all pds compatible images in current directory

        * pystamps [filename or glob]

            * Displays single image or all images matching glob that are PDS
              compatible

    * pdsview

        * Needs install first:

            * pip install pdsview


Install
--------

* git clone git@github.com:planetarypy/pystamps.git

* pip install -r requirements.txt

* pyside_postinstall.py -install
