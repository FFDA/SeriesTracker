#! /usr/bin/python3

#This file is resposible for creating Show Info window and all buttons for it.

# Python3 imports
import webbrowser
from urllib import request
from os import listdir
import re

# PyQt5 imports
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QVBoxLayout, QTabWidget, QLabel, QPushButton, QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView, QGroupBox, QHBoxLayout, QLineEdit, QGridLayout, QComboBox, QMenu, QSizePolicy
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QFont, QPixmap, QDesktopServices
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings, pyqtSignal, QObject, QSize, QUrl

from series_tracker import CreateShowEpisodeTable
from show_info_mark import *
from show_info_update import *
from show_info_manage import *
from misc import *

settings = QSettings("SeriesTracker", "SeriesTracker")

class OpenShowWindow(QWidget):
	
	def __init__(self, IMDB_id):
		super(OpenShowWindow, self).__init__()
		self.IMDB_id = IMDB_id

	def initUI(self):
		# Initiating Show Window
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.fetch_show_info() # Getting all info ready
		self.resize(int(settings.value("width")), int(settings.value("height")))
		center(self)
		self.setMinimumSize(int(settings.value("width")), int(settings.value("height")))
		self.setWindowTitle(self.title)
		self.setWindowModality(Qt.ApplicationModal)

		self.layout = QGridLayout()
		
		self.cover_box = QGroupBox() # Cover box layout
		self.cover_box.layout = QGridLayout()  # Cover box layout
		
		self.make_show_info_box()

		# Checks if there is a folder with the same name as show title in set directory
		episode_list = dict() # Default value is empty dictionary to mark that there isn't such folder.
		for title in listdir(settings.value("videoDir")):
			if "".join(character for character in self.title.lower() if character.isalnum()) == "".join(character for character in title.lower()[:len(self.title)] if character.isalnum()): # This part detects the folder that starts with the same words as show's title. It removes all not number or letter characters from the both titles and compares the same lenth strings.
				episode_list["path"] = settings.value("videoDir") + QDir.separator() + title + QDir.separator() # Adds full path to the folder with all episodes the dictionary.
				# If folder is found. Every seasonal_episode_id that is found is added to dictionary.
				for file_name in listdir(settings.value("videoDir") + QDir.separator() + title):
					episode_seasonal_id = get_seasonal_id(file_name) # This function is in misc.py
					if episode_seasonal_id!= None:
						episode_list[episode_seasonal_id.upper()] = file_name # Adds dictionary pair of episode_seasonal_id as a key and full file name as a value from scanned folder.

		self.episodes_table = CreateShowInfoEpisodeTable(self.IMDB_id, episode_list) # Initiating episode table
		
		self.episodes_table.sql_select_shows = "SELECT * FROM %s ORDER BY episode_seasonal_id ASC" % self.IMDB_id
		self.episodes_table.create_table()	
		
		self.create_buttons()
		
		self.button_ok = QPushButton("OK")
		self.button_ok.clicked.connect(self.close)

		self.layout.addWidget(self.cover_box, 0, 0, 8, 3)
		self.layout.addWidget(self.show_info_box, 0, 3, 8, 9)
		self.layout.addWidget(self.button_box, 9, 0, 1, 12)
		self.layout.addWidget(self.episodes_table.episode_table, 10, 0, 8, 12)
		self.layout.addWidget(self.button_ok, 18, 11, 1, 1)
		self.setLayout(self.layout)
		
		self.show()
		
		self.episodes_table.episode_table.scrollToBottom() # Scrolls table to the bottom
		self.episodes_table.episode_marked.connect(self.refill_show_info_box)
	
	def fetch_show_info(self):
		# Fetching data about show and seving them as variables to send to other functions/classes later.
		show_info = QSqlQuery("SELECT * FROM shows WHERE IMDB_id = '%s'" % self.IMDB_id)
		show_info.first()
		self.title = show_info.value("title")
		self.image = show_info.value("image")
		self.synopsis = show_info.value("synopsis")
		self.seasons = show_info.value("seasons")
		self.genres = show_info.value("genres")
		self.running_time = show_info.value("running_time")
		self.years_aired = show_info.value("years_aired")
		self.finished_watching = show_info.value("finished_watching")
		self.unknown_season = show_info.value("unknown_season")	
 
	def make_show_info_box(self):
		
		# Creating group box where Show Info and Poster will be placed.
		self.show_info_box = QGroupBox()
		self.show_info_box.layout = QGridLayout()

		info_box = QGroupBox() # Group box containing Show's info
		info_box.layout = QGridLayout()
		info_box.setMinimumSize(700, 300)
		 
		font_title = QFont() # Font size for title
		font_title.setPointSize(20)

		font_other = QFont() # Font size for other objects
		font_other.setPointSize(14)

		font_synopsis = QFont() # Font size for synopsis
		font_synopsis.setPointSize(12)
		
		self.label_title = QLabel()
		self.label_title.setFont(font_title)
		self.label_title.setAlignment(Qt.AlignHCenter)
		
		self.label_years_aired = QLabel()
		self.label_years_aired.setFont(font_other)

		self.label_genres = QLabel()
		self.label_genres.setFont(font_other)

		self.label_running_time = QLabel()
		self.label_running_time.setFont(font_other)

		self.label_seasons = QLabel()
		self.label_seasons.setFont(font_other)

		self.label_watched_time = QLabel()
		self.label_watched_time.setFont(font_other)

		self.label_in_list = QLabel()
		self.label_in_list.setFont(font_other)

		self.label_synopsis = QLabel()
		self.label_synopsis.setWordWrap(True)
		self.label_synopsis.setFont(font_synopsis)
		
		info_box.layout.addWidget(self.label_title)
		info_box.layout.addWidget(self.label_years_aired)
		info_box.layout.addWidget(self.label_genres)
		info_box.layout.addWidget(self.label_running_time)
		info_box.layout.addWidget(self.label_seasons)
		info_box.layout.addWidget(self.label_watched_time)
		info_box.layout.addWidget(self.label_in_list)
		info_box.layout.addWidget(self.label_synopsis)

		info_box.setLayout(info_box.layout)

		self.show_info_box.layout.addWidget(info_box)
		self.show_info_box.setLayout(self.show_info_box.layout)
		
		self.fill_show_info_box()
		self.create_cover_box()
		
	def fill_show_info_box(self):
		self.label_title.setText(self.title)
		self.label_years_aired.setText("Years aired: " + self.years_aired)
		self.label_genres.setText("Genres: " + self.genres)
		self.label_running_time.setText("Episode runtime: " + str(self.running_time) + " minutes")
		self.label_seasons.setText(str(self.seasons) + " season(s)")
		
		# This function retrieves number of episodes that are marked as watched.
		watched_episode_count = QSqlQuery("SELECT COUNT(*) FROM %s WHERE episode_watched =1" % self.IMDB_id)
		watched_episode_count.first()
		
		self.label_watched_time.setText("You watched this show for %d minutes (%s hours/%s days)" % (watched_episode_count.value(0) * self.running_time, str(round(watched_episode_count.value(0) * self.running_time/60, 1)), str(round(watched_episode_count.value(0) * self.running_time/1440, 1))))
		
		# Set's text for label that prints name of the list show is in
		if self.finished_watching == 0:
			current_list = "Currently in Watchlist"
		elif self.finished_watching == 1:
			current_list = "Currently in Finished Watching list"
		elif self.finished_watching == 2:
			current_list = "Currently in Plan to Watch list"
	
		self.label_in_list.setText(current_list)
		
		self.label_synopsis.setText(self.synopsis)
		
	def create_cover_box(self):
		# Creates cover box. And add poster if there is one downloaded. If not shows a button to download a poster.
				
		if self.image == "":
			self.cover_box.cover = QLabel("There is no cover to downlaod") # Poster placeholder
			self.cover_box.cover.setAlignment(Qt.AlignCenter)
			self.cover_box.layout.addWidget(self.cover_box.cover)
		elif QPixmap().load(settings.value("coverDir") + self.IMDB_id + ".jpg") == True:
			# If there is a cover in .local/share/SeriesTracker/covers folder it is loaded.
			self.cover_box.cover = QLabel() # Poster placeholder
			self.cover_box.cover.setAlignment(Qt.AlignCenter)
			image = QPixmap(settings.value("coverDir") + self.IMDB_id + ".jpg")
			self.cover_box.cover.setPixmap(image.scaled(QSize(200, 300), Qt.KeepAspectRatio, Qt.SmoothTransformation))
			self.cover_box.layout.addWidget(self.cover_box.cover)
		else:
			# If cover hasn't been downloaded yet button to download one is displayed.
			self.cover_box.button = QPushButton("Download Cover")
			self.cover_box.button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
			self.cover_box.button.setFocusPolicy(Qt.NoFocus)
			self.cover_box.button.clicked.connect(self.download_cover)
			self.cover_box.layout.addWidget(self.cover_box.button)
			
		self.cover_box.setLayout(self.cover_box.layout)
		
	def download_cover(self):
		# Downloads cover for a show and displays it.
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			path_to_cover = settings.value("coverDir") + self.IMDB_id + ".jpg"
			
			with open(path_to_cover, "bw") as f:
				f.write(request.urlopen(self.image).read())

			f.close()
			
			self.cover_box.layout.removeWidget(self.cover_box.button) # Removes botton from cover box.
			self.create_cover_box() # Recreates cover box
		
	def create_buttons(self):
		
		self.button_box = QGroupBox()
		self.button_box.layout = QHBoxLayout()

		# Season list that contains all season numbers in string form that will be used later on to populate drop down menu for user to choose a season from.
		# First value has "All" that prints all show's seasons.
		# If show has "Unknown" season list will have an option to choose it too.
		season_list = ["All"]

		# Appends all seasons in string from to season_list
		for i in range(self.seasons):
			season_list.append(str(i + 1))

		# Appends "Unknown" to the end of the list if there is an unknown season.
		if self.unknown_season == 1:
			season_list.append("Unknown")

		self.season_button = QComboBox()
		self.season_button.setMinimumSize(95, 31)
		self.season_button.setFocusPolicy(Qt.NoFocus)
		self.season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		self.season_button.currentTextChanged.connect(self.print_season) # Detects if user chooses different season and send value to print_season function
		
		season_button_label = QLabel("Season")

		# Creates button menu for "Open ..." button
		open_button_menu = QMenu()
		open_button_menu.addAction("IMDB page", self.open_imdb_page)
		open_button_menu.addAction("search in rarbg", self.open_rarbg_search)
		open_button_menu.addAction("search in 1337x", self.open_1337x_search)
		open_button_menu.addAction("search in torrentz2", self.open_torrentz2_search)
				
		# Creates button menu for "Mark ..." button
		mark_as_button_menu = QMenu()
		mark_as_button_menu.addAction("episode as not watched", self.open_mark_episode_as_not_watched)
		mark_as_button_menu.addAction("season as not watched", self.open_mark_season_as_not_watched)
		mark_as_button_menu.addAction("up to episode as watched", self.open_mark_up_to_episode_as_watched)
		mark_as_button_menu.addAction("season as watched", self.open_mark_season_as_watched)
				
		# Creates button menu for "Update ..." button
		update_button_menu = QMenu()
		update_button_menu.addAction("show info", self.open_update_show_info)
		update_button_menu.addAction("single season", self.open_update_single_season)
		update_button_menu.addAction("last three season", self.open_update_last_3_seasons)
		
		# Creates "Manage" button's menu
		manage_button_menu = QMenu()
		manage_button_menu.addAction("Fix Season", self.open_fix_season)
		manage_button_menu.addAction("Change List", self.open_change_list)
		manage_button_menu.addAction("Delete Show", self.open_delete_show)

		# Other buttons to manage database.
		mark_as_button = QPushButton("Mark ...")
		mark_as_button.setFocusPolicy(Qt.NoFocus)
		mark_as_button.setMinimumSize(150, 31)
		mark_as_button.setMenu(mark_as_button_menu)
		update_button = QPushButton("Update ...")
		update_button.setFocusPolicy(Qt.NoFocus)
		update_button.setMinimumSize(150, 31)
		update_button.setMenu(update_button_menu)
		manage_button = QPushButton("Manage")
		manage_button.setFocusPolicy(Qt.NoFocus)
		manage_button.setMenu(manage_button_menu)
		manage_button.setMinimumSize(150, 31)
		open_button = QPushButton("Open ...")
		open_button.setFocusPolicy(Qt.NoFocus)
		open_button.setMenu(open_button_menu)
		open_button.setMinimumSize(150, 31)

		self.button_box.layout.addWidget(season_button_label)
		self.button_box.layout.addWidget(self.season_button)
		self.button_box.layout.insertStretch(2)
		self.button_box.layout.addWidget(mark_as_button)
		self.button_box.layout.addWidget(update_button)
		self.button_box.layout.addWidget(manage_button)
		self.button_box.layout.addWidget(open_button)

		self.button_box.setLayout(self.button_box.layout)
		
	def open_imdb_page(self):
		# This function opens shows IMDB webpage
		
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			imdb_url = "https://www.imdb.com/title/" + self.IMDB_id + "/"
			webbrowser.open(imdb_url, new=2, autoraise=True)

	def open_rarbg_search(self):
		# This function open search for the show in rarbg torrent site.

		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			rardb_url = "https://rarbg2020.org/torrents.php?imdb=" + self.IMDB_id
			webbrowser.open(rardb_url, new=2, autoraise=True)
			return
	
	def open_1337x_search(self):
		# This function open search for the show in 1337x torrent site.
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			x1337_url = "https://1337x.to/search/" + re.sub("\W+", "+", self.title) + "/1/"
			webbrowser.open(x1337_url, new=2, autoraise=True)
			return

	def open_torrentz2_search(self):
		# This function open search for the show in torrentz2 torrent site.
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			torrentz2_url = "https://torrentz2.eu/search?f=" + re.sub("\W+", "+", self.title)
			webbrowser.open(torrentz2_url, new=2, autoraise=True)
			return

	def print_season(self, season):
		# This function set new SQL query to fetch episodes from the database. 
		# Query is set after getting a signal from dropdown menu in create_buttons() function.
		# It resets table row count to 0 (removes data from table) and initiates fill_episode_table() function.

		if season == "All":
			self.episodes_table.sql_select_shows = "SELECT * FROM %s ORDER BY episode_seasonal_id ASC" % self.IMDB_id # This "ORDER BY" is needed to sort episodes that do not have seasonal_id to the top.
		elif season == "Unknown":
			self.episodes_table.sql_select_shows = "SELECT * FROM %s WHERE season = ''" % self.IMDB_id
		else:
			self.episodes_table.sql_select_shows = "SELECT * FROM %s WHERE season = '%s'" % (self.IMDB_id, season)

		self.episodes_table.refill_episode_table()

	def open_fix_season(self):
		
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_fix_season_window = FixSeason(self.IMDB_id, self.seasons, self.unknown_season, self.title)
			result = self.open_fix_season_window.exec_()
			
			if result == QDialog.Accepted:
				self.episodes_table.refill_episode_table()
	
	def open_mark_episode_as_not_watched(self):
		# This function detects if window was closed and refill episode table.
		self.open_mark_episode_as_not_watched_window = OpenMarkAsNotWatched(self.IMDB_id, self.title, self.seasons, self.unknown_season)
		self.open_mark_episode_as_not_watched_window.initUI()
		self.open_mark_episode_as_not_watched_window.destroyed.connect(self.refill_show_info)
		
	def open_mark_season_as_not_watched(self):
		self.open_mark_season_as_not_watched_window = MarkSeasonAsNotWatched(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_mark_season_as_not_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_show_info()
		
	def open_mark_season_as_watched(self):
		self.open_mark_season_as_watched_window = MarkSeasonAsWatched(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_mark_season_as_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_show_info()
	
	def open_mark_up_to_episode_as_watched(self):
		self.open_mark_up_to_episode_as_watched_window = MarkUpToEpisodeAsWatched(self.IMDB_id, self.title, self.seasons, self.unknown_season)
		result = self.open_mark_up_to_episode_as_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_show_info()
			
	def open_update_single_season(self):
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_update_single_season_window = UpdateSingleSeason(self.IMDB_id, self.seasons, self.unknown_season, self.title)
			result = self.open_update_single_season_window.exec_()
			
			if result == QDialog.Accepted:
				self.episodes_table.refill_episode_table()
	
	def open_update_last_3_seasons(self):
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_update_last_3_season_window = UpdateThreeSeasons(self.IMDB_id, self.seasons, self.unknown_season, self.title)
			result = self.open_update_last_3_season_window.exec_()
			
			if result == QDialog.Accepted:
				self.episodes_table.refill_episode_table()
			
	def open_update_show_info(self):
		if has_internet_connection() == False:
			MessagePrompt("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_update_show_info_window = UpdateShowInfo(self.IMDB_id, self.title)
			result = self.open_update_show_info_window.exec_()
			
			if result == QDialog.Accepted:
				self.fetch_show_info()
				self.fill_show_info_box()
				self.update_season_list_combo_box
				
			
	def open_change_list(self):
		self.open_change_list_window = ChangeList(self.IMDB_id, self.finished_watching, self.title)
		result = self.open_change_list_window.exec_()
		
		if result == QDialog.Accepted:
			self.fetch_show_info()
			self.fill_show_info_box()
	
	def open_delete_show(self):
		# This function will open a window to delete all the data from database.
		# After deletion it SHOULD close ShowInfo window too.
		self.open_delete_show_window = DeleteShow(self.IMDB_id, self.title)
		result = self.open_delete_show_window.exec_()
		
		if result == QDialog.Accepted:
			self.close() # SHOULD close the window
			
	def refill_show_info(self):
		# This refill all info of the show info page including episode table.
		# It is used mostly after update functions.
		self.fetch_show_info()
		self.fill_show_info_box()
		self.episodes_table.refill_episode_table()

	def refill_show_info_box(self):
		# This function refills just info of the show, but not the table.
		# It is used when episode is marked as watched to chage watched time count.
		self.fetch_show_info()
		self.fill_show_info_box()

	def update_season_list_combo_box(self):
		# This function only update combo box that contains list of all seasons in show info box.
		# It will be used only after when show info is updated.
		# Code is mostly copied from create_button fucntion.

		# Season list that contains all season numbers in string form that will be used later on to populate drop down menu for user to choose a season from.
		# First value has "All" that prints all show's seasons.
		# If show has "Unknown" season list will have an option to choose it too.
		season_list = ["All"]

		# Appends all seasons in string from to season_list
		for i in range(self.seasons):
			season_list.append(str(i + 1))

		# Appends "Unknown" to the end of the list if there is an unknown season.
		if self.unknown_season == 1:
			season_list.append("Unknown")

		self.season_button.clear() # Cleared combo box.
		self.season_list.insertItems(0, season_list) # Adds updated season list to combo box.

		
class CreateShowInfoEpisodeTable(CreateShowEpisodeTable, QObject):
	# This class used to display episodes in ShowInfo window
	# CreateEpisodesTable class is in series_tracker.py
	
	episode_marked = pyqtSignal() # This is a signal that will be emited after episode is marked as watched.

	def __init__(self, IMDB_id, episode_list):
		QObject.__init__(self) # I don't know whats the difference compared to super. I coppied that from pythoncentral.io
		self.IMDB_id = IMDB_id
		self.sql_select_shows = ""
		self.table_column_count = 5
		self.horizontal_header_labels = ["", "Episode ID", "Air Date", "Episode Title", ""]
		self.episode_list = episode_list

	def create_table(self):

		self.column_to_hide = 5 # Value holds witch column to hide. This was added just for this table, because this column changes depending if there is play button in the table or not.

		self.table_model = QStandardItemModel()

		self.episode_table = QTableView()

		# Setting up to add play button if there are folder with episodes.
		if len(self.episode_list) != 0:
			self.table_column_count = 6 # Changing column count to add "Play" button.
			self.horizontal_header_labels = ["", "Episode ID", "Air Date", "Episode Title", "",""]
			self.column_to_hide = 6 # Hidding last calumn that holds episode_IMDB_id value
		
		self.table_model.setColumnCount(self.table_column_count)
		self.table_model.setHorizontalHeaderLabels(self.horizontal_header_labels)
		# self.table_model.sort(1, Qt.AscendingOrder)		
		
		self.fill_episode_table()

		self.episode_table.setModel(self.table_model)
		self.episode_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents) # Adjust how much space table takes
		self.episode_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Makes table not editable
		self.episode_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Clicking on cell selects row
		self.episode_table.verticalHeader().setVisible(False) # Removing vertincal headers for rows (removing numbering)
		self.episode_table.setSelectionMode(QAbstractItemView.NoSelection) # Makes not able to select cells or rows in table
		# self.episode_table.sortByColumn(1, Qt.AscendingOrder) # Sorts table in ascending order by seasonal ID
		self.episode_table.hideColumn(self.column_to_hide) # Hidding last calumn that holds episode_IMDB_id value	
		# self.episode_table.setShowGrid(False) # Removes grid
		### Setting custom widths for some columns ###
		self.episode_table.setColumnWidth(0, 30)
		self.episode_table.setColumnWidth(1, 100)
		self.episode_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
		self.episode_table.clicked.connect(self.table_clicked) # Detects clicks on the table

	def insert_table_row(self, row_count, episode, IMDB_id):

		# Adding row to the table
		self.table_model.insertRow(row_count)
		# Getting value of shows episode_watched cell
		episode_state = episode.value("episode_watched")
		# Setting checkbox to checked or unchecked depending on episode beeing watched or not

		show_watched = QStandardItem()
		# Making Checkbox not editable
		show_watched.setFlags(Qt.ItemIsEditable)

		# Setting up "Play" button
		if len(self.episode_list) != 0:

			if episode.value("episode_seasonal_id") in self.episode_list:
				button_play_color = QColor(0, 0, 0)
				button_play =  QStandardItem("Play")
			else:
				button_play_color = QColor(160, 161, 162)
				button_play =  QStandardItem("")
				
		# Setting background color for current row, checkbox's checkmark and setting "mark_watched" button status depending if episode is watched or not.
		if episode_state == 1:
			show_watched.setCheckState(Qt.Checked)
			mark_button = QStandardItem("Watched")
			mark_button_color = QColor(160, 161, 162)
		else:
			show_watched.setCheckState(Qt.Unchecked)
			mark_button = QStandardItem("Watched")
			mark_button_color = QColor(0, 0, 0)

		# Settings row's color depending on if episode is wathced and air_dare compared to todey()
		show_watched_color = row_backgound_color(episode.value("air_date"), episode_state)

		# Setting different values to different culumns of the row for the query result.
		self.table_model.setItem(row_count, 0, show_watched)
		self.table_model.item(row_count, 0).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 1, QStandardItem(episode.value("episode_seasonal_id")))
		self.table_model.item(row_count, 1).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 2, QStandardItem(episode.value("air_date")))
		self.table_model.item(row_count, 2).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 3, QStandardItem(episode.value("episode_title")))
		self.table_model.item(row_count, 3).setBackground(show_watched_color)
		# This part of the row changes, because of the different count of the columns
		if len(self.episode_list) != 0:
			# Table's row is made this way if there is a folder for the episodes.
			# This adds a "Play" button.
			self.table_model.setItem(row_count, 4, button_play)
			self.table_model.item(row_count, 4).setTextAlignment(Qt.AlignCenter)
			self.table_model.item(row_count, 4).setForeground(button_play_color)
			if button_play.text() == "":
				# Sets span of the cell (with episode's title) before the one that should have had "Play" button to take it's space.
				self.episode_table.setSpan(row_count, 3, 1, 2)
			self.table_model.setItem(row_count, 5, mark_button)
			self.table_model.item(row_count, 5).setTextAlignment(Qt.AlignCenter)
			self.table_model.item(row_count, 5).setForeground(mark_button_color)
			self.table_model.setItem(row_count, 6, QStandardItem(episode.value("episode_IMDB_id")))
		else:
			# Table's row made this they if there is no folder with show's title.
			# "Play" button is not added to the row.
			self.table_model.setItem(row_count, 4, mark_button)
			self.table_model.item(row_count, 4).setTextAlignment(Qt.AlignCenter)
			self.table_model.item(row_count, 4).setForeground(mark_button_color)
			self.table_model.setItem(row_count, 5, QStandardItem(episode.value("episode_IMDB_id")))

	def table_clicked(self, pos):	
		# Marks episode when clicked on button-cell.
		
		if pos.column() > 3: # If cell that is in column 0 - 3 is clicked does nothing
			
			button_text = self.table_model.item(pos.row(), pos.column()).text() # Name of the button

			if button_text == "Play": # If cell with text "Play" clicked
				episode_seasonal_id = self.table_model.item(pos.row(), 1).text() # Gets episode_seasonl_id from column 1 of the table
				path_to_episode = self.episode_list["path"] + self.episode_list[episode_seasonal_id] # Makes path to the episode that user wants to play by two valies 
				QDesktopServices().openUrl(QUrl.fromLocalFile(path_to_episode))
			else:
				episode_IMDB_id = self.table_model.item(pos.row(), self.column_to_hide).text() # Gets episodes_IMDB_ID from hidden column
					
				if button_text == "Watched":
					episode_state = "1"
					checkbox_state = Qt.Checked
					episode_watched_color = QColor(200, 230, 255)
					mark_button_color = QColor(160, 161, 162)
				else:
					return

				self.table_model.item(pos.row(), self.column_to_hide - 1).setForeground(mark_button_color)
				self.table_model.item(pos.row(), 0).setCheckState(checkbox_state) # Changes state of checkbox

				mark_episode = QSqlQuery("UPDATE %s SET episode_watched = %s WHERE episode_IMDB_id = '%s'" % (self.IMDB_id, episode_state, episode_IMDB_id))
				mark_episode.exec_()

				# Changes background color of the row.
				for n in range(4):
					self.table_model.item(pos.row(), n).setBackground(episode_watched_color)

				self.episode_marked.emit()
