#! /usr/bin/python3

from imdbpie import Imdb

import sqlite3
import re

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QComboBox, QLabel, QProgressBar
from PyQt5.QtSql import QSqlQuery

class UpdateSingleSeason(QDialog):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(UpdateSingleSeason, self).__init__()
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.selected_season = ""
		self.window_title = "Choose %s season to update" % self.title
		self.initUI()
		
	def initUI(self):
		self.setGeometry(400, 600, 800, 500)
		self.setModal(True)
		self.setWindowTitle(self.window_title)
		self.layout = QVBoxLayout()
		
		self.create_choose_season_combobox()
		
		self.message = QLabel("Choose a season")
		
		self.create_confirmation_buttons()
		
		self.layout.addWidget(self.choose_season_combobox)
		self.layout.addWidget(self.message)
		self.layout.addWidget(self.confirmation_button_box)
		self.setLayout(self.layout)
		self.show() 

	def create_confirmation_buttons(self):
		# Creates button that will be displayed at the bottom of the Window to confirm or cancel action.
		self.confirmation_button_box = QGroupBox()
		self.confirmation_button_box.layout = QHBoxLayout()
				
		cancel = QPushButton("Cancel")
		confirm = QPushButton("Update Season")
		
		cancel.clicked.connect(self.reject) #This button rejects the action and closes window withour changing anything in database.
		confirm.clicked.connect(self.update_selected_season)
		
		self.confirmation_button_box.layout.addWidget(cancel)
		self.confirmation_button_box.layout.addWidget(confirm)
		
		self.confirmation_button_box.setLayout(self.confirmation_button_box.layout)
		
	def create_choose_season_combobox(self):
	
		self.choose_season_combobox = QGroupBox()
		self.choose_season_combobox.layout = QHBoxLayout()

		# Season list that contains all season numbers in string form that will be used later on to populate drop down menu for user to choose a season from.
		# First value has "All" that prints all show's seasons.
		# If show has "Unknown" season list will have an option to choose it too.
		season_list = [""]

		# Appends all seasons in string from to season_list
		for i in range(self.seasons):
			season_list.append(str(i + 1))

		# Appends "Unknown" to the end of the list if there is an unknown season.
		if self.unknown_season == 1:
			season_list.append("Unknown")

		season_button = QComboBox()
		season_button.setMinimumSize(95, 31)
		season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		season_button.currentTextChanged.connect(self.setting_up_update) # Detects if user chooses different season and sends value to print_season function
		
		season_button_label = QLabel("Season")
		
		self.choose_season_combobox.layout.addWidget(season_button_label)
		self.choose_season_combobox.layout.addWidget(season_button)
				
		self.choose_season_combobox.setLayout(self.choose_season_combobox.layout)
		
	def setting_up_update(self, selected_season):
		
		if selected_season == "":
			self.message.setText("Please select a season")
		else:
			self.message.setText("Season %s will be updated" % selected_season)
			
		self.selected_season = selected_season
	
	def update_selected_season(self):
		
		if self.selected_season == "":
			self.message.setText("Select a season or choose cancel")
		else:
			self.open_update_season_window = UpdateSeason(self.IMDB_id, self.selected_season, self.title, self.seasons, self.unknown_season)
			self.open_update_season_window.exec_()
			self.accept()

class UpdateSeason(QDialog):

	def __init__(self, IMDB_id, selected_season, title, seasons, unknown_season):
		super(UpdateSeason, self).__init__()
		self.IMDB_id = IMDB_id
		self.selected_season = selected_season
		self.title = title
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.window_title = "Updating %s season %s" % (self.title, self.selected_season)
		self.imdb = Imdb()
		self.progress_minimum = 0
		self.progress_maximum = 1
		self.initUI()
		
	def initUI(self):
		
		self.setGeometry(400, 600, 800, 500)
		self.setModal(True)
		self.setWindowTitle(self.window_title)
		self.layout = QVBoxLayout()
		
		self.message = QLabel("Updating seasons")
		
		self.ok = QPushButton("OK")
		self.ok.setDisabled(True)
		
		self.create_progress_bar()

		self.ok.clicked.connect(self.accept)
		
		self.layout.addWidget(self.progress_bar)
		self.layout.addWidget(self.message)
		self.layout.addWidget(self.ok)
		self.setLayout(self.layout)
		self.show()
		
		self.update_season()

	def create_progress_bar(self):
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(self.progress_minimum)
		self.progress_bar.setMaximum(self.progress_maximum)

	def update_season(self):
		
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
		detailed_season_episodes = self.imdb.get_title_episodes_detailed(self.IMDB_id, int(season_in_IMDB))
		
		self.progress_bar.setMaximum(len(detailed_season_episodes['episodes']))
		
		checked_episode_count = 0 # This count is used for progress bar
		
		# Setting counter to print a message to user how many files where updated.
		updated_episode_count = 0
		added_episode_count = 0
		
		# Looping though episode in JSON file, assinging variable name to data that will be updated or inserted in to database.
		for episode in detailed_season_episodes['episodes']:
			
			fetched_episode_IMDB_id = get_IMDB_id_lambda(episode['id'])

			# Selecting episode from the database using it's IMDB_id
			episode_from_database = QSqlQuery("SELECT * FROM %s WHERE episode_IMDB_id = '%s'" % (self.IMDB_id, fetched_episode_IMDB_id))  
			#fetch_episode_from_database = episode_from_database.first()
			
			# Checking if episode anctually axists. If it does, variables names are assing to it's information
			if episode_from_database.first() != False:

				current_episode_season = episode_from_database.value("season")
				current_episode_number = episode_from_database.value("episode")
				current_episode_year = episode_from_database.value("episode_year")
				current_episode_title = episode_from_database.value("episode_title")
				current_episode_air_date = episode_from_database.value("air_date")

				fetched_episode_number = episode["episodeNumber"]
				fetched_episode_year = episode["year"]
				fetched_episode_title = episode["title"]
				fetched_episode_air_date = episode["releaseDate"]["first"]["date"]

				# Checking if there is a difference between the fetched data from IMDB and database. If so data is formated and record is updated.
				if self.selected_season != "Unknown":
				
					if season_in_IMDB != season_in_database or current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:
					
						if season_in_IMDB <= 9:
							new_episode_seasonal_id_season = "S0" + str(season_in_IMDB)
						else:
							new_episode_seasonal_id_season = "S" + str(season_in_IMDB)
						if fetched_episode_number <= 9:
							new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
						else:
							new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
						
						fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
						
						# Updating episodes information
						update_episode_string = "UPDATE {IMDB_id} SET episode = {episode_number}, episode_seasonal_id = {episode_seasonal_id}, episode_year = {episode_year}, episode_title = {episode_title}, air_date = {episode_air_date} WHERE episode_IMDB_id = {episode_IMDB_id}".format(IMDB_id = self.IMDB_id, episode_number = fetched_episode_number, episode_seasonal_id = fetched_episode_seasonal_id, episode_year = fetched_episode_year, episode_title = fetched_episode_title, episode_air_date = fetched_episode_air_date, episode_IMDB_id = fetched_episode_IMDB_id)
						sql_update_episode = QSqlQuery(update_episode_string)
						sql_update_episode.exec_()
						# Setting updated episode counter +1 to print how many episodes where updated.
						updated_episode_count += 1
				
				else:
					
					if fetched_episode_number != None:
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
						fetched_episode_number = ""
						fetched_episode_seasonal_id = ""
						
					if fetched_episode_year == None:
						fetched_episode_year = ""
					if fetched_episode_title == None:
						fetched_episode_title = ""
					if fetched_episode_air_date == None:
						fetched_episode_air_date = ""						
					
					if current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:
						# Updating episodes information
						update_episode_string = "UPDATE {IMDB_id} SET episode = {episode_number}, episode_seasonal_id = {episode_seasonal_id}, episode_year = {episode_year}, episode_title = {episode_title}, air_date = {episode_air_date} WHERE episode_IMDB_id = {episode_IMDB_id}".format(IMDB_id = self.IMDB_id, episode_number = fetched_episode_number, episode_seasonal_id = fetched_episode_seasonal_id, episode_year = fetched_episode_year, episode_title = fetched_episode_title, episode_air_date = fetched_episode_air_date, episode_IMDB_id = fetched_episode_IMDB_id)
						sql_update_episode = QSqlQuery(update_episode_string)
						sql_update_episode.exec_()
						# Setting updated episode counter +1 to print how many episodes where updated.
						updated_episode_count += 1

			# If episode does not exist in the database it is inserted in as a new record. The same steps are taken as in add new shows episodes in the add_show.py file.   
			else:
	
				if current_season <= 9:
					new_episode_seasonal_id_season = "S0" + str(current_season)
				else:
					new_episode_seasonal_id_season = "S" + str(current_season)
				if fetched_episode_number <= 9:
					new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
				else:
					new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
				
				fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
	
				episode_insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % self.IMDB_id
				sql_episode_insert = QSqlQuery(episode_insert_string, (0, int(season_in_database), fetched_episode_number, fetched_episode_IMDB_id, fetched_episode_seasonal_id, fetched_episode_year, fetched_episode_title, fetched_episode_air_date))
				sql_episode_insert.exec_()

				# Adding to the added episode count
				added_episode_count += 1
			
			checked_episode_count += 1 # Adds +1 to progress bars count
			self.progress_bar.setValue(checked_episode_count) # Set's new value to progress bar. It should move it forward in percentage.
			
			if self.progress_bar.value() >= self.progress_maximum:
				self.ok.setDisabled(False)

		if updated_episode_count != 0 and added_episode_count != 0:
			self.message.setText("Updated %d episodes and added %d episodes" % (updated_episode_count, added_episode_count))
		else:
			self.message.setText("There were nothing to update or to add")
