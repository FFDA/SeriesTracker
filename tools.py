#! /usr/bin/python3

import datetime
import tarfile
import re
from os import listdir

from PyQt5.QtCore import QSettings, Qt, QStandardPaths, QDir
from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QLabel, QCheckBox, QProgressBar, QGroupBox, QHBoxLayout, QFileDialog, QStyleFactory, QComboBox, QApplication

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
		self.setWindowTitle("Create Backup")
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
		if location != "":
			backup_filename = "SeriesTracker_" + datetime.datetime.today().strftime("%Y-%m-%d_%H-%M") + ".tar.gz"
			self.destination_line_edit.setText(location + QDir.separator() + backup_filename)
			self.enable_backup_botton()
		else:
			return
	
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

class RestoreWindow(QDialog):
	# Opens window that allows user to restore database, covers and settings file from backup file.
	def __init__(self):
		super(RestoreWindow, self).__init__()
		self.initUI()
		
	def initUI(self):
		self.resize(600, 200)
		self.setModal(True)
		self.setWindowTitle("Backup Restore")
		self.layout = QGridLayout()
		
		destination_label = QLabel("Choose restore file")
		destination_label.setAlignment(Qt.AlignCenter)
		self.destination_line_edit = QLineEdit()
		self.destination_line_edit.setReadOnly(True)
		self.destination_choose_button = QPushButton("Choose")
		self.destination_choose_button.clicked.connect(self.choose_restore_file)
		
		self.progress = QProgressBar()
		self.progress.setMinimum(0)
		
		self.button_restore = QPushButton("Restore")
		self.button_restore.setEnabled(False)
		self.button_restore.clicked.connect(self.restore)
		self.button_close = QPushButton("Close")
		self.button_close.clicked.connect(self.accept)
		
		self.layout.addWidget(destination_label, 0, 0, 1, 8)
		self.layout.addWidget(self.destination_line_edit, 1, 0, 1, 7)
		self.layout.addWidget(self.destination_choose_button, 1, 7, 1, 1)
		self.layout.addWidget(self.progress, 2, 0, 1, 8)
		self.layout.addWidget(self.button_restore, 3, 6, 1, 1)
		self.layout.addWidget(self.button_close, 3, 7, 1, 1)
		
		self.setLayout(self.layout)
		self.show()
		
		print()

	def choose_restore_file(self):
		# Display a dialog box to user to choose a location where backup file will be saved.
		# filters files to show files with tar.gz extension.
		location_home = QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0]
		backup_file = QFileDialog.getOpenFileName(self, "Backup file", location_home, "Backup (SeriesTracker*.tar.gz)")[0]
		if backup_file != "":
			self.destination_line_edit.setText(backup_file)
			self.button_restore.setEnabled(True)
		else:
			return

	def restore(self):
		# Restores data from back by going though backup file and checking whats inside and restoring it to appropriate location.
		cover_re_match = re.compile("tt([\d]+\.jpg)")
		progress_count = 0
		
		backup_file = tarfile.open(self.destination_line_edit.text(), "r:gz") # Opens chosen backup file
		self.progress.setMaximum(len(backup_file.getnames()) + 2) # Set progress_bar value to the item count of backup file + 2
		
		progress_count += 1
		self.progress.setValue(progress_count)
		
		for item in backup_file.getnames():
			if cover_re_match.search(item) != None:
				# Extracts covers
				backup_file.extract(item, QStandardPaths.standardLocations(QStandardPaths.GenericDataLocation)[0] + "/SeriesTracker/")
			elif item == "SeriesTracker.conf":
				# Extracts settings
				backup_file.extract(item, QStandardPaths.standardLocations(QStandardPaths.ConfigLocation)[0] + QDir.separator() + "SeriesTracker" + QDir.separator())
			elif item == "shows.db":
				# Extracts database
				backup_file.extract(item, re.sub("shows.db", "", settings.value("DB_path")))
			
			progress_count += 1
			self.progress.setValue(progress_count)

		backup_file.close()
		progress_count += 1
		self.progress.setValue(progress_count)

class SettingsWindow(QDialog):

	def __init__(self):
		super(SettingsWindow, self).__init__()
		self.initUI()

	def initUI(self):
		self.layout = QGridLayout()
		#self.resize(800, 500)
		self.setModal(True)
		self.setWindowTitle("Settings")

		self.style_list = list(map(lambda x: x.lower(), QStyleFactory().keys())) # Getting all available style for Qt5 application and making it to lower case list.

		### Creating layout for "Style" portion of the Settings
		box_style = QGroupBox("Style")
		box_style.layout = QHBoxLayout()
		self.combo_box_style = QComboBox()
		self.combo_box_style.setFocusPolicy(Qt.NoFocus)
		self.combo_box_style.addItems(self.style_list)
		self.combo_box_style.setCurrentText(settings.value("currentStyle")) # Setting combo box value to the value that is saved in settings.
		self.combo_box_style.currentTextChanged.connect(self.change_style)
		box_style.layout.addWidget(self.combo_box_style)
		box_style.setLayout(box_style.layout)

		### Creating layout for "Playback" portion of the settings
		# Choosing root directory of shows folder.
		playback_message = QLabel("Choose directory where you keep all your shows")
		playback_message.setAlignment(Qt.AlignHCenter)
		self.playback_line_edit = QLineEdit()
		self.playback_line_edit.setReadOnly(True)
		if settings.contains("videoDir"):
			# If settings has a value for videoDir path to that dir will be set in to the line_edit
			self.playback_line_edit.setText(settings.value("videoDir"))
		self.playback_line_edit.setPlaceholderText("Choose root folder of all shows")
		button_playback_choose = QPushButton("Choose")
		button_playback_choose.setFocusPolicy(Qt.NoFocus)
		button_playback_choose.clicked.connect(self.choose_video_directory) # Launches window to choose directory where user keeps shows.

		# Choosing media player.
		self.combo_box_media_player = QComboBox()
		self.combo_box_media_player.setFocusPolicy(Qt.NoFocus)
		self.combo_box_media_player_list = ["", "vlc", "mpv"]
		self.combo_box_media_player.addItems(self.combo_box_media_player_list)
		if settings.contains("videoPlayer"):
			# If videoPlayer value already exists in settings that value will be set in combo_box
			self.combo_box_media_player.setCurrentText(settings.value("videoPlayer"))
		self.combo_box_media_player.currentTextChanged.connect(self.change_player)

		# Setting "Playback" layout
		box_playback = QGroupBox("Playback")
		box_playback.layout = QGridLayout()
		box_playback.layout.addWidget(playback_message, 0, 0, 1, 6)
		box_playback.layout.addWidget(self.playback_line_edit, 1, 0, 1, 5)
		box_playback.layout.addWidget(button_playback_choose, 1, 5, 1, 1)
		box_playback.layout.addWidget(self.combo_box_media_player, 2, 0, 1, 6)
		box_playback.setLayout(box_playback.layout)

		### Main buttons and other layout stuff
		self.button_cancel = QPushButton("Cancel")
		self.button_cancel.setFocusPolicy(Qt.NoFocus)
		self.button_cancel.clicked.connect(self.reject)
		self.button_apply = QPushButton("Apply")
		self.button_apply.setFocusPolicy(Qt.NoFocus)
		self.button_apply.setEnabled(False)
		self.button_apply.clicked.connect(self.apply_changes)
		self.button_ok = QPushButton("Ok")
		self.button_ok.setFocusPolicy(Qt.NoFocus)
		self.button_ok.clicked.connect(self.clicked_ok)

		self.layout.addWidget(box_style, 0, 0, 1, 6)
		self.layout.addWidget(box_playback, 1, 0, 2, 6)
		self.layout.addWidget(self.button_cancel, 4, 0, 1, 1)
		self.layout.addWidget(self.button_apply, 4, 4, 1, 1)
		self.layout.addWidget(self.button_ok, 4, 5, 1, 1)
		self.setLayout(self.layout)
		self.show()

	def change_style(self, style):
		# Simply checks if selected style maches with the current one.
		# If it doesn't enables "Apply" button.
		if style != settings.value("currentStyle"):
			self.button_apply.setEnabled(True)
		else:
			self.button_apply.setEnabled(False)
	
	def choose_video_directory(self):
		# Displays a window for user to choose a directory where (s)he keeps shows.
		location_home = QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0]
		video_dir = QFileDialog.getExistingDirectory(self, "Choose directory", location_home)
		if video_dir != "": # If user cancels window instead of choosing a catalog dialog window returns empty sting. In that case nothing happens.
			# Set path to chosen directory to the line_edit and enabled apply button.
			self.playback_line_edit.setText(video_dir)
			self.button_apply.setEnabled(True)
	
	def change_player(self, player):
		# Enables "Apply button if user choose new player"
		if player != settings.value("videoPlayer"):
			self.button_apply.setEnabled(True)
		else:
			self.button_apply.setEnabled(False)
	
	def apply_changes(self):
		if settings.value("currentStyle") != self.combo_box_style.currentText():
			# Changes style and saves it to settings
			QApplication.setStyle(self.combo_box_style.currentText())
			settings.setValue("currentStyle", self.combo_box_style.currentText())
		if settings.value("videoDir") != self.playback_line_edit.text():
			# Saves chosen dir to settings
			settings.setValue("videoDir", self.playback_line_edit.text())
		if settings.value("videoPlayer") != self.combo_box_media_player.currentText():
			settings.setValue("videoPlayer", self.combo_box_media_player.currentText())
		self.button_apply.setEnabled(False) # Disables "Apply" button.
		
	def clicked_ok(self):
		# Combines apply changes and closes window with accept signal.
		self.apply_changes()
		self.accept()