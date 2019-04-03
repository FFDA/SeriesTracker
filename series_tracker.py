#! /usr/bin/python3

#Imporing Python3 stuff
import sys
import datetime
import sqlite3
from functools import partial

# Importing PyQt5 stuff
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings, QCoreApplication
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication, QVBoxLayout, QTabWidget, QLabel, QPushButton, QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView, QGroupBox, QHBoxLayout, QLineEdit, QGridLayout, QDialog, QShortcut
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor

from database import *
from misc import *
from show_info import *
from add_show import *

# PyQt5 settings
settings = QSettings("SeriesTracker", "SeriesTracker")

settings.setValue("width", 1200)
settings.setValue("height", 800)

class mainWindow(QMainWindow):

	def __init__(self):
		super().__init__()
		self.initUI()	

	def initUI(self):
		db = DatabaseConnection
		db.check(self)
		db.connect()
		self.resize(settings.value("width"), settings.value("height"))	
		center(self)
		self.setWindowTitle("Series Episode Tracker")
		self.tab_widget = TabWidget(self)
		self.setCentralWidget(self.tab_widget)
		self.show()

class TabWidget(QWidget):
	
	def __init__(self, parent):
		super(QWidget, self).__init__(parent)
		# Initializeing layout for the widget of the main Window?
		self.layout = QVBoxLayout(self)
		
		# Initializing tab screen by setting QTabWidget and than adding tabs with QWidget as a main function.
		self.tabs = QTabWidget()
		self.tab1 = QWidget()
		self.tab2 = QWidget()

		# Adding tabs to the tabs (QTabWidget) widget and setttig names for it.
		self.tabs.addTab(self.tab1, "Recent Episodes")
		self.tabs.addTab(self.tab2, "Shows")
		
		# Detecting if tab changed and innitaing function.
		self.tabs.currentChanged.connect(self.tab_changed)
		
		# Telling to look for a function that will set information in the widget.
		self.tab1UI()
		self.tab2UI()

		# Adding tabs to the widget
		self.layout.addWidget(self.tabs)
		self.setLayout(self.layout)
		
	# Defining first tab UI.
	def tab1UI(self):
		
		# Setting tab1 layout to vertical
		self.tab1.layout = QVBoxLayout()
		
		# Setting up Latest Episodes table
		self.latest_episodes = CreateEpisodesTable()
		self.latest_episodes.label_text = "Latest Episodes"
		self.latest_episodes.sql_select_shows = "SELECT * FROM shows WHERE finished_watching = 0"
		self.latest_episodes.sql_filter_episodes = "SELECT * FROM %s WHERE LENGTH(air_date) > 7 AND air_date < '%s' ORDER BY air_date ASC"
		self.latest_episodes.create_label()
		self.latest_episodes.create_table()
		self.latest_episodes.fill_episode_table()
		
		# Setting up Next Episodes table
		self.next_episodes = CreateUpcomingEpisodesTable()
		self.next_episodes.label_text = "Upcoming Episodes"
		self.next_episodes.sql_select_shows = "SELECT * FROM shows WHERE finished_watching = 0"
		self.next_episodes.sql_filter_episodes = "SELECT * FROM %s WHERE air_date >= '%s' ORDER BY episode_seasonal_id ASC"
		self.next_episodes.create_label()
		self.next_episodes.create_table()
		self.next_episodes.fill_episode_table()
		
		# Adding label to the tab1 layout
		self.tab1.layout.addWidget(self.latest_episodes.episode_table_label)
		# Adding table to the tab1 layout
		self.tab1.layout.addWidget(self.latest_episodes.episode_table)
		self.tab1.layout.addWidget(self.next_episodes.episode_table_label)
		self.tab1.layout.addWidget(self.next_episodes.episode_table)
		# Adding setting tab1 laytout
		self.tab1.setLayout(self.tab1.layout)


	def tab2UI(self):

		# Setting tab2 laytout to vertival
		self.tab2.layout = QGridLayout()
		
		self.shows_table = CreateShowTables()

		self.shows_table.create_buttons()
		self.shows_table.create_table()
		self.shows_table.create_filter_box()
		self.shows_table.fill_table()

		self.tab2.layout.addWidget(self.shows_table.button_box, 0, 0, 1, 4)
		self.tab2.layout.addWidget(self.shows_table.button_add_show_box, 0, 5, 1, 1)
		self.tab2.layout.addWidget(self.shows_table.filter_box,1, 0, 1, 6)
		self.tab2.layout.addWidget(self.shows_table.shows_table, 2, 0, 10, 6)
		self.tab2.setLayout(self.tab2.layout)
		
		focus_search = QShortcut("CTRL+F", self)
		focus_search.activated.connect(self.set_focus_on_search)
		
				
	def tab_changed(self, index):
		# Checks to which tab user changed to. Set focus on search field in "Shows" tab.
		if index == 0:
			self.latest_episodes.refill_episode_table()
			self.next_episodes.refill_episode_table()
		else:
			self.shows_table.refill_table(self.shows_table.sql_query)
			self.set_focus_on_search()
			
	def set_focus_on_search(self):
		# Sets focus on search field in "Shows" tab
		self.shows_table.filter_box.setFocus() # Auto focuses on Filter box every time user clicks on Shows tab.
		

class CreateEpisodesTable:

	# Variable with current date for to compare episode's air_date later
	current_year = datetime.datetime.today().strftime("%Y")
	current_month_day = datetime.datetime.today().strftime("%m-%d")
	
	def __init__(self):
		self.sql_select_shows = ""
		self.label_text = ""
		self.sql_filter_episodes = ""
		self.table_column_count = 7
		self.horizontal_header_labels = ["", "Title", "Episode", "Air Date", "Episode Title", ""]
	
	def create_label(self):
		# Adding label
		self.episode_table_label = QLabel(self.label_text)
		self.episode_table_label.setMargin(5)
		# Setting alighment of the label
		self.episode_table_label.setAlignment(Qt.AlignHCenter)

	def create_table(self):

		self.table_model = QStandardItemModel()
		self.table_model.setColumnCount(self.table_column_count)
		self.table_model.setHorizontalHeaderLabels(self.horizontal_header_labels)

		self.episode_table = QTableView()
		self.episode_table.setModel(self.table_model)
		self.episode_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents) # Adjust how much space table takes
		self.episode_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Makes table not editable
		self.episode_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Clicking on cell selects row
		self.episode_table.verticalHeader().setVisible(False) # Removing vertincal headers for rows (removing numbering)
		self.episode_table.setSelectionMode(QAbstractItemView.NoSelection) # Makes not able to select cells or rows in table
		self.episode_table.hideColumn(6) # Hidding last calumn that holds IMDB_id value
		# self.episode_table.setShowGrid(False) # Removes grid
		### Setting custom widths for some columns ###
		self.episode_table.setColumnWidth(0, 30)
		self.episode_table.setColumnWidth(1, 340)
		self.episode_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

	# Marks episode as watched and repopulates table with updated data.
	def mark_watched(self, IMDB_id, episode_IMDB_id):
		mark_episode = QSqlQuery("UPDATE %s SET episode_watched = 1 WHERE episode_IMDB_id = '%s'" % (IMDB_id, episode_IMDB_id))
		mark_episode.exec_()
		self.refill_episode_table()

	def fill_episode_table(self):
		# Setting variable to 0 because row count is unknown
		row_count = 0

		# Selecting using provided query
		selected = QSqlQuery(self.sql_select_shows)

		# Iterating thought every quary result
		while selected.next():

			# Selecting all episodes from show in the watchlist that has air_date longer than 4 digists and which has air_date beforte current date. Ordering results in descending order.
			episode = QSqlQuery(self.sql_filter_episodes % (selected.value("IMDB_id"), self.current_year + "-" + self.current_month_day))
			episode.last()
			self.insert_table_row(row_count, episode, selected.value("IMDB_id"), selected.value("title"))

			row_count += 1
		
		self.episode_table.sortByColumn(1, Qt.AscendingOrder) #Orders table after filling it
		self.episode_table.doubleClicked.connect(self.open_show) # Enables double click on

	def insert_table_row(self, row_count, episode, IMDB_id, title):

			# Adding row to the table
			self.table_model.insertRow(row_count)
			# Getting value of shows episode_watched cell
			episode_state = episode.value("episode_watched")
			# Setting checkbox to checked or unchecked depending on episode beeing watched or not
			mark_watched_button = QPushButton("Watched")
			mark_watched_button.setFlat(True)
	
			show_watched = QStandardItem()
			# Making Checkbox not editable
			show_watched.setFlags(Qt.ItemIsEditable)
	
			# Setting background color for current row, checkbox's checkmark and setting "mark_watched" button status depending if episode is watched or not.
			if episode_state == 1:
				show_watched.setCheckState(Qt.Checked)
				show_watched_color = QColor(200, 230, 255)
				mark_watched_button.setEnabled(False)
			else:
				show_watched.setCheckState(Qt.Unchecked)
				show_watched_color = QColor(200, 255, 170)
	
			# Setting background color to red if current_date is smaller than air_date of the episode.
			if episode.value("air_date") > self.current_year + "-" + self.current_month_day or episode.value("air_date") == None or len(episode.value("air_date")) < 8:

				show_watched_color = QColor(255, 170, 175)
	
			# Setting different values to different culumns of the row for the query result.
			self.table_model.setItem(row_count, 0, show_watched)
			self.table_model.item(row_count, 0).setBackground(show_watched_color)
			self.table_model.setItem(row_count, 1, QStandardItem(title))
			self.table_model.item(row_count, 1).setBackground(show_watched_color)
			self.table_model.setItem(row_count, 2, QStandardItem(episode.value("episode_seasonal_id")))
			self.table_model.item(row_count, 2).setBackground(show_watched_color)
			self.table_model.setItem(row_count, 3, QStandardItem(episode.value("air_date")))
			self.table_model.item(row_count, 3).setBackground(show_watched_color)
			self.table_model.setItem(row_count, 4, QStandardItem(episode.value("episode_title")))
			self.table_model.item(row_count, 4).setBackground(show_watched_color)
			self.episode_table.setIndexWidget(self.table_model.index(row_count, 5), mark_watched_button)
			mark_watched_button.clicked.connect(partial(self.mark_watched, IMDB_id, episode.value("episode_IMDB_id")))
			self.table_model.setItem(row_count, 6, QStandardItem(IMDB_id))

	# Retrieves shows IMDB_id on which was clicked and opens show info window
	def open_show(self, pos):
		IMDB_id = self.table_model.data(self.table_model.index(pos.row(), 6))
		self.show_window = OpenShowWindow(IMDB_id)
		self.show_window.initUI()
		
		self.show_window.destroyed.connect(self.refill_episode_table)

		
	def refill_episode_table(self):
		self.episode_table.doubleClicked.disconnect(self.open_show)
		self.table_model.setRowCount(0)
		self.fill_episode_table()

class CreateUpcomingEpisodesTable(CreateEpisodesTable):

	def fill_episode_table(self):
		# Setting variable to 0 because row count is unknown
		row_count = 0

		# Selecting using provided query
		selected = QSqlQuery(self.sql_select_shows)

		# Iterating thought every quary result
		while selected.next():

			# Selecting all episodes from show in the watchlist that has air_date longer than 4 digists and which has air_date beforte current date. Ordering results in descending order.
			episode = QSqlQuery(self.sql_filter_episodes % (selected.value("IMDB_id"), self.current_year + "-" + self.current_month_day))
			if episode.first() == True:
				self.insert_table_row(row_count, episode, selected.value("IMDB_id"), selected.value("title"))
				row_count += 1
			else:
				episode = QSqlQuery("SELECT * FROM %s WHERE episode_watched = 0 AND (air_date IS null OR length(air_date) <= 8)" % selected.value("IMDB_id"))
				if episode.first() == True:
					self.insert_table_row(row_count, episode, selected.value("IMDB_id"), selected.value("title"))
					row_count += 1
				else:
				  pass

		self.episode_table.doubleClicked.connect(self.open_show)
		
		self.episode_table.sortByColumn(1, Qt.AscendingOrder) #Orders table after filling it

	def insert_table_row(self, row_count, episode, IMDB_id, title):
		# Adding row to the table
		self.table_model.insertRow(row_count)
		# Getting value of shows episode_watched cell
		episode_state = episode.value("episode_watched")
		# Setting checkbox to checked or unchecked depending on episode beeing watched or not
		mark_watched_button = QPushButton("Watched")
		mark_watched_button.setFlat(True)

		show_watched = QStandardItem()
		# Making Checkbox not editable
		show_watched.setFlags(Qt.ItemIsEditable)
 
		# Setting background color for current row, checkbox's checkmark and setting "mark_watched" button status depending if episode is watched or not.
		if episode_state == 1:
			show_watched.setCheckState(Qt.Checked)
			show_watched_color = QColor(200, 230, 255)
			mark_watched_button.setEnabled(False)
		else:
			show_watched.setCheckState(Qt.Unchecked)
			show_watched_color = QColor(200, 255, 170)
 
		# Setting background color to red if current_date is smaller than air_date of the episode.
		if episode.value("air_date") > self.current_year + "-" + self.current_month_day or episode.value("air_date") == None or len(episode.value("air_date")) < 8:
			show_watched_color = QColor(255, 170, 175)

		# Setting different values to different culumns of the row for the query result.
		self.table_model.setItem(row_count, 0, show_watched)
		self.table_model.item(row_count, 0).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 1, QStandardItem(title))
		self.table_model.item(row_count, 1).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 2, QStandardItem(episode.value("episode_seasonal_id")))
		self.table_model.item(row_count, 2).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 3, QStandardItem(episode.value("air_date")))
		self.table_model.item(row_count, 3).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 4, QStandardItem(episode.value("episode_title")))
		self.table_model.item(row_count, 4).setBackground(show_watched_color)
		self.episode_table.setIndexWidget(self.table_model.index(row_count, 5), mark_watched_button)
		mark_watched_button.clicked.connect(partial(self.mark_watched, IMDB_id, episode.value("episode_IMDB_id")))
		self.table_model.setItem(row_count, 6, QStandardItem(IMDB_id))



class CreateShowTables:
	
	# This class creates UI for "Shows" tab.

	def __init__(self):
		# self.table_label_text = "All Shows"
		self.horizontal_header_labels = ["Title", "Seasons", "Status", "Years aired", "Synopsis"]
		self.table_column_count = 6
		self.sql_query = "SELECT * FROM shows ORDER BY title ASC"
	
	def create_buttons(self):

		# Innitiating box for buttons and adding layout for it.
		
		self.button_add_show_box = QGroupBox()
		self.button_add_show_box.layout = QHBoxLayout()	
		
		# Creates Add Show button and it's layout.
		button_add_show = QPushButton("Add Show")
		button_add_show.setFocusPolicy(Qt.NoFocus)
		button_add_show.clicked.connect(self.open_add_show)
		self.button_add_show_box.layout.addWidget(button_add_show)		
		self.button_add_show_box.setLayout(self.button_add_show_box.layout)
		
		self.get_show_count()
		
		self.button_box = QGroupBox()
		self.button_box.layout = QHBoxLayout()

		self.btn_all_shows = QPushButton("All Shows " + "(" + self.count_all + ")")
		self.btn_watchlist = QPushButton("Watchlist " + "(" + self.count_watchlist + ")")
		self.btn_finished_watching = QPushButton("Finished Watching " + "(" + self.count_finished_watching + ")") 
		self.btn_plan_to_watch = QPushButton("Plan to Watch " + "(" + self.count_plan_to_watch + ")")

		# Making buttons checkable to make them look differently, and to make them work exclusively
		self.btn_all_shows.setCheckable(True)
		self.btn_all_shows.setFocusPolicy(Qt.NoFocus)
		self.btn_watchlist.setCheckable(True)
		self.btn_watchlist.setFocusPolicy(Qt.NoFocus)
		self.btn_finished_watching.setCheckable(True)
		self.btn_finished_watching.setFocusPolicy(Qt.NoFocus)
		self.btn_plan_to_watch.setCheckable(True)
		self.btn_plan_to_watch.setFocusPolicy(Qt.NoFocus)

		# Setting default button
		self.btn_all_shows.setChecked(True)	

		# Set buttons to work exclusively 
		self.btn_all_shows.setAutoExclusive(True)
		self.btn_watchlist.setAutoExclusive(True)
		self.btn_finished_watching.setAutoExclusive(True)
		self.btn_plan_to_watch.setAutoExclusive(True)

		self.button_box.layout.addWidget(self.btn_all_shows)
		self.button_box.layout.addWidget(self.btn_watchlist)
		self.button_box.layout.addWidget(self.btn_finished_watching)
		self.button_box.layout.addWidget(self.btn_plan_to_watch)

		# Linking buttons with function and passing different sql_query
		self.btn_all_shows.clicked.connect(partial(self.refill_table, "SELECT * FROM shows ORDER BY title ASC"))
		self.btn_watchlist.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE finished_watching = 0 ORDER BY title ASC"))
		self.btn_finished_watching.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE  finished_watching = 1 ORDER BY title ASC"))
		self.btn_plan_to_watch.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE finished_watching = 2 ORDER BY title ASC"))

		self.button_box.setLayout(self.button_box.layout)
		
	def get_show_count(self):
		# Retrives how many shows there are in each list
		sql_count_all = QSqlQuery("SELECT COUNT(*) FROM shows")
		sql_count_all.first()
		self.count_all = str(sql_count_all.value(0))
		
		sql_count_watchlist = QSqlQuery("SELECT COUNT(*) FROM shows WHERE finished_watching = 0")
		sql_count_watchlist.first()
		self.count_watchlist = str(sql_count_watchlist.value(0))
		
		sql_count_finished_watching = QSqlQuery("SELECT COUNT() FROM shows WHERE finished_watching = 1")
		sql_count_finished_watching.first()
		self.count_finished_watching = str(sql_count_finished_watching.value(0))
		
		sql_count_plan_to_watch = QSqlQuery("SELECT COUNT() FROM shows WHERE finished_watching = 2")
		sql_count_plan_to_watch.first()
		self.count_plan_to_watch = str(sql_count_plan_to_watch.value(0))


	def create_filter_box(self):
		
		# Adding search/filter box
		self.filter_box = QLineEdit()
		self.filter_box.setClearButtonEnabled(True)
		self.filter_box.setPlaceholderText("Start typing show's title")
		self.filter_box.textChanged.connect(self.filter_model.setFilterRegExp)

	def create_table(self):

		# Making table model that has to be added to QTableView, but in this case it will be added as a source model for QSortFilterProxyModel to be able to filter results on the go.
		self.table_model = QStandardItemModel()
		self.table_model.setColumnCount(self.table_column_count)
		self.table_model.setHorizontalHeaderLabels(self.horizontal_header_labels)

		# This intermediate model allows to filter show table
		self.filter_model = QSortFilterProxyModel()
		self.filter_model.setSourceModel(self.table_model)
		self.filter_model.setFilterKeyColumn(0) # Setting target column of the filter function. It can be changed to -1 to from all columns.
		self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # Making filter regex not case sensitive.

		# TableView model that actually displays show table
		self.shows_table = QTableView()
		self.shows_table.setWordWrap(False) # Had to add this, because PyQt5 from pip has different default parameters from feroda's repository's PyQt5.
		self.shows_table.setModel(self.filter_model)
		self.shows_table.verticalHeader().setVisible(False)
		self.shows_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.shows_table.setColumnWidth(0, 200)
		self.shows_table.setColumnWidth(2, 110)
		self.shows_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Selects full rows only
		self.shows_table.setSelectionMode(QAbstractItemView.SingleSelection) # Selects only one line at time.
		self.shows_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
		self.shows_table.hideColumn(5) # Hides column that has IMDB_id in it.
		self.shows_table.setSortingEnabled(True) # Enables sorting by column when clicking on them.
		self.shows_table.sortByColumn(0, Qt.AscendingOrder)


	def fill_table(self):
		
		row_count = 0

		selected = QSqlQuery(self.sql_query)

		while selected.next():

			self.table_model.insertRow(row_count)

			# Getting values that have to be converted to text
			status_value = selected.value("finished_airing")
			if status_value == 1:
				status = "Still Airing"
			else:
				status = "Finished Airing"

			self.table_model.setItem(row_count, 0, QStandardItem(selected.value("Title")))
			self.table_model.setItem(row_count, 1, QStandardItem(str(selected.value("seasons"))))
			self.table_model.item(row_count, 1).setTextAlignment(Qt.AlignCenter)
			self.table_model.setItem(row_count, 2, QStandardItem(status))
			self.table_model.setItem(row_count, 3, QStandardItem(selected.value("years_aired")))
			self.table_model.setItem(row_count, 4, QStandardItem(selected.value("synopsis")))
			self.table_model.setItem(row_count, 5, QStandardItem(selected.value("IMDB_id")))
			
			row_count += 1

		self.shows_table.doubleClicked.connect(self.open_show)
		
		
	def refill_table(self, new_query):
		self.sql_query = new_query
		self.table_model.setRowCount(0)
		self.shows_table.doubleClicked.disconnect(self.open_show) # Disconnects table with double click signal. Otherwise with every chage of the table when buttons are used it will add more signals. This signal will be reimplemented with fill_table().
		self.fill_table()
		self.redo_buttons()

	
	def redo_buttons(self):
		self.get_show_count()
		self.btn_all_shows.setText("All Shows " + "(" + self.count_all + ")")
		self.btn_watchlist.setText("Watchlist " + "(" + self.count_watchlist + ")")
		self.btn_finished_watching.setText("Finished Watching " + "(" + self.count_finished_watching + ")") 
		self.btn_plan_to_watch.setText("Plan to Watch " + "(" + self.count_plan_to_watch + ")")

	def open_show(self, pos):
		# Clicking action is done on the show_table, but data actually has to be fetched from QSortFilterProxyModel.
		# For this reason you have to get index of item in filter_model using special index function.
		# Lastly use this index in data() function on filter_model to retrieve information from cell that you/user actually see.
		IMDB_id = self.filter_model.data(self.filter_model.index(pos.row(), 5))
		self.show_window = OpenShowWindow(IMDB_id)
		self.show_window.initUI()		
		self.show_window.destroyed.connect(partial(self.refill_table, self.sql_query))
		
	def open_add_show(self):
		self.open_add_show_window = AddShow()
		result = self.open_add_show_window.exec_()
		
		if result == QDialog.Accepted:
			self.refill_table(self.sql_query)


class CreateShowEpisodeTable(CreateEpisodesTable):
	# Base class to create episode that shows all episodes id the class and allows episodes to be marked as watched/unwatched.
	# This class without any changes is used in show_info_mark.py
	# Modified used in show_info
	
	def __init__(self, IMDB_id):
		self.IMDB_id = IMDB_id
		self.sql_select_shows = ""
		self.table_column_count = 5
		self.horizontal_header_labels = ["", "Episode ID", "Air Date", "Episode Title", ""]
		
	# Had to reimplement this function, because I couldn't change couple of settings of the table
	def create_table(self):

		self.table_model = QStandardItemModel()
		self.table_model.setColumnCount(self.table_column_count)
		self.table_model.setHorizontalHeaderLabels(self.horizontal_header_labels)
		self.table_model.sort(1, Qt.AscendingOrder)
		
		self.fill_episode_table()

		self.episode_table = QTableView()
		self.episode_table.setModel(self.table_model)
		self.episode_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents) # Adjust how much space table takes
		self.episode_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Makes table not editable
		self.episode_table.setSelectionBehavior(QAbstractItemView.SelectRows) # Clicking on cell selects row
		self.episode_table.verticalHeader().setVisible(False) # Removing vertincal headers for rows (removing numbering)
		self.episode_table.setSelectionMode(QAbstractItemView.NoSelection) # Makes not able to select cells or rows in table
		self.episode_table.sortByColumn(1, Qt.AscendingOrder) # Sorts table in ascending order by seasonal ID
		self.episode_table.hideColumn(5) # Hidding last calumn that holds episode_IMDB_id value	
		# self.episode_table.setShowGrid(False) # Removes grid
		### Setting custom widths for some columns ###
		self.episode_table.setColumnWidth(0, 30)
		self.episode_table.setColumnWidth(1, 100)
		self.episode_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
	
		self.episode_table.clicked.connect(self.mark_episode) # Detects clicks on the table

	def fill_episode_table(self):
		# This function fills episode table using query provided in self.sql_select_shows.

		row_count = 0
		episodes = QSqlQuery(self.sql_select_shows)

		while episodes.next():

			self.insert_table_row(row_count, episodes, self.IMDB_id)
			row_count += 1
	
	def insert_table_row(self, row_count, episode, IMDB_id):

		# Adding row to the table
		self.table_model.insertRow(row_count)
		# Getting value of shows episode_watched cell
		episode_state = episode.value("episode_watched")
		# Setting checkbox to checked or unchecked depending on episode beeing watched or not

		show_watched = QStandardItem()
		# Making Checkbox not editable
		show_watched.setFlags(Qt.ItemIsEditable)

		# Setting background color for current row, checkbox's checkmark and setting "mark_watched" button status depending if episode is watched or not.
		if episode_state == 1:
			show_watched.setCheckState(Qt.Checked)
			show_watched_color = QColor(200, 230, 255)
			mark_button = QStandardItem("Not Watched")
		else:
			show_watched.setCheckState(Qt.Unchecked)
			show_watched_color = QColor(200, 255, 170)
			mark_button = QStandardItem("Watched")

		# Setting background color to red if current_date is smaller than air_date of the episode.
		if episode.value("air_date") > self.current_year + "-" + self.current_month_day or episode.value("air_date") == None or len(episode.value("air_date")) < 8:

			show_watched_color = QColor(255, 170, 175)

		# Setting different values to different culumns of the row for the query result.
		self.table_model.setItem(row_count, 0, show_watched)
		self.table_model.item(row_count, 0).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 1, QStandardItem(episode.value("episode_seasonal_id")))
		self.table_model.item(row_count, 1).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 2, QStandardItem(episode.value("air_date")))
		self.table_model.item(row_count, 2).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 3, QStandardItem(episode.value("episode_title")))
		self.table_model.item(row_count, 3).setBackground(show_watched_color)
		self.table_model.setItem(row_count, 4, mark_button)
		self.table_model.item(row_count, 4).setTextAlignment(Qt.AlignCenter)
		self.table_model.setItem(row_count, 5, QStandardItem(episode.value("episode_IMDB_id")))

	def mark_episode(self, pos):	
		# Marks episode when clicked on button-cell.
		if pos.column() == 4:
			episode_button = self.table_model.item(pos.row(), pos.column()).text()
			episode_IMDB_id = self.table_model.item(pos.row(), 5).text()
			
			if episode_button == "Watched":
				episode_state = "1"
				button_text = "Not Watched"			
				checkbox_state = Qt.Checked
				episode_watched_color = QColor(200, 230, 255)
			else:
				episode_state = "0"
				button_text = "Watched"
				checkbox_state = Qt.Unchecked
				episode_watched_color = QColor(200, 255, 170)

			mark_episode = QSqlQuery("UPDATE %s SET episode_watched = %s WHERE episode_IMDB_id = '%s'" % (self.IMDB_id, episode_state, episode_IMDB_id))
			mark_episode.exec_()
			self.table_model.setData(pos, button_text) # Changes button's text.
			self.table_model.item(pos.row(), 0).setCheckState(checkbox_state) # Changes state of checkbox

			# Changes background color of the row.
			for n in range(4):
				self.table_model.item(pos.row(), n).setBackground(episode_watched_color)
				
	def refill_episode_table(self):
		self.table_model.setRowCount(0)
		self.fill_episode_table()


if __name__ == "__main__":
	app = QApplication(sys.argv)
	mainWindow = mainWindow()
	sys.exit(app.exec_())
