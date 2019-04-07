#! /usr/bin/python3

import datetime
import tarfile
from os import listdir

from PyQt5.QtCore import QSettings, Qt, QStandardPaths, QDir
from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QLabel, QCheckBox, QProgressBar, QGroupBox, QHBoxLayout, QFileDialog

settings = QSettings("SeriesTracker", "SeriesTracker")

class BackupWindow(QDialog):
	# This displays a QDialog window that allows user to choose what (s)he want's to backup.
	# User can choose to backup database, covers and settings file.
	# Backup is placed in tar.gz file thats name SeriesTracker_[datetime].tar.gz
	
	def __init__(self):
		super(BackupWindow, self).__init__()
		self.initUI()
		
	def initUI(self):
		self.resize(600, 200)
		self.setModal(True)
		self.layout = QGridLayout()
		
		destination_label = QLabel("Choose backup destination")
		destination_label.setAlignment(Qt.AlignCenter)
		self.destination_line_edit = QLineEdit()
		self.destination_line_edit.setReadOnly(True)
		self.destination_choose_button = QPushButton("Choose")
		self.destination_choose_button.clicked.connect(self.set_location)
		
		checkbox_group_box = QGroupBox("Choose what to backup")
		checkbox_group_box.layout = QHBoxLayout()
		checkbox_group_box.layout.setAlignment(Qt.AlignHCenter)
		self.checkbox_database = QCheckBox("Database")
		self.checkbox_database.setCheckState(Qt.Checked)
		self.checkbox_database.stateChanged.connect(self.enable_backup_botton)
		self.checkbox_covers = QCheckBox("Covers")
		self.checkbox_covers.setCheckState(Qt.Checked)
		self.checkbox_covers.stateChanged.connect(self.enable_backup_botton)
		self.checkbox_settings = QCheckBox("Settings")
		self.checkbox_settings.stateChanged.connect(self.enable_backup_botton)
		checkbox_group_box.layout.addWidget(self.checkbox_database)
		checkbox_group_box.layout.addWidget(self.checkbox_covers)
		checkbox_group_box.layout.addWidget(self.checkbox_settings)
		checkbox_group_box.setLayout(checkbox_group_box.layout)
		
		self.progress = QProgressBar()
		self.progress.setMinimum(0)
		self.progress.setMaximum(5)
		
		self.button_backup = QPushButton("Backup")
		self.button_backup.setEnabled(False)
		self.button_backup.clicked.connect(self.backup)
		self.button_close = QPushButton("Close")
		self.button_close.clicked.connect(self.accept)
		
		self.layout.addWidget(destination_label, 0, 0, 1, 8)
		self.layout.addWidget(self.destination_line_edit, 1, 0, 1, 7)
		self.layout.addWidget(self.destination_choose_button, 1, 7, 1, 1)
		self.layout.addWidget(checkbox_group_box, 2, 0, 1, 8)
		self.layout.addWidget(self.progress, 3, 0, 1, 8)
		self.layout.addWidget(self.button_backup, 8, 6, 1, 1)
		self.layout.addWidget(self.button_close, 8, 7, 1, 1)
				
		self.setLayout(self.layout)
		self.show()
		
	def set_location(self):
		# Displays user a dialog box to choose a location where backup file will be saved.
		# Appends file name that consists from program's name, date and extension.
		location_home = QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0]
		location = QFileDialog.getExistingDirectory(self, "Choose directory", location_home)
		backup_filename = "SeriesTracker_" + datetime.datetime.today().strftime("%Y-%m-%d_%H-%M") + ".tar.gz"
		self.destination_line_edit.setText(location + QDir.separator() + backup_filename)
		self.enable_backup_botton()
	
	def enable_backup_botton(self):
		# This function is executed everytime a state of checkbox is changed and to check if at least one of them is checked.
		# If there is at least one checkbox checked "Backup" buttons will be disabled.
		# If at least one checkbox is checked and there is text in self.destination_line_edit "Backup" button will be enabled
		
		if self.checkbox_database.checkState() == Qt.Unchecked and self.checkbox_covers.checkState() == Qt.Unchecked and self.checkbox_settings.checkState() == Qt.Unchecked or self.destination_line_edit.text() == "":
			self.button_backup.setEnabled(False)
		else:
			self.button_backup.setEnabled(True)
		
	def backup(self):
		# Does the actual backup.
		
		backup_file = tarfile.open(self.destination_line_edit.text(), "w:gz") # Opens a backup tar file
		self.progress.setValue(1)
		
		if self.checkbox_database.checkState() == Qt.Checked:
			# Executes if user chose to backup database.
			location_database = settings.value("DB_path") # Gets database location from settings file.
			backup_file.add(location_database, arcname="shows.db", recursive=False) # Adds database to archive.
			self.progress.setValue(2)
		if self.checkbox_covers.checkState() == Qt.Checked:
			# Executes is user chose to backup covers.
			location_covers = settings.value("coverDir") # Gets cover folder from settings file.
			backup_file.add(location_covers, arcname="covers", recursive=False) 
			for cover in listdir(path=location_covers): # List of all files in the directory.
				# Goes through the list if files and adds them one by one to /covers/ dir in archive
				backup_file.add(location_covers + QDir.separator() + cover, arcname="covers" + QDir.separator() + cover, recursive=False)
			self.progress.setValue(3)
		if self.checkbox_settings.checkState() == Qt.Checked:
			# Executes if user chose to backup settings file.
			location_settings = settings.fileName() # Gets location of settings file.
			backup_file.add(location_settings, arcname="SeriesTracker.conf", recursive=False) # Adds file to archive.
			self.progress.setValue(4)
			
		self.progress.setValue(5)
		
		backup_file.close() # Closes backup archive