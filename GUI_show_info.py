#! /usr/bin/python3

#This file is resposible for creating Show Info window and all buttons for it.

# Python3 imports
import webbrowser

# PyQt5 imports
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QVBoxLayout, QTabWidget, QLabel, QPushButton, QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView, QGroupBox, QHBoxLayout, QLineEdit, QGridLayout, QComboBox, QMenu
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QFont
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings

from GUI_episode_tracker import CreateShowEpisodesTable
from GUI_show_info_mark import *
from GUI_show_info_update import *
from GUI_show_info_manage import *

settings = QSettings("SeriesTracker", "SeriesTracker")

class OpenShowWindow(QDialog):
	
	def __init__(self, IMDB_id):
		super(OpenShowWindow, self).__init__()
		self.IMDB_id = IMDB_id
		self.initUI()

	def initUI(self):
		# Initiating Show Window
		
		self.fetch_show_info() # Getting all info ready
		
		self.setGeometry(settings.value("top"), settings.value("left"), settings.value("width"), settings.value("height"))
		self.setMinimumSize(settings.value("width"), settings.value("height"))
		self.setWindowTitle(self.title)
		self.setModal(True)

		self.layout = QGridLayout()
		
		self.make_show_info_box()
		
		self.episodes_table = CreateShowEpisodesTable(self.IMDB_id) # Initiating episode table

		self.episodes_table.sql_select_shows = "SELECT * FROM %s" % self.IMDB_id
		self.episodes_table.create_table()	
		
		self.create_buttons()
		
		self.button_ok = QPushButton("OK")
		self.button_ok.clicked.connect(self.accept)

		self.layout.addWidget(self.show_info_box, 0, 0, 8, 12)
		self.layout.addWidget(self.button_box, 9, 0, 1, 12)
		self.layout.addWidget(self.episodes_table.episode_table, 10, 0, 8, 12)
		self.layout.addWidget(self.button_ok, 18, 11, 1, 1)
		self.setLayout(self.layout)
		
		self.show()
		
		self.episodes_table.episode_table.scrollToBottom() # Scrolls table to the bottom
		
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

		image_box = QLabel() # Poster placeholder
		image_box.setMinimumSize(200, 300)
		info_box = QGroupBox() # Group box containing Show's info
		info_box.layout = QVBoxLayout()
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

		self.label_running_time = QLabel()
		self.label_running_time.setFont(font_other)

		self.label_seasons = QLabel()
		self.label_seasons.setFont(font_other)

		# Calculates and add to label how much minutes user spent watching show
		self.label_watched_time = QLabel()
		self.label_watched_time.setFont(font_other)

		self.label_in_list = QLabel()
		self.label_in_list.setFont(font_other)

		self.label_synopsis = QLabel()
		self.label_synopsis.setWordWrap(True)
		self.label_synopsis.setFont(font_synopsis)
		
		info_box.layout.addWidget(self.label_title)
		info_box.layout.addWidget(self.label_years_aired)
		info_box.layout.addWidget(self.label_running_time)
		info_box.layout.addWidget(self.label_seasons)
		info_box.layout.addWidget(self.label_watched_time)
		info_box.layout.addWidget(self.label_in_list)
		info_box.layout.addWidget(self.label_synopsis)

		info_box.setLayout(info_box.layout)

		self.show_info_box.layout.addWidget(image_box, 0, 0)
		self.show_info_box.layout.addWidget(info_box, 0, 1, 1, 3)
		self.show_info_box.setLayout(self.show_info_box.layout)
		
		self.fill_show_info_box()
		
	def fill_show_info_box(self):
		self.label_title.setText(self.title)
		self.label_years_aired.setText("Years aired: " + self.years_aired)
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

		season_button = QComboBox()
		season_button.setMinimumSize(95, 31)
		season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		season_button.currentTextChanged.connect(self.print_season) # Detects if user chooses different season and send value to print_season function
		
		season_button_label = QLabel("Season")

		# Button that opens show's IMDB page
		open_webpage = QPushButton("Open IMDB page")
		open_webpage.clicked.connect(self.open_imdb_page)
		open_webpage.setMinimumSize(150, 31)
				
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
		manage_button_menu.addAction("Delete Show")

		# Other buttons to manage database.
		mark_as_button = QPushButton("Mark ...")
		mark_as_button.setMinimumSize(150, 31)
		mark_as_button.setMenu(mark_as_button_menu)
		update_button = QPushButton("Update ...")
		update_button.setMinimumSize(150, 31)
		update_button.setMenu(update_button_menu)
		manage_button = QPushButton("Manage")
		manage_button.setMenu(manage_button_menu)
		manage_button.setMinimumSize(150, 31)

		self.button_box.layout.addWidget(season_button_label)
		self.button_box.layout.addWidget(season_button)
		self.button_box.layout.insertStretch(2)
		self.button_box.layout.addWidget(mark_as_button)
		self.button_box.layout.addWidget(update_button)
		self.button_box.layout.addWidget(manage_button)
		self.button_box.layout.addWidget(open_webpage)

		self.button_box.setLayout(self.button_box.layout)
		
	def open_imdb_page(self):
		# This function opens shows Webpage
		imdb_url = "https://www.imdb.com/title/" + self.IMDB_id
		webbrowser.open(imdb_url, new=2, autoraise=True)
	
	def print_season(self, season):
		# This function set new SQL query to fetch episodes from the database. 
		# Query is set after getting a signal from dropdown menu in create_buttons() function.
		# It resets table row count to 0 (removes data from table) and initiates fill_episode_table() function.

		if season == "All":
			self.episodes_table.sql_select_shows = "SELECT * FROM %s" % self.IMDB_id
		elif season == "Unknown":
			self.episodes_table.sql_select_shows = "SELECT * FROM %s WHERE season = ''" % self.IMDB_id
		else:
			self.episodes_table.sql_select_shows = "SELECT * FROM %s WHERE season = '%s'" % (self.IMDB_id, season)

		self.refill_episode_table()

	def open_fix_season(self):
		self.open_fix_season_window = FixSeason(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_fix_season_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
	
	def open_mark_episode_as_not_watched(self):
		self.open_mark_episode_as_not_watched_window = OpenMarkAsNotWatched(self.IMDB_id, self.title, self.seasons, self.unknown_season)
		self.open_mark_episode_as_not_watched_window.initUI()
		self.open_mark_episode_as_not_watched_window.destroyed.connect(self.refill_episode_table)
		
	def open_mark_season_as_not_watched(self):
		self.open_mark_season_as_not_watched_window = MarkSeasonAsNotWatched(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_mark_season_as_not_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
		
	def open_mark_season_as_watched(self):
		self.open_mark_season_as_watched_window = MarkSeasonAsWatched(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_mark_season_as_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
	
	def open_mark_up_to_episode_as_watched(self):
		self.open_mark_up_to_episode_as_watched_window = MarkUpToEpisodeAsWatched(self.IMDB_id, self.title, self.seasons, self.unknown_season)
		result = self.open_mark_up_to_episode_as_watched_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
			
	def open_update_single_season(self):
		self.open_update_single_season_window = UpdateSingleSeason(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_update_single_season_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
	
	def open_update_last_3_seasons(self):
		self.open_update_single_season_window = UpdateThreeSeasons(self.IMDB_id, self.seasons, self.unknown_season, self.title)
		result = self.open_update_single_season_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_episode_table()
			
	def open_update_show_info(self):
		self.open_update_show_info_window = UpdateShowInfo(self.IMDB_id, self.title)
		result = self.open_update_show_info_window.exec_()
		
		if result == QDialog.Accepted:
			self.fetch_show_info()
			self.fill_show_info_box()
			
	def open_change_list(self):
		self.open_change_list_window = ChangeList(self.IMDB_id, self.finished_watching, self.title)
		result = self.open_change_list_window.exec_()
		
		if result == QDialog.Accepted:
			self.fetch_show_info()
			self.fill_show_info_box()
	
	def refill_episode_table(self):

		self.episodes_table.table_model.setRowCount(0)
		self.episodes_table.fill_episode_table()
		self.episodes_table.episode_table.scrollToBottom() # Scrolls table to the bottom
