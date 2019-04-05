#! /usr/bin/python3

from PyQt5.QtWidgets import QDesktopWidget, QDialog, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import QStandardPaths, QDir, QSettings
from PyQt5.QtNetwork import QNetworkInterface
import re

settings = QSettings("SeriesTracker", "SeriesTracker")

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

def init_settings():
	# Sets settings that are used.
	# Path to database location is set in database.py
	
	cover_folder = QStandardPaths.standardLocations(QStandardPaths.GenericDataLocation)[0] + "/SeriesTracker/covers/" # Path to a folder where show covers will be saved.
	
	settings.setValue("width", 1200)
	settings.setValue("height", 800)
	settings.setValue("coverDir", cover_folder)
	
	QDir().mkpath(settings.value("coverDir")) # Creates a path to cover folder

def has_internet_connection():
	# Checks if there is an internet conncetion and returns True or False appropriately.
	
	ct = 0 
	
	for interface in QNetworkInterface().allInterfaces():
		if (bool(interface.flags() & QNetworkInterface().IsUp and not interface.flags() & QNetworkInterface().IsLoopBack)) == True:
			ct += 1
	
	if ct > 0: # This may give some problems in the future
		return True
	else:
		return False

class CheckInternet(QDialog):
	# Prompts user with a message that is passed to this class.
	# Has only one button "OK"
	
	def __init__(self, message):
		super(CheckInternet, self).__init__()
		self.message = message
		self.initUI()
		
	def initUI(self):
		self.setModal(True)
		self.layout = QVBoxLayout()
		message_label = QLabel(self.message)
		
		button_ok = QPushButton("OK")
		button_ok.clicked.connect(self.accept)
		
		self.layout.addWidget(message_label)
		self.layout.addWidget(button_ok)
		self.setLayout(self.layout)
		self.show()
