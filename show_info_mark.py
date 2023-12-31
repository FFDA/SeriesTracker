#! /usr/bin/python3

# This file creates windows for all "Mark ..." button options

# Python3 imports
from functools import partial

# PyQt5 imports
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView, QGroupBox, QHBoxLayout, QDialog, QScrollArea, QComboBox, QGridLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings, QSize, QPoint
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

from series_tracker import CreateShowEpisodeTable
from misc import center

settings = QSettings("SeriesTracker", "SeriesTracker")

class MarkSeasonAsNotWatched(QDialog):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(MarkSeasonAsNotWatched, self).__init__()
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.window_title = "Choose season of %s to mark as watched" % self.title
		self.message_text = "Mark season %s as not watched"
		self.sql_season_mark = ""
		self.confirm_button_text = "Mark As Not Watched"
		self.initUI()

	def initUI(self):
		self.resize(300, 200)
		center(self)
		self.setWindowTitle(self.window_title)
		self.setModal(True)
		
		self.layout = QGridLayout()
		self.create_buttons()
		self.message = QLabel("You haven't selected a season")
		self.message.setAlignment(Qt.AlignCenter)
		
		# Confirmation buttonss		
		self.cancel = QPushButton("Cancel")
		self.confirm = QPushButton(self.confirm_button_text)	
		self.confirm.setDisabled(True)
		self.cancel.clicked.connect(self.reject)
		self.confirm.clicked.connect(self.mark_season_as_watched)
		
		self.layout.addWidget(self.season_button_label, 0, 1, 1, 1)
		self.layout.addWidget(self.season_button, 0, 2, 1, 1)
		self.layout.addWidget(self.message, 1, 0, 1, 4)
		self.layout.addWidget(self.cancel, 2, 0, 1, 1)
		self.layout.addWidget(self.confirm, 2, 3, 1, 1)
		self.setLayout(self.layout)
	
	def message_box_text(self, season):
		if season != "":
			self.message.setText(self.message_text % season)
			self.sql_season_mark = "UPDATE %s SET episode_watched = 0 WHERE season = %s" % (self.IMDB_id, season)
			self.confirm.setDisabled(False)
		else:
			self.message.setText("You haven't selected a season")
			self.confirm.setDisabled(True)
	
	def create_buttons(self):

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
		self.season_button.currentTextChanged.connect(self.message_box_text) # Detects if user chooses different season and sends value to print_season function
		
		self.season_button_label = QLabel("Season")
		

	def mark_season_as_watched(self):
		if self.sql_season_mark == "":
			self.message.setText("Please select a season")
		else:
			mark_season = QSqlQuery(self.sql_season_mark)
			mark_season.exec_()
			self.accept()

class MarkSeasonAsWatched(MarkSeasonAsNotWatched):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(MarkSeasonAsNotWatched, self).__init__() # Parent class name has to be passed to super for it to work!
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.window_title = "Choose season of %s to mark as watched" % self.title
		self.message_text = "Mark season %s as watched"
		self.sql_season_mark = ""
		self.confirm_button_text = "Mark As Watched"
		self.initUI()

	def message_box_text(self, season):
		if season != "":
			self.message.setText(self.message_text % season)
			self.sql_season_mark = "UPDATE %s SET episode_watched = 1 WHERE season = %s" % (self.IMDB_id, season)
			self.confirm.setDisabled(False)
		else:
			self.message.setText("You haven't selected a season")
			self.confirm.setDisabled(True)

class MarkUpToEpisodeAsWatched(QDialog):
	
	def __init__(self, IMDB_id, title, seasons, unknown_season):
		super(MarkUpToEpisodeAsWatched, self).__init__()
		self.IMDB_id = IMDB_id
		self.title = title
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.window_title = "Choose episode of %s" % self.title
		self.message_text = "Select the episode and press confirm. All episodes up to selected one will be marked as watched."
		self.sql_episode_mark = ""
		self.initUI()
		
	def initUI(self):
		self.resize(800, 500)
		center(self)
		self.setWindowTitle(self.window_title)
		self.layout = QVBoxLayout()
		
		self.message = QLabel(self.message_text)
		self.message.setWordWrap(True)
		self.message.setAlignment(Qt.AlignCenter)
		
		self.create_confirmation_buttons()
		
		self.create_episode_tables()
		
		self.mark_message = QLabel("You haven't selected an episode")
		self.mark_message.setAlignment(Qt.AlignCenter)
		
		self.layout.addWidget(self.message)
		self.layout.addWidget(self.scroll_area)
		self.layout.addWidget(self.mark_message)
		self.layout.addWidget(self.confirmation_button_box)
		
		self.setLayout(self.layout)
		
	def create_episode_tables(self):
		
		self.table_dict = {} # THis is a dictionary that holds every table in it.
		
		self.scroll_area = QScrollArea()
		
		self.scroll_area.setWidgetResizable(True)
		self.episode_tables = QWidget()
		self.episode_tables.layout = QGridLayout()
		
		# Integers that hold values to make a 3x3 grid from tables.
		widget_row_count = 0
		widget_col_count = 0

		for season in range(1, self.seasons + 1):
			
			self.table_box = QGroupBox()
			self.table_box.layout = QVBoxLayout()
			self.table_box.setTitle("%d Season" % season)
			
			self.table_dict["self.episode_table_widget_{0}".format(season)] = QTableWidget() # Creates dictory keys with name that starts "self.episode_table_widget_" and has season number at the end. Item for this dictionary item is a QTableWidget.
			
			current_table_widget = self.table_dict["self.episode_table_widget_{0}".format(season)] # Asings normalish name for the table widget
			
			current_table_widget.setColumnCount(3)
			current_table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers) # Makes widget not editable
			current_table_widget.setSelectionMode(QAbstractItemView.SingleSelection) # Makes that it is possible to select only one cell at a time.
			
			selected_episodes = QSqlQuery("SELECT episode_seasonal_id FROM %s WHERE season = '%s'" % (self.IMDB_id, season))
			
			# Variables to make table as 3x3 grid.		
			row_count = 0
			col_count = 0
			
			current_table_widget.insertRow(row_count)
			
			while selected_episodes.next():
						
				if col_count == 3: # Resets tables column count every third coumn and adds an extra line to the table
					col_count = 0
					row_count += 1
					current_table_widget.insertRow(row_count)
				
				current_table_widget.setItem(row_count, col_count, QTableWidgetItem(selected_episodes.value("episode_seasonal_id")))
				
				col_count += 1

			current_table_widget.verticalHeader().setVisible(False)
			current_table_widget.horizontalHeader().setVisible(False)
			current_table_widget.resizeColumnsToContents()
			
			current_table_widget.cellClicked.connect(partial(self.make_sql_query, season))
			
			# Resest widget_col_count every third column
			if widget_col_count == 3:
				widget_col_count = 0
				widget_row_count += 1
			
			widget_col_count += 1
			
			# Following code I repurposed from StackOverlow.
			# https://stackoverflow.com/questions/41542934/pyqt-qtablewidget-remove-scrollbar-to-show-full-table
			
			current_table_widget_width = 4 # Needed for horizontal header to have some room.
			current_table_widget_height = 4 # Needed for vertical header to have some room.
				
			for i in range(current_table_widget.columnCount()): # For range of all columns
				current_table_widget_width += current_table_widget.columnWidth(i) # adds current row's width to total count
			for i in range(current_table_widget.rowCount()): # For range of all rows
				current_table_widget_height += current_table_widget.rowHeight(i) # adds current row's height to total count
			
			# Sets min and max size of current table	
			current_table_widget.setMaximumSize(QSize(current_table_widget_width, current_table_widget_height))
			current_table_widget.setMinimumSize(QSize(current_table_widget_width, current_table_widget_height))
			
			self.table_box.layout.addWidget(current_table_widget)
			self.table_box.setLayout(self.table_box.layout)
						
			self.episode_tables.layout.addWidget(self.table_box, widget_row_count, widget_col_count) # Adds table to episode_tables grid
			
		self.episode_tables.setLayout(self.episode_tables.layout)
		
		self.scroll_area.setWidget(self.episode_tables)
		
	def make_sql_query(self, season, row, col):
		# This function checks if user clicked on cell with data. If there is an episode_seasoal_id it sets/uptates sql query that will be used to update database and prints message to user.
		# Otherwise it prints a message to user saying that he has to select an episode and sets sql_query string to empty one.
		try:
			episode_seasonal_id = self.table_dict["self.episode_table_widget_{0}".format(season)].item(row, col).text()
			self.mark_message.setText("Episodes up to and including %s will be marked as watched" % episode_seasonal_id)
			self.sql_episode_mark = "UPDATE %s SET episode_watched = 1 WHERE episode_seasonal_id <= '%s' AND episode != ''" % (self.IMDB_id, episode_seasonal_id)
			self.confirm.setDisabled(False)
		except AttributeError:
			self.mark_message.setText("You haven't selected an episode")
			self.sql_episode_mark = ""
			self.confirm.setDisabled(True)
			

	def create_confirmation_buttons(self):
		# Creates button that will be displayed at the bottom of the Window to confirm or cancel action.
		self.confirmation_button_box = QGroupBox()
		self.confirmation_button_box.layout = QHBoxLayout()
				
		cancel = QPushButton("Cancel")
		self.confirm = QPushButton("Mark as Watched")
		self.confirm.setDisabled(True)
		
		cancel.clicked.connect(self.reject) #This button rejects the action and closes window withour changing anything in database.
		self.confirm.clicked.connect(self.mark_up_to_episode)
		
		self.confirmation_button_box.layout.addWidget(cancel)
		self.confirmation_button_box.layout.addWidget(self.confirm)
		
		self.confirmation_button_box.setLayout(self.confirmation_button_box.layout)
		
	def mark_up_to_episode(self):
		# Marks all episodes to as watched if query isn't empty.
		# Otherwise prints a message to user.
		if self.sql_episode_mark != "":
			mark_query = QSqlQuery(self.sql_episode_mark)
			mark_query.exec_()
			self.accept()
		else:
			self.mark_message.setText("Please choose an episode or click cancel") 

class OpenMarkAsNotWatched(QWidget):

	def __init__(self, IMDB_id, title, seasons, unknown_season):
		super(OpenMarkAsNotWatched, self).__init__()
		self.IMDB_id = IMDB_id
		self.title = title
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.setAttribute(Qt.WA_DeleteOnClose)
		
	def initUI(self):
		self.resize(int(settings.value("width")), int(settings.value("height")))
		center(self)
		self.setMinimumSize(int(settings.value("width")), int(settings.value("height")))
		self.setWindowTitle("Mark %s episodes as not watched" % self.title)
		self.setWindowModality(Qt.ApplicationModal) # This function disables other windows untill user closes Show Window

		self.layout = QVBoxLayout()
		
		self.episodes_table = CreateShowEpisodeTable(self.IMDB_id)
		self.episodes_table.sql_select_shows = "SELECT * FROM %s" % self.IMDB_id
		self.episodes_table.create_table()
		
		self.create_buttons()
		
		self.layout.addWidget(self.button_box)
		self.layout.addWidget(self.episodes_table.episode_table)
		self.setLayout(self.layout)
		self.show()
		
		self.episodes_table.episode_table.scrollToBottom()

	def create_buttons(self):
		
		self.button_box = QGroupBox()
		self.button_box.layout = QGridLayout()

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
		season_button.setFocusPolicy(Qt.NoFocus)
		season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		season_button.currentTextChanged.connect(self.print_season) # Detects if user chooses different season and send value to print_season function
		
		season_button_label = QLabel("Season")
		
		self.button_box.layout.addWidget(season_button_label, 0, 1, Qt.AlignRight)
		self.button_box.layout.addWidget(season_button, 0, 2, Qt.AlignLeft)
		
		self.button_box.setLayout(self.button_box.layout)
	
		
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

		self.episodes_table.refill_episode_table()

