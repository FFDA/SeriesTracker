#! /usr/bin/python3

from imdbpie import Imdb

import sqlite3
import re
import urllib.request as urllib
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QLabel, QProgressBar, QTextEdit, QGridLayout
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtCore import Qt

class UpdateSingleSeason(QDialog):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(UpdateSingleSeason, self).__init__()
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.selected_season = ""
		self.window_title = "Choose %s season to update" % self.title
		self.imdb = Imdb()
		self.progress_minimum = 0
		self.progress_maximum = 1
		self.initUI()
		
	def initUI(self):
		self.setGeometry(400, 600, 800, 500)
		self.setModal(True)
		self.setWindowTitle(self.window_title)
		self.layout = QGridLayout()
		
		self.create_choose_season_combobox()
		
		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		
		self.create_progress_bar()
		
		self.message = QLabel("Choose a season")
		self.message.setAlignment(Qt.AlignCenter)
		
		self.create_confirmation_buttons()
		
		self.layout.addWidget(self.season_button_label, 0, 1, 1, 1)
		self.layout.addWidget(self.season_button, 0, 2, 1, 1)
		self.layout.addWidget(self.message, 1, 0, 1, 4)
		self.layout.addWidget(self.info_box, 2, 0, 4, 4)
		self.layout.addWidget(self.progress_bar, 7, 0, 1, 4)
		self.layout.addWidget(self.cancel, 8, 0, 1, 1)
		self.layout.addWidget(self.update_button, 8, 2, 1, 1)
		self.layout.addWidget(self.ok, 8, 3, 1, 1)
		self.setLayout(self.layout)
		self.show() 

	def create_confirmation_buttons(self):
				
		self.cancel = QPushButton("Cancel")
		self.ok = QPushButton("OK")
		self.ok.setDisabled(True) # Disables OK button. It will be enabled after update operation is finished.
		self.update_button = QPushButton("Update Season")
		self.update_button.setDisabled(True) # Disables Update Season button. It will be enabled after user set a season to update.
		
		self.cancel.clicked.connect(self.reject) #This button rejects the action and closes window withour changing anything in database.
		self.ok.clicked.connect(self.accept)
		self.update_button.clicked.connect(self.update_season)
		
	def create_choose_season_combobox(self):

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

		self.season_button = QComboBox()
		self.season_button.setMinimumSize(95, 31)
		self.season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		self.season_button.currentTextChanged.connect(self.setting_up_update) # Detects if user chooses different season and sends value to print_season function
		
		self.season_button_label = QLabel("Season")
		
	def setting_up_update(self, selected_season):
		
		if selected_season == "":
			self.message.setText("Please select a season")
			self.update_button.setDisabled(True) # Redisables "Update Season" button if user changes season selection to empty.
		else:
			self.message.setText("Season %s will be updated" % selected_season)
			self.update_button.setDisabled(False) # Enables "Update Season" button for user to innitaite season update.
		
		self.selected_season = selected_season

	def create_progress_bar(self):
		
		# Simply creates progress bar.
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(self.progress_minimum)
		self.progress_bar.setMaximum(self.progress_maximum)

	def change_season_button_index(self):
		# This function exists, because I will be able to change season_button index after finishing updating season.
		# Previously it was at the end of update_season function, but it made to error out UpdateThreeSeason class.
	
		self.season_button.setCurrentIndex(0) # This sets season combo_box to option that doesn't have any value and it should disable "Update Season" button.
	
	def update_season(self):
		
		# This function needs self.title, self.selected_season, self.seasons, self.IMDB_id
		
		self.ok.setDisabled(True) # Setting OK button to be disabled just in case.
		
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
		
		self.progress_bar.setMaximum(len(detailed_season_episodes['episodes'])) # Set maximum value to progress_bar		
		checked_episode_count = 0 # This count is used for progress bar to increase value. Increasing value makes progress_bar to "move"
		
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

			if fetched_episode_number != "" or season_in_database != "":
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
						self.info_box.append("Updated episode {} {}".format(fetched_episode_seasonal_id, fetched_episode_title))
				
				# THIS PART DEALS WHITH EXISTING EPISODES FORM UNKNONW SEASON!
				# The only difference between this and episode check above is that this one does not check for difference in seaosns, while still trying to add one.
				else:
					
					# Leaving these here for a moment, because I might need them for debugging
					# print(season_in_database)
					# print(season_in_IMDB)
					# print(current_episode_number)
					# print(fetched_episode_number)
					# print(current_episode_year)
					# print(fetched_episode_year)
					# print(current_episode_title)
					# print(fetched_episode_title)
					# print(current_episode_air_date)
					# print(fetched_episode_air_date)
					
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
						self.info_box.append("Updated episode {} {}".format(fetched_episode_seasonal_id, fetched_episode_title))

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
				sql_insert_episode.bindValue(":episode_air_date", fetched_episode_air_date) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty air_date will make sql_query to fail.					
				sql_insert_episode.exec_()
				
				added_episode_count += 1
				self.info_box.append("Added episode {} {}".format(fetched_episode_seasonal_id, fetched_episode_title))
				
			checked_episode_count += 1 # Adds +1 to progress bars count
			self.progress_bar.setValue(checked_episode_count) # Set's new value to progress bar. It should move it forward in percentage.
		
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
		
		self.cancel.setDisabled(True) # Disabling "Cancel" button because user has to quit using OK button to refresh tables
		self.ok.setDisabled(False) # Re enabling OK button
		self.change_season_button_index()
		

class UpdateThreeSeasons(UpdateSingleSeason):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(UpdateSingleSeason, self).__init__()
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.selected_season = ""
		self.window_title = "Update last three seasons of %s" % self.title
		self.imdb = Imdb()
		self.progress_minimum = 0
		self.progress_maximum = 1
		self.initUI()

	def initUI(self):
		self.setGeometry(400, 600, 800, 500)
		self.setModal(True)
		self.setWindowTitle(self.window_title)
		self.layout = QGridLayout()
		
		#self.create_choose_season_combobox()
		
		self.season_list = []

		# Appends all seasons in string from to season_list
		for i in range(self.seasons):
			self.season_list.append(str(i + 1))

		# Appends "Unknown" to the end of the list if there is an unknown season.
		if self.unknown_season == 1:
			self.season_list.append("Unknown")
		
		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		
		self.create_progress_bar()
		
		if len(self.season_list[-3:]) == 3:
			self.message = QLabel("Seasons {}, {} and {} will be updated".format(*self.season_list[-3:]))
		elif len(self.season_list[-3:]) == 2:
			self.message = QLabel("Seasons {} and {} will be updated".format(*self.season_list[-3:]))
		else:
			self.message = QLabel("Season {} will be updated".format(*self.season_list[-3:]))
		
		self.message.setAlignment(Qt.AlignCenter)
		
		self.create_confirmation_buttons()
		
		self.layout.addWidget(self.message, 0, 0, 1, 4)
		self.layout.addWidget(self.info_box, 1, 0, 4, 4)
		self.layout.addWidget(self.progress_bar, 6, 0, 1, 4)
		self.layout.addWidget(self.cancel, 7, 0, 1, 1)
		self.layout.addWidget(self.update_button, 7, 2, 1, 1)
		self.layout.addWidget(self.ok, 7, 3, 1, 1)
		self.setLayout(self.layout)
		self.show() 

	def create_confirmation_buttons(self):
				
		self.cancel = QPushButton("Cancel")
		self.ok = QPushButton("OK")
		self.ok.setDisabled(True) # Disables OK button. It will be enabled after update operation is finished.
		self.update_button = QPushButton("Update Seasons")
		
		self.cancel.clicked.connect(self.reject) #This button rejects the action and closes window withour changing anything in database.
		self.ok.clicked.connect(self.accept)
		self.update_button.clicked.connect(self.update_three_seasons)
		
	def update_three_seasons(self):
		
		for season in self.season_list[-3:]:
			self.progress_bar.setValue(0)
			self.selected_season = season
			self.update_season()
		
		self.cancel.setDisabled(True)
		self.update_button.setDisabled(True)
	
	def change_season_button_index(self):
		# This function is here to make function in UpdateSeason class with same name to do nothing.
		pass
			
class UpdateShowInfo(QDialog):
	
	def __init__(self, IMDB_id, title):
		super(UpdateShowInfo, self).__init__()
		self.IMDB_id = IMDB_id
		self.title = title
		self.imdb = Imdb()
		self.window_title = "Update %s info" % self.title
		
		self.initUI()
		
	def initUI(self):
		# All UI disign is in here.
		self.setGeometry(400, 600, 800, 500)
		self.setModal(True)
		self.setWindowTitle(self.window_title)
		self.layout = QGridLayout()
		
		self.message = QLabel("Show %s will be updated" % self.title)
		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(0)
		self.progress_bar.setMaximum(8)
		
		self.button_cancel = QPushButton("Cancel")
		self.button_update = QPushButton("Update show")
		self.button_update.clicked.connect(self.initiate_update) 
		self.button_ok = QPushButton("OK")
		self.button_ok.setDisabled(True)
		self.button_ok.clicked.connect(self.accept)
		
		self.layout.addWidget(self.message, 0, 0, 1, 4)
		self.layout.addWidget(self.info_box, 1, 0, 4, 4)
		self.layout.addWidget(self.progress_bar, 5, 0, 1, 4)
		self.layout.addWidget(self.button_cancel, 6, 0, 1, 1)
		self.layout.addWidget(self.button_update, 6, 2, 1, 1)
		self.layout.addWidget(self.button_ok, 6, 3, 1, 1)
		self.setLayout(self.layout)
		self.show() 
		
	def initiate_update(self):
		self.button_cancel.setDisabled(True)
		self.button_update.setDisabled(True)
		self.update_show_info(self.IMDB_id)
		self.button_ok.setDisabled(False)

	def update_show_info(self, IMDB_id):
		
		something_updated_trigger = 0
		
		self.info_box.append("Starting updating show %s info. Pease be patient" % self.title)
			
		# Retrieving show values that will be checked from the database.
		sql_select_show = QSqlQuery("SELECT seasons, years_aired, finished_airing, unknown_season FROM shows WHERE IMDB_id = '%s'" % IMDB_id)
		
		sql_select_show.first()
		
		# Assingning show values that will be checked to variables
		current_seasons = sql_select_show.value("seasons")
		current_unknown_season = sql_select_show.value("unknown_season")
		current_years_aired = sql_select_show.value("years_aired")
		current_finished_airing = sql_select_show.value("finished_airing")
		self.progress_bar.setValue(1)
		
		# Checking if there is at least one episode that belongs to Unknown season
		sql_check_unknown_season_episode = QSqlQuery("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % IMDB_id)
		sql_check_unknown_season_episode.first()
		unknown_season_episode_exists = sql_check_unknown_season_episode.value(0)
		self.progress_bar.setValue(2)		
		
		# Retrieving show values from IMDB
		fetched_show_info = self.imdb.get_title_episodes_detailed(IMDB_id, 1)
		
		fetched_season_list = fetched_show_info["allSeasons"]
		self.progress_bar.setValue(3)

		if None in fetched_season_list:
			fetched_seasons = len(fetched_season_list) - 1
			fetched_unknown_season = 1
		else:
			fetched_seasons = len(fetched_season_list)
			fetched_unknown_season = 0
		
		self.progress_bar.setValue(4)
			
		# Downloadning HTML page of the website.
		html_page = urllib.urlopen("https://www.imdb.com/title/" + IMDB_id +"/")
		# Parsing downloaded HTML file to get title of the page.
		soup_title = BeautifulSoup(html_page, 'html.parser').title.contents[0]
		# Parsing years aired of the show.
		years_aired = re.findall("(?<=\D)\d{4}(?=\D)", soup_title)
		
		self.progress_bar.setValue(5)
		
		self.info_box.append(current_years_aired)
		self.info_box.append(str(years_aired))

		fetched_finished_airing = len(years_aired)

		if len(years_aired) == 2:
			fetched_years_aired = years_aired[0] + " - " + years_aired[1]
		elif len(years_aired) == 1:
			fetched_years_aired = years_aired[0] + " - "
		
		self.progress_bar.setValue(6)
		
		if current_finished_airing != fetched_finished_airing or current_years_aired != fetched_years_aired:
			# This if statement checks if years that show aired change on IMDB_id website by checking if it has one one or two years.
			# If show has one year it makrs show as it still airing, if it has two dates it will be marked as finished airing.
			# It also updates air dates in the database.
			sql_update_years_and_finished = QSqlQuery("UPDATE shows SET finished_airing = {finished_airing}, years_aired = '{years_aired}' WHERE IMDB_id = '{show_id}'".format(finished_airing = fetched_finished_airing, years_aired = fetched_years_aired, show_id = IMDB_id))
			sql_update_years_and_finished.exec_()
			self.info_box.append("Updated years aired from {old_years_aired} to {new_years_aired} and change show's airing status".format(old_years_aired = current_years_aired, new_years_aired = fetched_years_aired))
			something_updated_trigger = 1
		
		if current_seasons != fetched_seasons:
			# This if statament checks season count and if it changed season count will be updated.
			sql_update_season = QSqlQuery("UPDATE shows SET seasons = {seasons} WHERE IMDB_ID = '{show_id}'".format(seasons = fetched_seasons, show_id = IMDB_id))
			sql_update_season.exec_()
			self.info_box.append("Updated season count from {old_season_count} to {new_season_count}. You should update show's seasons next".format(old_season_count = current_seasons, new_season_count = fetched_season_count))
			something_updated_trigger = 1
			
		#This if statement tries to check if there is and Unknown season in database and IMDB, but not ignore if there is and episodes with unknown season.
		if current_unknown_season != fetched_unknown_season and unknown_season_episode_exists == 1:
			self.info_box.append("It appears that all episodes in 'Unknown' season where removed or updated")
			self.info_box.append("You should update shows seasons")
			something_updated_trigger = 1
		elif current_unknown_season != fetched_unknown_season and unknown_season_episode_exists == 0:
			nknown_season_toggle = QSqlQuery("UPDATE shows SET unknown_season = 1 WHERE IMDB_id = '%s'" % self.IMDB_id)
			unknown_season_toggle.exec_()
			self.info_box.append("'Unknown season was added to show's season list.")
			self.info_box.append("You should update shows seasons")
			something_updated_trigger = 1
		
		self.progress_bar.setValue(7)

		self.info_box.append("")
		self.info_box.append("Finished updating %s info" % self.title)
		if something_updated_trigger == 0:
			self.info_box.append("Nothing was changed/updated")
		self.info_box.append("")

		self.progress_bar.setValue(8)
