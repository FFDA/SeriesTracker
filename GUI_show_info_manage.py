#! /usr/bin/python3

from imdbpie import Imdb
import IMDB_id_validation as validate
from GUI_misc import center

from PyQt5.QtWidgets import QDialog, QPushButton, QProgressBar, QComboBox, QLabel, QProgressBar, QGridLayout, QTextEdit
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtCore import Qt

class FixSeason(QDialog):
	
	def __init__(self, IMDB_id, seasons, unknown_season, title):
		super(FixSeason, self).__init__()
		self.IMDB_id = IMDB_id
		self.seasons = seasons
		self.unknown_season = unknown_season
		self.title = title
		self.imdb = Imdb()
		self.progress_minimum = 0
		self.progress_maximum = 1
		self.selected_season = ""
		
		self.initUI()
		
	def initUI(self):
		# All UI disign is in here.
		self.resize(800, 500)
		center(self)
		self.setModal(True)
		self.setWindowTitle("Choose season of %s to fix" % self.title)
		self.layout = QGridLayout()
		
		self.description_message = QLabel("Sometime seasons have multiple same episodes that differs in title or some other detail. It happens with shows that have 'Unknown' seasons. When IMDB currators add same episodes with different IMDB_ids. This function will try to fix it if you click 'Fix Season' button.")
		self.description_message.setWordWrap(True)
		
		self.message = QLabel("Please choose a season")
		self.message.setAlignment(Qt.AlignCenter)
		
		self.info_box = QTextEdit()
		self.info_box.setReadOnly(True)
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(0)
		self.progress_bar.setMaximum(8)
		
		self.button_cancel = QPushButton("Cancel")
		self.button_cancel.clicked.connect(self.reject)
		self.button_fix = QPushButton("Fix Season")
		self.button_fix.setDisabled(True)
		self.button_fix.clicked.connect(self.fix_season) 
		self.button_ok = QPushButton("OK")
		self.button_ok.setDisabled(True)
		self.button_ok.clicked.connect(self.accept)
		
		self.create_choose_season_combobox()
		
		self.layout.addWidget(self.season_button_label, 0, 1, 1, 1)
		self.layout.addWidget(self.season_button, 0, 2, 1, 1)
		self.layout.addWidget(self.description_message, 1, 0, 1, 4)
		self.layout.addWidget(self.message, 2, 0, 1, 4)
		self.layout.addWidget(self.info_box, 3, 0, 4, 4)
		self.layout.addWidget(self.progress_bar, 8, 0, 1, 4)
		self.layout.addWidget(self.button_cancel, 9, 0, 1, 1)
		self.layout.addWidget(self.button_fix, 9, 2, 1, 1)
		self.layout.addWidget(self.button_ok, 9, 3, 1, 1)
		self.setLayout(self.layout)
		self.show() 
		
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
		self.season_button.currentTextChanged.connect(self.setting_up_fix) # Detects if user chooses different season and sends value to print_season function
		self.season_button.setFocusPolicy(Qt.NoFocus)
		
		self.season_button_label = QLabel("Season")
		
	def setting_up_fix(self, selected_season):
		
		if selected_season == "":
			self.message.setText("Please select a season")
			self.button_fix.setDisabled(True) # Redisables "Update Season" button if user changes season selection to empty.
		else:
			self.message.setText("Season %s will be updated" % selected_season)
			self.button_fix.setDisabled(False) # Enables "Update Season" button for user to innitaite season update.
		
		self.selected_season = selected_season

	def create_progress_bar(self):
		# Simply creates progress bar.
		
		self.progress_bar = QProgressBar()
		self.progress_bar.setMinimum(self.progress_minimum)
		self.progress_bar.setMaximum(self.progress_maximum)

	def fix_season(self):
		
		progress_bar_value_count = 0
		something_was_removed_check = 0

		self.button_cancel.setDisabled(True)
		self.button_ok.setDisabled(True) # Setting OK button to be disabled just in case.
		
		self.info_box.append("Fixing {}'s Season {}".format(self.title, self.selected_season))
		
		# Because IMDB and my database uses different values for unknown season while retrieving it I have to assign two different values and use them accordingly.
		if self.selected_season == "Unknown":
			season_in_IMDB = int(self.seasons + self.unknown_season)
			season_in_database = ""
		else:
			season_in_IMDB = int(self.selected_season)
			season_in_database = int(self.selected_season)
			
		# Retrieving season that user want to fix episodes from IMDB.
		season_fix_imdb = self.imdb.get_title_episodes_detailed(self.IMDB_id, season_in_IMDB)
		
		list_of_season_fix_imdb = []

		for episode in season_fix_imdb["episodes"]:
			list_of_season_fix_imdb.append(validate.check_if_input_contains_IMDB_id(episode["id"]))
			
		self.progress_bar.setMaximum(len(list_of_season_fix_imdb))
		
		season_fix_db = QSqlQuery("SELECT episode_IMDB_id, episode_seasonal_id, episode_title FROM %s WHERE season == '%s'" % (self.IMDB_id, season_in_database))
		
		while season_fix_db.next():
		# Checks every IMDB_id fetched from IMDB against all IMDB retrieved from database.
		# If any of fetched IMDB_ids can't be found in database it will be removed from it. 
			try:
				list_of_season_fix_imdb.index(season_fix_db.value("episode_IMDB_id"))
				pass
			except ValueError:
				sql_delete_episode = QSqlQuery("DELETE FROM %s WHERE episode_IMDB_id='%s'" % (current_IMDB_id, season_fix_db.value("episode_IMDB_id")))
				sql_delete_epsidoe.exec_()
				self.info_box.append("Removed episode with IMDB ID: {episode_IMDB_id}, seasonal ID: {episode_seasonal_id} and title: {episode_title}".format(episode_IMDB_id = season_fix_db.value("episode_IMDB_id"), episode_seasonal_id = season_fix_db.value("episode_seasonal_id"), episode_title = season_fix_db.value("episode_title")))
				something_was_removed_check = 1 # Initiating a toggle that will not print a message that nothing was deleted.
			
			progress_bar_value_count += 1
			self.progress_bar.setValue(progress_bar_value_count)
		
		self.info_box.append("Finished fixing season %s" % self.selected_season)        
		
		if something_was_removed_check == 0:
			self.info_box.append("Nothing was removed")
		
		self.button_ok.setDisabled(False)
		self.change_season_button_index()

	def change_season_button_index(self):
		# This function exists, because I will be able to change season_button index after finishing updating season.
		# Previously it was at the end of update_season function, but it made to error out UpdateThreeSeason class.
	
		self.season_button.setCurrentIndex(0) # This sets season combo_box to option that doesn't have any value and it should disable "Update Season" button.
 
class ChangeList(QDialog):
	
	def __init__(self, IMDB_id, current_list, title):
		super(ChangeList, self).__init__()
		self.IMDB_id = IMDB_id
		self.current_list = current_list
		self.title = title
		self.initUI()
		
	def initUI(self):
		# All UI disign is in here.
		self.resize(400, 300)
		center(self)
		self.setModal(True)
		self.setWindowTitle("Change %s list" % self.title)
		self.layout = QGridLayout()
		
		self.description_message = QLabel("Select new list for %s" % self.title)
		self.description_message.setWordWrap(True)
		self.description_message.setAlignment(Qt.AlignCenter)
		
		self.combo_box_label = QLabel("Change to:")
		self.combo_box_list = ["Watchlist", "Finished Watching", "Plan to Watch"]
		self.combo_box = QComboBox()
		self.combo_box.addItems(self.combo_box_list)
		self.combo_box.setCurrentIndex(self.current_list) # Setting combo box index to make "Plan to Watch" as default option.
		self.combo_box.currentIndexChanged.connect(self.setupChange)
		self.combo_box.setFocusPolicy(Qt.NoFocus)
		
		self.message = QLabel("Select a different list")
		self.message.setAlignment(Qt.AlignCenter)
			
		self.button_cancel = QPushButton("Cancel")
		self.button_cancel.clicked.connect(self.reject)
		self.button_apply = QPushButton("Apply")
		self.button_apply.clicked.connect(self.change_list)
		self.button_apply.setDisabled(True)
		
		self.layout.addWidget(self.description_message, 0, 0, 1, 4)
		self.layout.addWidget(self.combo_box_label, 1, 1, 1, 1)
		self.layout.addWidget(self.combo_box, 1, 2, 1, 1)
		self.layout.addWidget(self.message, 2, 0, 1, 4)
		self.layout.addWidget(self.button_cancel, 3, 0, 1, 1)
		self.layout.addWidget(self.button_apply, 3, 3, 1, 1)
		self.setLayout(self.layout)
		self.show()
		
	def setupChange(self, index):
		# Displays different message depending on user's choosen list.
		# Enables/Disabled "apply" button depending if user chose a list that is not the current one.
		
		if index != self.current_list:
			self.message.setText("{show} list will be changed to {list_name}".format(show = self.title, list_name =  self.combo_box_list[index]))
			self.button_apply.setDisabled(False)
		else:
			self.message.setText("Select a different list")
			self.button_apply.setDisabled(True)
	
	def change_list(self):
		# Changes the list of the show and closes the window
		
		sql_change_list = QSqlQuery("UPDATE shows SET finished_watching = {list_index} WHERE IMDB_ID = '{IMDB_id}'".format(list_index = self.combo_box.currentIndex(), IMDB_id = self.IMDB_id))
		sql_change_list.exec_()
		
		self.accept()


class DeleteShow(QDialog):
	
	def __init__(self, IMDB_id, title):
		super(DeleteShow, self).__init__()
		self.IMDB_id = IMDB_id
		self.title = title
		
		self.initUI()
		
	def initUI(self):
		self.resize(400, 300)
		self.setModal(True)
		center(self)
		self.setWindowTitle("Delete %s" % self.title)
		self.layout = QGridLayout()
		
		self.message = QLabel("All data about %s will be deleted" % self.title)
		self.message.setWordWrap(True)
		self.message.setAlignment(Qt.AlignHCenter)
		
		self.button_cancel = QPushButton("Cancel")
		self.button_cancel.clicked.connect(self.reject)
		self.button_delete = QPushButton("Delete")
		self.button_delete.clicked.connect(self.delete_show)
		
		self.layout.addWidget(self.message, 0, 0, 1, 3)
		self.layout.addWidget(self.button_cancel, 2, 0, 1, 1)
		self.layout.addWidget(self.button_delete, 2, 2, 1, 1)
		
		self.setLayout(self.layout)	
		self.show()
		
	def delete_show(self):
		
		sql_delete_show_from_shows_table = QSqlQuery("DELETE FROM shows WHERE IMDB_id = '%s'" % self.IMDB_id)
		sql_delete_show_from_shows_table.exec_()
		
		sql_delete_show_table = QSqlQuery("DROP TABLE %s" % self.IMDB_id)
		sql_delete_show_table.exec_()
		self.accept()
