#! /usr/bin/python3

from PyQt5.QtWidgets import QDesktopWidget
import re

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

# Regex pattern that is used to detect IMDB_id.
pattern_to_look_for = re.compile("tt\d+")

# This function checks user input and returns False if does not contain IMDB_id or returns string with IMDB_id if it does.
def check_if_input_contains_IMDB_id(user_input):
    if pattern_to_look_for.search(user_input):
        if len(pattern_to_look_for.search(user_input)[0]) == 9:
            return pattern_to_look_for.search(user_input)[0]
    else:
        return False
