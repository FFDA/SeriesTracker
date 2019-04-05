#! /usr/bin/python3

#This file is resposible for creating Show Info window and all buttons for it.

# Python3 imports
import webbrowser
from urllib import request

# PyQt5 imports
from PyQt5.QtWidgets import QDialog, QMainWindow, QApplication, QVBoxLayout, QTabWidget, QLabel, QPushButton, QTableView, QAbstractScrollArea, QAbstractItemView, QHeaderView, QGroupBox, QHBoxLayout, QLineEdit, QGridLayout, QComboBox, QMenu, QDesktopWidget, QSizePolicy
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings, pyqtSignal, QObject, QSize

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
		
		self.episodes_table = CreateShowInfoEpisodeTable(self.IMDB_id) # Initiating episode table
		
		self.episodes_table.sql_select_shows = "SELECT * FROM %s" % self.IMDB_id
		self.episodes_table.create_table()	
		
		self.create_buttons()
		
		self.button_ok = QPushButton("OK")
		self.button_ok.clicked.connect(self.close)

		self.layout.addWidget(self.cover_box, 0, 0, 8, 2)
		self.layout.addWidget(self.show_info_box, 0, 2, 8, 10)
		self.layout.addWidget(self.button_box, 9, 0, 1, 12)
		self.layout.addWidget(self.episodes_table.episode_table, 10, 0, 8, 12)
		self.layout.addWidget(self.button_ok, 18, 11, 1, 1)
		self.setLayout(self.layout)
		
		self.show()
		
		self.episodes_table.episode_table.scrollToBottom() # Scrolls table to the bottom
		self.episodes_table.episode_marked.connect(self.refill_show_info)
	
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

		#self.show_info_box.layout.addWidget(image_box, 0, 0)
		self.show_info_box.layout.addWidget(info_box)
		self.show_info_box.setLayout(self.show_info_box.layout)
		
		self.fill_show_info_box()
		self.create_cover_box()
		
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
		
	def create_cover_box(self):
		# Creates cover box. And add poster if there is one downloaded. If not shows a button to download a poster.
		
		if QPixmap().load(settings.value("coverDir") + self.IMDB_id + ".jpg") == True:
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

		season_button = QComboBox()
		season_button.setMinimumSize(95, 31)
		season_button.setFocusPolicy(Qt.NoFocus)
		season_button.insertItems(0, season_list) # Adding all the options from season_list to the drop down menu
		season_button.currentTextChanged.connect(self.print_season) # Detects if user chooses different season and send value to print_season function
		
		season_button_label = QLabel("Season")

		# Button that opens show's IMDB page
		open_webpage = QPushButton("Open IMDB page")
		open_webpage.setFocusPolicy(Qt.NoFocus)
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
		
		if has_internet_connection() == False:
			CheckInternet("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
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

		self.episodes_table.refill_episode_table()

	def open_fix_season(self):
		
		if has_internet_connection() == False:
			CheckInternet("Please connect to internet").exec_() # This class is defined in misc.py
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
			CheckInternet("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_update_single_season_window = UpdateSingleSeason(self.IMDB_id, self.seasons, self.unknown_season, self.title)
			result = self.open_update_single_season_window.exec_()
			
			if result == QDialog.Accepted:
				self.episodes_table.refill_episode_table()
	
	def open_update_last_3_seasons(self):
		if has_internet_connection() == False:
			CheckInternet("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
			self.open_update_single_season_window = UpdateThreeSeasons(self.IMDB_id, self.seasons, self.unknown_season, self.title)
			result = self.open_update_single_season_window.exec_()
			
			if result == QDialog.Accepted:
				self.refill_episode_table()
			
	def open_update_show_info(self):
		if has_internet_connection() == False:
			CheckInternet("Please connect to internet").exec_() # This class is defined in misc.py
			return
		else:
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
	
	def open_delete_show(self):
		# This function will open a window to delete all the data from database.
		# After deletion it SHOULD close ShowInfo window too.
		self.open_delete_show_window = DeleteShow(self.IMDB_id, self.title)
		result = self.open_delete_show_window.exec_()
		
		if result == QDialog.Accepted:
			self.close() # SHOULD close the window
			
	def refill_show_info(self):
		self.fetch_show_info()
		self.fill_show_info_box()
		self.episodes_table.refill_episode_table()

		
class CreateShowInfoEpisodeTable(CreateShowEpisodeTable, QObject):
	# This class used to display episodes in ShowInfo window
	# CreateEpisodesTable class is in series_tracker.py
	
	episode_marked = pyqtSignal() # This is a signal that will be emited after episode is marked as watched.

	def __init__(self, IMDB_id):
		QObject.__init__(self) # I don't know whats the difference compared to super. I coppied that from pythoncentral.io
		self.IMDB_id = IMDB_id
		self.sql_select_shows = ""
		self.table_column_count = 5
		self.horizontal_header_labels = ["", "Episode ID", "Air Date", "Episode Title", ""]

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
			mark_button = QStandardItem("Watched")
			mark_button_color = QColor(160, 161, 162)
		else:
			show_watched.setCheckState(Qt.Unchecked)
			show_watched_color = QColor(200, 255, 170)
			mark_button = QStandardItem("Watched")
			mark_button_color = QColor(0, 0, 0)

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
		self.table_model.item(row_count, 4).setForeground(mark_button_color)
		self.table_model.setItem(row_count, 5, QStandardItem(episode.value("episode_IMDB_id")))

	def mark_episode(self, pos):	
		# Marks episode when clicked on button-cell.
		if pos.column() == 4:
			episode_button = self.table_model.item(pos.row(), pos.column()).text()
			episode_IMDB_id = self.table_model.item(pos.row(), 5).text()
			
			if episode_button == "Watched":
				episode_state = "1"
				#button_text = self.not_watched_button_text		
				checkbox_state = Qt.Checked
				episode_watched_color = QColor(200, 230, 255)
				mark_button_color = QColor(160, 161, 162)
			else:
				return

			mark_episode = QSqlQuery("UPDATE %s SET episode_watched = %s WHERE episode_IMDB_id = '%s'" % (self.IMDB_id, episode_state, episode_IMDB_id))
			mark_episode.exec_()
			#self.table_model.setData(pos, button_text) # Changes button's text.
			self.table_model.item(pos.row(), 4).setForeground(mark_button_color)
			self.table_model.item(pos.row(), 0).setCheckState(checkbox_state) # Changes state of checkbox

			# Changes background color of the row.
			for n in range(4):
				self.table_model.item(pos.row(), n).setBackground(episode_watched_color)

			self.episode_marked.emit()
