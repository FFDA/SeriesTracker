#! /usr/bin/python3

import datetime
import tarfile
import re
from os import listdir
from time import sleep
from imdbpie import Imdb

from PyQt5.QtCore import QSettings, Qt, QStandardPaths, QDir
from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QPushButton, QLabel, QCheckBox, QProgressBar, QGroupBox, QHBoxLayout, QFileDialog, QStyleFactory, QComboBox, QApplication, QTextEdit
from PyQt5.QtSql import QSqlQuery

from misc import check_if_input_contains_IMDB_id

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

class UpdateWatchlist(QDialog):
	
	def __init__(self):
		super(UpdateWatchlist, self).__init__()
		self.imdb = Imdb()
		self.initUI()

	def initUI(self):
		self.layout = QGridLayout()
		self.setModal(True)
		self.resize(600, 400)
		self.setWindowTitle("Update Watchlist")

		### Message for the user
		self.label_message = QLabel("This should be done rarely, because IMDB has some kind of protection against bots using their service and if it will be abused they might start block imdbpie")
		self.label_message.setWordWrap(True)
		self.label_message.setAlignment(Qt.AlignHCenter)
		###

		### Text Edit window, that displays info for the user
		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		###

		### Progress_bars.
		self.progress_bar_current = QProgressBar()
		self.progress_bar_current.setMinimum(0)
		self.progress_bar_overall = QProgressBar()
		self.progress_bar_overall.setMinimum(0)
		###

		### Buttons for the layout
		self.button_close = QPushButton("Close")
		self.button_close.setFocusPolicy(Qt.NoFocus)
		self.button_close.clicked.connect(self.reject)
		self.button_update = QPushButton("Update")
		self.button_update.setFocusPolicy(Qt.NoFocus)
		self.button_update.clicked.connect(self.update_watchlist)
		self.button_ok = QPushButton("OK")
		self.button_ok.setFocusPolicy(Qt.NoFocus)
		self.button_ok.clicked.connect(self.accept)
		self.button_ok.setEnabled(False)
		###

		### Adding items to layout
		self.layout.addWidget(self.label_message, 0, 0, 1, 4)
		self.layout.addWidget(self.info_box, 1, 0, 3, 4)
		self.layout.addWidget(self.progress_bar_current, 4, 0, 1, 4)
		self.layout.addWidget(self.progress_bar_overall, 5, 0, 1, 4)	
		self.layout.addWidget(self.button_close, 6, 0, 1, 1)
		self.layout.addWidget(self.button_update, 6, 2, 1, 1)
		self.layout.addWidget(self.button_ok, 6, 3, 1, 1)
		self.setLayout(self.layout)
		###

		self.show()

	def update_watchlist(self):
		# Gets shows that have to be updated and passes to other functions.
		# Takes care of progress_bar_overall.
		
		self.button_update.setEnabled(False)
		self.button_close.setEnabled(False)

		self.info_box.append("Starting to update Watchlist. This will take some time if there are a lot of shows.")
		self.info_box.append("")
		self.info_box.append("========================")

		watchlist = QSqlQuery("SELECT * FROM shows WHERE finished_watching = 0") # Fetches watchlist from DB
		watchlist.exec_()
		
		progress_count = 0

		count = QSqlQuery("SELECT COUNT(*) FROM shows WHERE finished_watching = 0") # How many shows there are in wtachlist
		count.exec_()
		count.first()
		watchlist_count = count.value(0)

		### Setting up progress bars
		self.progress_bar_overall.setMaximum(watchlist_count)
		self.progress_bar_current.setMaximum(9)
		###

		while watchlist.next():
			# Loops thought all the shows and updates show_info and last season. If show has unknown season it is updated too.
			self.progress_bar_current.setValue(0)

			self.IMDB_id = watchlist.value("IMDB_id")
			self.title = watchlist.value("title")

			self.info_box.append("")
			self.info_box.append("Upadating {}".format(self.title))
			
			self.update_show_info(self.IMDB_id)

			sleep(10) # Sleeping for 10 seconds as a protection agains IMDB's bot protection.

			### Getting values again, because season count might have changed.
			sql_get_show_info = QSqlQuery("SELECT * FROM shows WHERE IMDB_ID = '%s'" % self.IMDB_id) 
			sql_get_show_info.exec_()
			sql_get_show_info.first()

			self.seasons = sql_get_show_info.value("seasons")
			self.unknown_season = sql_get_show_info.value("unknown_season")
			self.selected_season = self.seasons
			###

			self.update_season() # Innitiating last season update
	
			if self.unknown_season == 1:
				# If there is an unknown season it is updated too.
				self.selected_season = "Unknown"
				self.update_season()

			self.progress_bar_current.setValue(9)
			self.info_box.append("========================")

			progress_count += 1
			self.progress_bar_overall.setValue(progress_count)
		
		self.button_ok.setEnabled(True)

		self.info_box.append("")
		self.info_box.append("Finished updating Watchlist.")

### Code taken from show_info_update.py UpdateShowInfo class
	def update_show_info(self, IMDB_id):
		
		something_updated_trigger = 0
		fetched_finished_airing = 2 # Default value for finished_airing. It will be changed later on if it is detected that show finished airing.
		
		self.info_box.append("Starting updating show %s info. Please be patient" % self.title)
			
		# Retrieving show values that will be checked from the database.
		sql_select_show = QSqlQuery("SELECT seasons, years_aired, running_time, finished_airing, unknown_season FROM shows WHERE IMDB_id = '%s'" % IMDB_id)
		
		sql_select_show.first()
		
		# Assingning show values that will be checked to variables
		current_seasons = sql_select_show.value("seasons")
		current_unknown_season = sql_select_show.value("unknown_season")
		current_years_aired = sql_select_show.value("years_aired")
		current_finished_airing = sql_select_show.value("finished_airing")
		current_running_time = sql_select_show.value("running_time")
		self.progress_bar_current.setValue(1)
		
		# Checking if there is at least one episode that belongs to Unknown season
		sql_check_unknown_season_episode = QSqlQuery("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % IMDB_id)
		sql_check_unknown_season_episode.first()
		unknown_season_episode_exists = sql_check_unknown_season_episode.value(0)
		self.progress_bar_current.setValue(2)		
		
		# Retrieving show values from IMDB
		fetched_show_info_detailed = self.imdb.get_title_episodes_detailed(IMDB_id, 1)
		
		fetched_season_list = fetched_show_info_detailed["allSeasons"]
		self.progress_bar_current.setValue(3)

		if None in fetched_season_list:
			fetched_seasons = len(fetched_season_list) - 1
			fetched_unknown_season = 1
		else:
			fetched_seasons = len(fetched_season_list)
			fetched_unknown_season = 0
		
		self.progress_bar_current.setValue(4)
		
		# Tries to get years when show started and finish airing.
		# If it can't get a second year it means, that show is still airing. It's not always the case, but it best I can do.
		# If finished_aird last year matches the start year it means that show aired just for one year.
		show_info_auxiliary = self.imdb.get_title_auxiliary(IMDB_id) # Retrieving show's info from IMDB
		show_start_year = show_info_auxiliary["seriesStartYear"]
		try:
			show_end_year = show_info_auxiliary["seriesEndYear"]
		except KeyError:
			show_end_year = ""
			fetched_finished_airing = 1	
		
		self.progress_bar_current.setValue(5)
		
		fetched_running_time = self.get_running_time(fetched_show_info_detailed, show_info_auxiliary)
		
		# Setting years airing that will be inserted into database.
		if show_start_year == show_end_year:
			fetched_years_aired = show_start_year		
		else:
			fetched_years_aired = str(show_start_year) + " - " + str(show_end_year)
		
		self.progress_bar_current.setValue(6)
		
		if current_finished_airing != fetched_finished_airing or current_years_aired != fetched_years_aired:
			# This if statement checks if years that show aired change on IMDB_id website by checking if it has one one or two years.
			# If show has one year it makrs show as it still airing, if it has two dates it will be marked as finished airing.
			# It also updates air dates in the database.
			sql_update_years_and_finished = QSqlQuery("UPDATE shows SET finished_airing = {finished_airing}, years_aired = '{years_aired}' WHERE IMDB_id = '{show_id}'".format(finished_airing = fetched_finished_airing, years_aired = fetched_years_aired, show_id = IMDB_id))
			sql_update_years_and_finished.exec_()
			self.info_box.append("Updated years aired from {old_years_aired} to {new_years_aired} and changed show's airing status".format(old_years_aired = current_years_aired, new_years_aired = fetched_years_aired))
			something_updated_trigger = 1
		
		if current_seasons != fetched_seasons:
			# This if statament checks season count and if it changed season count will be updated.
			sql_update_season = QSqlQuery("UPDATE shows SET seasons = {seasons} WHERE IMDB_ID = '{show_id}'".format(seasons = fetched_seasons, show_id = IMDB_id))
			sql_update_season.exec_()
			self.info_box.append("Updated season count from {old_season_count} to {new_season_count}. You should update show's seasons next".format(old_season_count = current_seasons, new_season_count = fetched_seasons))
			something_updated_trigger = 1
			
		if current_running_time != fetched_running_time:
			sql_update_running_time = QSqlQuery("UPDATE shows SET running_time = {running_time} WHERE IMDB_ID = '{show_id}'".format(running_time = fetched_running_time, show_id = IMDB_id))
			sql_update_running_time.exec_()
			self.info_box.append("Show's running time was changed from {old_running_time} to {new_running_time}".format(old_running_time = current_running_time, new_running_time = fetched_running_time))
			something_updated_trigger = 1
			
		#This if statement tries to check if there is and Unknown season in database and IMDB, but not ignore if there is and episodes with unknown season.
		if current_unknown_season != fetched_unknown_season and unknown_season_episode_exists == 1:
			self.info_box.append("It appears that all episodes in 'Unknown' season where removed or updated")
			self.info_box.append("You should update show's seasons")
			something_updated_trigger = 1
		elif current_unknown_season != fetched_unknown_season and unknown_season_episode_exists == 0:
			unknown_season_toggle = QSqlQuery("UPDATE shows SET unknown_season = 1 WHERE IMDB_id = '%s'" % self.IMDB_id)
			unknown_season_toggle.exec_()
			self.info_box.append("'Unknown season was added to show's season list.")
			self.info_box.append("You should update show's seasons")
			something_updated_trigger = 1
			
		
		self.progress_bar_current.setValue(7)

		self.info_box.append("")
		self.info_box.append("Finished updating %s info" % self.title)
		if something_updated_trigger == 0:
			self.info_box.append("Nothing was changed/updated")
		self.info_box.append("")

		self.progress_bar_current.setValue(8)

	def get_running_time(self, fetched_show_info_detailed, show_info_auxiliary):
		# Moved code that retrieves running time to this function, because there are a lot of nuance with it on IMDB side.
		first_episode_imdb_id = check_if_input_contains_IMDB_id(fetched_show_info_detailed['episodes'][1]['id']) # This is needed because IMDB shows different running time for tvMiniSeries (full run) and tvSeries (just for an episode).
			
		episode_run_time = self.imdb.get_title(first_episode_imdb_id)
		
		if show_info_auxiliary['titleType'] == 'tvSeries':
			# This if statement tries to get running_time for "normal" TV series.			
			if "runningTimeInMinutes" in episode_run_time['base'] and episode_run_time['base']["runningTimeInMinutes"] <= 60:
				return episode_run_time['base']["runningTimeInMinutes"]
			elif "runningTimeInMinutes" in show_info_auxiliary:
				return show_info_auxiliary["runningTimeInMinutes"]
			else:
				return 0
		
		else:
			# This if statement tries to get running_time for "mini" TV Series			
			if "runningTimeInMinutes" in episode_run_time['base']:
				# This if tries to retrieve running_time from one of the episodes of the show.
				return episode_run_time['base']["runningTimeInMinutes"]
			elif "runningTimeInMinutes" in show_info_auxiliary:
				# This one calculates episode runtime bu getting running time of all episode and dividing it by episode count
				full_run_time = show_info_auxiliary["runningTimeInMinutes"]
				episode_count = show_info_auxiliary["numberOfEpisodes"]
				return full_run_time / episode_count
			else:
				# If everything fails it running time will be set as 0
				return 0
###

### Taken from show_info_update.py UpdateSingleSeason class
	def update_season(self):	
		# This function needs self.title, self.selected_season, self.seasons, self.IMDB_id, self.unknown_season
		
		self.info_box.append("Updating {} Season {}".format(self.title, self.selected_season))
		
		# Because IMDB and my database uses different values for unknown season while retrieving it I have to assign two different values and use them accordingly.
		if self.selected_season == "Unknown":
			season_in_IMDB = int(self.seasons + self.unknown_season)
			season_in_database = ""
		else:
			season_in_IMDB = int(self.selected_season)
			season_in_database = int(self.selected_season)
		
		# Pattern for IMDB_id
		pattern_to_look_for = re.compile("tt\d+")
		# This labda should return just IMDB_id from given link
		get_IMDB_id_lambda = lambda x: pattern_to_look_for.search(x)[0]
		
		# Getting detailed episode JSON file from IMDB using IMDBpie
		detailed_season_episodes = self.imdb.get_title_episodes_detailed(self.IMDB_id, season_in_IMDB)
		
		# Setting counter to print a message to user how many files where updated.
		updated_episode_count = 0
		added_episode_count = 0
		
		# Looping though episode in JSON file, assinging variable name to data that will be updated or inserted in to database.
		for episode in detailed_season_episodes['episodes']:
			
			fetched_episode_IMDB_id = get_IMDB_id_lambda(episode['id'])

			# Selecting episode from the database using it's IMDB_id
			episode_from_database = QSqlQuery("SELECT * FROM %s WHERE episode_IMDB_id = '%s'" % (self.IMDB_id, fetched_episode_IMDB_id))

			# Asigning values fetched from IMDB to the variables.
			fetched_episode_number = episode["episodeNumber"]
			fetched_episode_year = episode["year"]
			fetched_episode_title = episode["title"]
			fetched_episode_air_date = episode["releaseDate"]["first"]["date"]
			
			if fetched_episode_number == None:
				fetched_episode_number = ""		
			if fetched_episode_year == None:
				fetched_episode_year = ""
			if fetched_episode_title == None:
				fetched_episode_title = ""
			if fetched_episode_air_date == None:
				fetched_episode_air_date = ""

			if fetched_episode_number != "" and season_in_database != "":
				if season_in_IMDB <= 9:
					new_episode_seasonal_id_season = "S0" + str(season_in_IMDB)
				else:
					new_episode_seasonal_id_season = "S" + str(season_in_IMDB)
				if fetched_episode_number <= 9:
					new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
				else:
					new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
					
				fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
			else:
				fetched_episode_seasonal_id = ""
			
			# Checking if episode anctually axists. If it does, variables names are assinged to it's information
			if episode_from_database.first() != False:
				
				current_episode_season = episode_from_database.value("season")
				current_episode_number = episode_from_database.value("episode")
				current_episode_year = episode_from_database.value("episode_year")
				current_episode_title = episode_from_database.value("episode_title")
				current_episode_air_date = episode_from_database.value("air_date")
				
				# THIS PART DEALS WITH EXISTING EPISODES FROM KNOWN SEASONS!
				# Checking if there is a difference between the fetched data from IMDB and database. If so data is formated and record is updated.
				if self.selected_season != "Unknown":
					if season_in_IMDB != season_in_database or current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:
						
						# This sting uses two types of substitution. One is Python3 and the other one is provided py Qt5. 						
						update_episode_string = "UPDATE {IMDB_id} SET season = :episode_season, episode = :episode_number, episode_seasonal_id = :episode_seasonal_id, episode_year = :episode_year, episode_title = :episode_title, air_date = :episode_air_date WHERE episode_IMDB_id = '{episode_IMDB_id}'".format(IMDB_id = self.IMDB_id, episode_IMDB_id = fetched_episode_IMDB_id)
						sql_update_episode = QSqlQuery()
						sql_update_episode.prepare(update_episode_string)
						sql_update_episode.bindValue(":episode_season", season_in_database) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode season will make sql_query to fail.
						sql_update_episode.bindValue(":episode_number", fetched_episode_number) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode numbers will make sql_query to fail.
						sql_update_episode.bindValue(":episode_seasonal_id", fetched_episode_seasonal_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_seasonal_id will make sql_query to fail.
						sql_update_episode.bindValue(":episode_year", fetched_episode_year) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode year will make sql_query to fail.
						sql_update_episode.bindValue(":episode_title", fetched_episode_title) # This substitutions is provided by Qt5 and is needed, becauase otherwise titles with quotes fill fail to be inserted into database.
						sql_update_episode.bindValue(":episode_air_date", fetched_episode_air_date) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty air_date will make sql_query to fail.
						sql_update_episode.exec_()
						
						# Setting updated episode counter +1 to print how many episodes where updated.
						updated_episode_count += 1
						self.info_box.append("Updated episode {episode_seasonal_id}:".format(episode_seasonal_id = fetched_episode_seasonal_id))
						if current_episode_title != fetched_episode_title:
							self.info_box.append("		Title: '{old_episode_title}' => '{new_episode_title}'".format(old_episode_title = current_episode_title, new_episode_title = fetched_episode_title))
						if current_episode_air_date != fetched_episode_air_date:
							self.info_box.append("		Air Date: '{old_air_date}' => '{new_air_date}'".format(old_air_date = current_episode_air_date, new_air_date = fetched_episode_air_date))
				
				# THIS PART DEALS WHITH EXISTING EPISODES FORM UNKNONW SEASON!
				# The only difference between this and episode check above is that this one does not check for difference in seaosns, while still trying to add one.
				else:
					
					if current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:
						
						# Updating episode information
						# This sting uses two types of substitution. One is Python3 and the other one is provided py Qt5.
						update_episode_string = "UPDATE {IMDB_id} SET season = :episode_season, episode = :episode_number, episode_seasonal_id = :episode_seasonal_id, episode_year = :episode_year, episode_title = :episode_title, air_date = :episode_air_date WHERE episode_IMDB_id = '{episode_IMDB_id}'".format(IMDB_id = self.IMDB_id, episode_IMDB_id = fetched_episode_IMDB_id)
						sql_update_episode = QSqlQuery()
						sql_update_episode.prepare(update_episode_string)
						sql_update_episode.bindValue(":episode_season", season_in_database) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode season will make sql_query to fail.
						sql_update_episode.bindValue(":episode_number", fetched_episode_number) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode numbers will make sql_query to fail.
						sql_update_episode.bindValue(":episode_seasonal_id", fetched_episode_seasonal_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_seasonal_id will make sql_query to fail.
						sql_update_episode.bindValue(":episode_year", fetched_episode_year) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode year will make sql_query to fail.
						sql_update_episode.bindValue(":episode_title", fetched_episode_title) # This substitutions is provided by Qt5 and is needed, becauase otherwise titles with quotes fill fail to be inserted into database.
						sql_update_episode.bindValue(":episode_air_date", fetched_episode_air_date) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty air_date will make sql_query to fail.
						sql_update_episode.exec_()
						
						# Setting updated episode counter +1 to print how many episodes where updated.
						updated_episode_count += 1
						self.info_box.append("Updated episode {episode_seasonal_id}:".format(episode_seasonal_id = fetched_episode_seasonal_id))
						if current_episode_title != fetched_episode_title:
							self.info_box.append("		Title: '{old_episode_title}' => '{new_episode_title}'".format(old_episode_title = current_episode_title, new_episode_title = fetched_episode_title))
						if current_episode_air_date != fetched_episode_air_date:
							self.info_box.append("		Air Date: '{old_air_date}' => '{new_air_date}'".format(old_air_date = current_episode_air_date, new_air_date = fetched_episode_air_date))

			# If episode does not exist in the database it is inserted in as a new record. The same steps are taken as in add new shows episodes in the add_show.py file.
			# This part should work the same for the Normal and Unknown seasons. 
			else:

				# This sting uses two types of substitution. One is Python3 and the other one is provided py Qt5.
				insert_episode_string = "INSERT INTO {IMDB_id} VALUES ({episode_watched}, :episode_season, :episode_number, :episode_IMDB_id, :episode_seasonal_id, :episode_year, :episode_title, :air_date)".format(IMDB_id = self.IMDB_id, episode_watched = 0)
				
				sql_insert_episode = QSqlQuery()
				sql_insert_episode.prepare(insert_episode_string)
				sql_insert_episode.bindValue(":episode_season", season_in_database) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode season will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_number", fetched_episode_number) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode numbers will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_IMDB_id", fetched_episode_IMDB_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_IMDB_id will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_seasonal_id", fetched_episode_seasonal_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_seasonal_id will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_year", fetched_episode_year) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode year will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_title", fetched_episode_title) # This substitutions is provided by Qt5 and is needed, becauase otherwise titles with quotes fill fail to be inserted into database.
				sql_insert_episode.bindValue(":air_date", fetched_episode_air_date) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty air_date will make sql_query to fail.					
				sql_insert_episode.exec_()
				
				added_episode_count += 1
				self.info_box.append("Added episode {} {}".format(fetched_episode_seasonal_id, fetched_episode_title))
		
		if self.unknown_season == 1:
			# This statement checks if there are any episodes in "Unknown" season and if they are all updated removes "Unknown" season from list.
			sql_check_unknown_season_episode = QSqlQuery("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % self.IMDB_id)
			sql_check_unknown_season_episode.first()
			unknown_season_episode_exists = sql_check_unknown_season_episode.value(0)
			if unknown_season_episode_exists == 0:
				unknown_season_toggle = QSqlQuery("UPDATE shows SET unknown_season = 0 WHERE IMDB_id = '%s'" % self.IMDB_id)
				unknown_season_toggle.exec_()
				
		self.info_box.append("")
		self.info_box.append("Finished updating season {} of {}".format(self.selected_season, self.title))
		self.info_box.append("Updated {} episodes".format(updated_episode_count))
		self.info_box.append("Added {} episodes".format(added_episode_count))
		self.info_box.append("")

###

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

		# Setting "Playback" layout
		box_playback = QGroupBox("Playback")
		box_playback.layout = QGridLayout()
		box_playback.layout.addWidget(playback_message, 0, 0, 1, 6)
		box_playback.layout.addWidget(self.playback_line_edit, 1, 0, 1, 5)
		box_playback.layout.addWidget(button_playback_choose, 1, 5, 1, 1)
		box_playback.setLayout(box_playback.layout)

		### Creating layout for "Misc" portion of the settings
		
		##	This creates a checkbox for user to choose if he/she want's to auto download covers.
		## 	Check box'es value is saved in settngs and default value is unchecked.
		self.cover_checkbox = QCheckBox("Auto-download Covers")
		if int(settings.value("downloadCovers")) == 0:
			self.cover_checkbox.setCheckState(Qt.Unchecked)
		else:
			self.cover_checkbox.setCheckState(Qt.Checked)
		self.cover_checkbox.stateChanged.connect(self.auto_download_covers)
		
		box_covers = QGroupBox("Misc")
		box_covers.layout = QHBoxLayout()
		box_covers.layout.addWidget(self.cover_checkbox)
		box_covers.setLayout(box_covers.layout)

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
		self.layout.addWidget(box_covers, 3, 0, 1, 6)
		self.layout.addWidget(self.button_cancel, 6, 0, 1, 1)
		self.layout.addWidget(self.button_apply, 6, 4, 1, 1)
		self.layout.addWidget(self.button_ok, 6, 5, 1, 1)
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
		if video_dir != "": # If user cancels window instead of choosing a catalog dialog window returns empty string. In that case nothing happens.
			# Set path to chosen directory to the line_edit and enabled apply button.
			self.playback_line_edit.setText(video_dir)
			self.button_apply.setEnabled(True)
	
	def auto_download_covers(self):
		## Checks if checkbox's status matches the one that is saved in settings.
		## If it doesn't "apply" button will be enabled
		
		if int(settings.value("downloadCovers")) != self.cover_checkbox.isChecked():
			# Compares current values of cover_checkbox and settings file's downloadCovers and sets "Apply" button status appropriately.
			self.button_apply.setEnabled(True)
		else:
			self.button_apply.setEnabled(False)

	def apply_changes(self):
		
		# Changes style and saves it to settings
		if settings.value("currentStyle") != self.combo_box_style.currentText():
			QApplication.setStyle(self.combo_box_style.currentText())
			settings.setValue("currentStyle", self.combo_box_style.currentText())
		
		# Saves chosen dir to settings
		if settings.value("videoDir") != self.playback_line_edit.text():	
			settings.setValue("videoDir", self.playback_line_edit.text())
		
		# Saves cover_checkbox value to settings
		if self.cover_checkbox.isChecked(): # Gets state of the cover_checkbox and assigns it a number 0 or 1 depending of that state for easier comparison.
			current_cover_checkbox_state = 1
		else:
			current_cover_checkbox_state = 0
		if settings.value("downloadCovers") != current_cover_checkbox_state:
			settings.setValue("downloadCovers", current_cover_checkbox_state)
		
		self.button_apply.setEnabled(False) # Disables "Apply" button.
		
	def clicked_ok(self):
		# Combines apply changes and closes window with accept signal.
		self.apply_changes()
		self.accept()