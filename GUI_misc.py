#! /usr/bin/python3

from PyQt5.QtWidgets import QDesktopWidget 

def center(self):
	# Copied this function from https://gist.github.com/saleph/163d73e0933044d0e2c4
	# Getting to lazy to research it myself.
	
	# geometry of the main window
	window_geometry = self.frameGeometry()

	# center point of screen
	center_point = QDesktopWidget().availableGeometry().center()

	# move rectangle's center point to screen's center point
	window_geometry.moveCenter(center_point)

	# top left of rectangle becomes top left of window centering it
	self.move(window_geometry.topLeft())
