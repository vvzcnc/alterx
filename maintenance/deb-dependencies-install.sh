#!/bin/sh

( exec apt install \
	git \
	python-pip \
	python-pyqt5 \
	python-pyqt5.qsci \
	python-pyqt5.qtopengl )

( pip install \
    vtk \
    crcmod \
    pyudev \
    serial \
    pyqtgraph \
    polib )
