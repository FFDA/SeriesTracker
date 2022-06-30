#! /usr/bin/python3

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QComboBox, QTextEdit, QProgressBar, QPushButton, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtSql import QSqlQuery

from imdbpie import Imdb
from urllib import request # Needed to download covers
import re
from misc import center, check_if_input_contains_IMDB_id, has_internet_connection

settings = QSettings("SeriesTracker", "SeriesTracker")
 
class AddShow(QDialog):
	 
	def __init__(self):
		super(AddShow, self).__init__()
		self.imdb = Imdb()
		self.initUI()
		
	def initUI(self):
		self.resize(800, 500)
		center(self)
		self.setModal(True)
		self.setWindowTitle("Add Show")
		self.layout = QGridLayout()
		
		self.message = QLabel("Paste show's IMDB id or full url from IMDB.com and click Add Show")
		self.message.setAlignment(Qt.AlignCenter)
		
		self.IMDB_id_input = QLineEdit()
		self.IMDB_id_input.setClearButtonEnabled(True)
		self.IMDB_id_input.setPlaceholderText("Paste IMDB here")
		self.IMDB_id_input.textChanged.connect(self.IMDB_id_input_management)
		
		self.combo_box_label = QLabel("Add to:")
		# self.combo_box_label.setAlignment(Qt.AlignRight)
		self.combo_box_list = ["Watchlist", "Finished Watching", "Plan to Watch"]
		self.combo_box = QComboBox()
		self.combo_box.addItems(self.combo_box_list)
		self.combo_box.setCurrentIndex(2) # Setting combo box index to make "Plan to Watch" as default option.

		# This checkbox initiates with status from settings. It can be changed for this current windown, but it will not be saved to the settings file and value will be restored from settings file next time window will be opened. To change this value user has to go to tools > settings.
		self.download_cover_checkbox = QCheckBox("Download Cover")
		if int(settings.value("downloadCovers")):
			self.download_cover_checkbox.setCheckState(Qt.Checked)
		else:
			self.download_cover_checkbox.setCheckState(Qt.Unchecked)

		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(0)
		self.progress_bar.setMaximum(1)
		
		self.button_cancel = QPushButton("Cancel")
		self.button_cancel.clicked.connect(self.reject)
		self.button_add_show = QPushButton("Add Show")
		self.button_add_show.clicked.connect(self.initiate_add_show)
		self.button_add_show.setDisabled(True)
		self.button_ok = QPushButton("OK")
		self.button_ok.clicked.connect(self.accept)
		self.button_ok.setDisabled(True)
		
		self.layout.addWidget(self.message, 0, 0, 1, 4)
		self.layout.addWidget(self.IMDB_id_input, 1, 0, 1, 4)
		self.layout.addWidget(self.combo_box_label, 2, 0, 1, 1)
		self.layout.addWidget(self.combo_box, 2, 1, 1, 1)
		self.layout.addWidget(self.download_cover_checkbox, 2, 3, 1, 1)
		self.layout.addWidget(self.info_box, 3, 0, 4, 4)
		self.layout.addWidget(self.progress_bar, 8, 0, 1, 4)
		self.layout.addWidget(self.button_cancel, 9, 0, 1, 1)
		self.layout.addWidget(self.button_add_show, 9, 2, 1, 1)
		self.layout.addWidget(self.button_ok, 9, 3, 1, 1)
		
		self.setLayout(self.layout)
		self.show()
		
	def IMDB_id_input_management(self, text):
		# This function enables / disables "Add Show" button depending if there is any text in the IMDB_id_input field
		
		if text != "":
			self.button_add_show.setDisabled(False)
		else:
			self.button_add_show.setDisabled(True)
			
	def initiate_add_show(self):
		
		self.combo_box.setDisabled(True)
		self.button_cancel.setDisabled(True)
		
		# Validates if user added text contains IMDB_id.
		# If it does it checks if that show is already in the database. If it is not proceed to add the show.
		# If user adds text without IMDB_id it prints text in the info_box.
		# Likewise if user tries to add show that already exists in the database message will be added to info_box to tell that.
		
		self.IMDB_id_input.setReadOnly(True) # Sets IMDB_id_input field to readOnly that user could add extra text. Just in case.
		
		user_input = self.IMDB_id_input.text()
		checked_user_input = check_if_input_contains_IMDB_id(user_input) # Checks if input contains IMDB_id
		
		if checked_user_input != False: # User input has IMDB_id in it
			
			self.info_box.append("Adding show with IMDB_id: " + checked_user_input)
			sql_check_if_exists = QSqlQuery("SELECT EXISTS (SELECT * FROM shows WHERE IMDB_id = '%s')" % checked_user_input) # SqlQuery to check if show is in database.
			sql_check_if_exists.first()
			if sql_check_if_exists.value(0) == 0: # Starts adding the show
				self.info_box.append("Starting to add the show")
				self.add_show(checked_user_input)
			else:
				self.info_box.setTextColor(Qt.red)
				self.info_box.append("Show already exists in database") # Prints a message that show is already in database
				self.info_box.setTextColor(Qt.black)
				self.button_ok.setDisabled(False)
		else:
			self.info_box.setTextColor(Qt.red)
			self.info_box.append("Couldn't find IMDB_id")
			self.info_box.setTextColor(Qt.black)
		
		self.IMDB_id_input.clear()
		self.IMDB_id_input.setReadOnly(False)
		self.combo_box.setDisabled(False)
		
	def add_show(self, IMDB_id):
		# This functiong creates show entry into shows table and adds the show.
		
		progress_bar_value = 0
		
		finished_airing = 2 # Default value for finsihed airing. It will be changed latter if it is detected that show finsihed airing.
		unknown_season = 0 # Default value for unknown season. It will be changed to 1 later if show has one.
		
		show_info = self.imdb.get_title_auxiliary(IMDB_id) # Retrieving show's info from IMDB
		
		# Checks if user tries to add movie instead if the show. And cancels proccess if he/she is.
		if show_info["titleType"] == "movie":
			self.info_box.setTextColor(Qt.red)
			self.info_box.append("You provided IMDB ID of a movie.")
			self.info_box.append("It will not be added to database.")
			self.info_box.setTextColor(Qt.black)
			return
		
		title = show_info["title"]
		
		# Tries to get url for an image that will be downloaded later as a Series cover
		try:
			image = show_info["image"]["url"]
		except KeyError:
			image = ""
		
		# Tries to get summary of the show. Only one show right now does not have a summary: tt1288814
		try:
			synopsis = show_info['plot']['outline']['text']
		except KeyError:
			synopsis = show_info['plot']['summaries'][0]['text']
		except TypeError:
			synopsis = "There is no summary available at this time"		
		
		season_list = [] # This will be used later on to add every season in to database
		
		# Goes throught every season and adds it as separate item in the list.
		# Replaces None season with "Unknown" and toggles unknown_season marker to 1 if there is one.
		for season in range(len(show_info['seasonsInfo'])):
			if show_info['seasonsInfo'][season]['season'] == None:
				season_list.append("Unknown")
				unknown_season = 1
			else:
				season_list.append(show_info['seasonsInfo'][season]['season'])
		
		self.progress_bar.setMaximum(len(season_list) + 6) # Setting true maximum value of progress_bar.
		progress_bar_value += 2
		self.progress_bar.setValue(progress_bar_value)
		
		# Assingns seasons number depending on if there is "Unknown" season or not.
		if unknown_season == 0:
			seasons = len(season_list)
		else:
			seasons = len(season_list) - 1
		
		# Genres of the show
		genres = " ".join(show_info["genres"])
		
		# Tries to get years when show started and finish airing.
		# If it can't get a second year it means, that show is still airing. It's not always the case, but it best I can do.
		# If finished_aird last year matches the start year it means that show aired just for one year.
		try:
			show_start_year = show_info["seriesStartYear"]
		except KeyError:
			show_start_year = ""
		
		try:
			show_end_year = show_info["seriesEndYear"]
		except KeyError:
			show_end_year = ""
			finished_airing = 1	
		
		fetched_show_info_detailed = self.imdb.get_title_episodes_detailed(IMDB_id, 1)
		running_time = self.get_running_time(fetched_show_info_detailed, show_info)
		
		# Setting years airing that will be inserted into database.
		if show_start_year == show_end_year:
			years_aired = show_start_year		
		else:
			years_aired = str(show_start_year) + " - " + str(show_end_year)
		
		# finished_watching is user chosen list that he/she whanted show to be added to.
		finished_watching = self.combo_box.currentIndex()
		
		progress_bar_value += 1
		self.progress_bar.setValue(progress_bar_value)
		
		status_finished_airing = lambda status : "Airing" if status == 1 else "Finished Airing"
		status_finished_watching = lambda status : "Watching" if status == 0 else ("Finished Watching" if status == 1 else "Plan to Watch")
		status_unknown_season = lambda status : "Yes" if status == 1 else "No"
		
		# Printig collected data for user.
		self.info_box.append("")
		self.info_box.append("IMDB id: " + IMDB_id)
		self.info_box.append("Title: " + title)
		self.info_box.append("Image: " + image)
		self.info_box.append("Synopsis: " + synopsis)
		self.info_box.append("Seasons: " + str(seasons))
		self.info_box.append("Genres: " + str(genres))
		self.info_box.append("Running time: " + str(running_time))
		self.info_box.append("Finished airing: " + status_finished_airing(finished_airing))
		self.info_box.append("Years aired: " + str(years_aired))
		self.info_box.append("List: " + status_finished_watching(finished_watching))
		self.info_box.append("Unknown season: " + status_unknown_season(unknown_season))
		
		# Preparing SQL query to insert show into shows table
		sql_insert_new_show_str = "INSERT INTO shows VALUES (:IMDB_id, :title, :image, :synopsis, :seasons, :genres, :running_time, :finished_airing, :years_aired, :finished_watching, :unknown_season)"
		
		sql_insert_new_show = QSqlQuery()
		sql_insert_new_show.prepare(sql_insert_new_show_str)
	
		progress_bar_value += 1
		self.progress_bar.setValue(progress_bar_value)
		
		# Bindig values
		sql_insert_new_show.bindValue(":IMDB_id", IMDB_id)
		sql_insert_new_show.bindValue(":title", title)
		sql_insert_new_show.bindValue(":image", image)
		sql_insert_new_show.bindValue(":synopsis", synopsis)
		sql_insert_new_show.bindValue(":seasons", seasons)
		sql_insert_new_show.bindValue(":genres", genres)
		sql_insert_new_show.bindValue(":running_time", running_time)
		sql_insert_new_show.bindValue(":finished_airing", finished_airing)
		sql_insert_new_show.bindValue(":years_aired", years_aired)
		sql_insert_new_show.bindValue(":finished_watching", finished_watching)
		sql_insert_new_show.bindValue(":unknown_season", unknown_season)
	
		#Inserting new row into shows table.
		sql_insert_new_show.exec_()
		
		progress_bar_value += 1
		self.progress_bar.setValue(progress_bar_value)
		
		# Creating SQL query to add show's episode table
		sql_create_show_episode_table = QSqlQuery("CREATE TABLE IF NOT EXISTS %s (episode_watched INTEGER, season INTEGGER, episode INTEGER, episode_IMDB_id TEXT NOT NULL PRIMARY KEY, episode_seasonal_id TEXT, episode_year INTEGER, episode_title TEXT NOT NULL, air_date TEXT)" % IMDB_id)
		sql_create_show_episode_table.exec_()
		
		# This value will be used to mark episodes as watched if user select to add show as finisehd watching.
		if finished_watching == 1:
			mark_episode = 1
		else:
			mark_episode = 0
		
		added_episode_count = 0
		
		progress_bar_value += 1
		self.progress_bar.setValue(progress_bar_value)
		
		# This part will go thought all avialable seasons and add them one by one.
		for season in season_list:
			
			self.info_box.append("Now adding season: {}".format(season))
			
			# If it has to add an unknown season function has to have it's number.
			# That is all normal seasons + 1
			if season == "Unknown":
				season_in_IMDB = int(seasons + unknown_season)
				season_in_database = ""
			else:
				season_in_IMDB = season
				season_in_database = season
				
			# Pattern for IMDB_id
			pattern_to_look_for = re.compile("tt\d+")
			# This labda should return just IMDB_id from given link
			get_IMDB_id_lambda = lambda x: pattern_to_look_for.search(x)[0]
			
			# Getting detailed episode JSON file from IMDB using IMDBpie
			detailed_season_episodes = self.imdb.get_title_episodes_detailed(IMDB_id, season_in_IMDB)

			# Looping though episode in JSON file, assinging variable name to data that will be updated or inserted in to database.
			for episode in detailed_season_episodes['episodes']:
				
				fetched_episode_IMDB_id = get_IMDB_id_lambda(episode['id'])

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
					if season <= 9:
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
					
				
				# This sting uses two types of substitution. One is Python3 and the other one is provided py Qt5.
				insert_episode_string = "INSERT INTO {IMDB_id} VALUES (:episode_watched, :episode_season, :episode_number, :episode_IMDB_id, :episode_seasonal_id, :episode_year, :episode_title, :air_date)".format(IMDB_id = IMDB_id)
				
				sql_insert_episode = QSqlQuery()
				sql_insert_episode.prepare(insert_episode_string)
				sql_insert_episode.bindValue(":episode_watched", mark_episode)
				sql_insert_episode.bindValue(":episode_season", season_in_database) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode season will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_number", fetched_episode_number) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode numbers will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_IMDB_id", fetched_episode_IMDB_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_IMDB_id will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_seasonal_id", fetched_episode_seasonal_id) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode_seasonal_id will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_year", fetched_episode_year) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty episode year will make sql_query to fail.
				sql_insert_episode.bindValue(":episode_title", fetched_episode_title) # This substitutions is provided by Qt5 and is needed, becauase otherwise titles with quotes fill fail to be inserted into database.
				sql_insert_episode.bindValue(":air_date", fetched_episode_air_date) # This substitutions is provided by Qt5 and is needed, becauase otherwise empty air_date will make sql_query to fail.					
				sql_insert_episode.exec_()
				
				added_episode_count += 1						
			progress_bar_value += 1
			self.progress_bar.setValue(progress_bar_value)
		
		## This if statement checks if user wants to download cover for the show. If so it tells user that it is downloading the cover and initiantes download_cover function. Otherwise nothing message is printed that tell that user will have to do it manually from show_info window.
		if self.download_cover_checkbox.isChecked():
			self.info_box.append("Downloading show's cover image.")
			self.download_cover(IMDB_id, image)
		else:
			self.info_box.append("Skipped download of the show's cover image. That will still be possible to do from Shows Info window.")
		
		self.info_box.append("Finished adding show.")
		self.info_box.append("Total episodes: {}".format(added_episode_count))
		
		self.button_ok.setDisabled(False)

	def get_running_time(self, fetched_show_info_detailed, show_info_auxiliary):
		# Moved code that retrieves running time to this function, because there are a lot of nuance with it on IMDB side.
		
		# When show is in early stages of development it might be missing some info. And that might crash the program
		try:
			first_episode_imdb_id = check_if_input_contains_IMDB_id(fetched_show_info_detailed['episodes'][1]['id']) # This is needed because IMDB shows different running time for tvMiniSeries (full run) and tvSeries (just for an episode).
		except IndexError:
			return 0
			
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

	def download_cover(self, IMDB_id, image):
		## Checks if there is an internet connection. Returns false if not.
		## Then tries to download show cover with image(url) passed to the program.
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return False
		elif len(image) == 0:
			self.info_box.append("Could not find an image url")
			return False
		else:
			path_to_cover = settings.value("coverDir") + IMDB_id + ".jpg"
			
			with open(path_to_cover, "bw") as f:
				f.write(request.urlopen(image).read())

			f.close()
			return True
			