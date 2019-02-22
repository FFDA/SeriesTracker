#! /usr/bin/python3

from PyQt5.QtCore import Qt, QCoreApplication, QSortFilterProxyModel
import PyQt5.QtSql as QtSql
from PyQt5.QtWidgets import *
import sys
from PyQt5.QtGui import *
import datetime
import sqlite3
import os
from functools import partial

import pathlib #  needed to get $HOME folder
import configparser # Will be used to store path to the file of the database.

# Setting up config parser
config = configparser.ConfigParser()

# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")

# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

class mainWindow(QMainWindow):

    # Opening a database.
    database = QtSql.QSqlDatabase().addDatabase("QSQLITE")
    database.setDatabaseName(config["DATABASE"]["Path"])
    database.open()

    def __init__(self):
        super().__init__()

        self.top = 200
        self.left = 500
        self.height = 700
        self.width = 1000
        self.initUI()

    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
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
        self.tab3 = QWidget()
#         self.tab4 = QWidget()

        # Adding tabs to the tabs (QTabWidget) widget and setttig names for it.
        self.tabs.addTab(self.tab1, "Recent Episodes")
        self.tabs.addTab(self.tab2, "Shows")
#         self.tabs.addTab(self.tab3, "Plan To Watch")
#         self.tabs.addTab(self.tab4, "Finished Watching")
        
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
        latest_episodes = CreateEpisodeTables()
        latest_episodes.label_text = "Latest Episodes"
        latest_episodes.sql_select_shows = "SELECT * FROM shows WHERE finished_watching = 0"
        latest_episodes.sql_filter_episodes = "SELECT * FROM %s WHERE LENGTH(air_date) > 4 AND air_date < '%s' ORDER BY air_date ASC"
        latest_episodes.create_label()
        latest_episodes.create_table()
        latest_episodes.fill_episode_table()

        
        # Setting up Next Episodes table
        next_episodes = CreateEpisodeTables()
        next_episodes.label_text = "Upcoming Episodes"
        next_episodes.sql_select_shows = "SELECT * FROM shows WHERE finished_watching = 0"
        next_episodes.sql_filter_episodes = "SELECT * FROM %s WHERE LENGTH(air_date) > 4 AND air_date > '%s' ORDER BY air_date DESC"
        next_episodes.create_label()
        next_episodes.create_table()
        next_episodes.fill_episode_table()
        
        # Adding label to the tab1 layout
        self.tab1.layout.addWidget(latest_episodes.episode_table_label)
        # Adding table to the tab1 layout
        self.tab1.layout.addWidget(latest_episodes.episode_table)
        self.tab1.layout.addWidget(next_episodes.episode_table_label)
        self.tab1.layout.addWidget(next_episodes.episode_table)
        # Adding setting tab1 laytout
        self.tab1.setLayout(self.tab1.layout)


    def tab2UI(self):

        # Setting tab2 laytout to vertival
        self.tab2.layout = QVBoxLayout()

        shows_table = CreateShowTables()

        shows_table.create_buttons()
        shows_table.create_table()
        shows_table.create_filter_box()
        shows_table.fill_table()

        self.tab2.layout.addWidget(shows_table.button_box)
        self.tab2.layout.addWidget(shows_table.filter_box)
        self.tab2.layout.addWidget(shows_table.shows_table)
        self.tab2.setLayout(self.tab2.layout)

class CreateEpisodeTables:

    # Variable with current date for to compare episode's air_date later
    current_year = datetime.datetime.today().strftime("%Y")
    current_month_day = datetime.datetime.today().strftime("%m-%d")
    
    def __init__(self):
        self.sql_select_shows = ""
        self.label_text = ""
        self.table_column_count = 6
        self.table_horizontal_header_labels = ["", "Title", "Episode", "Airdate", "Episode Title", ""]
        self.sql_filter_episodes = ""
    
    def create_label(self):
        # Adding label
        self.episode_table_label = QLabel(self.label_text)
        self.episode_table_label.setMargin(5)
        # Setting alighment of the label
        self.episode_table_label.setAlignment(Qt.AlignHCenter)

    def create_table(self):
        # Initiating Table
        self.episode_table = QTableWidget()
        # Removing vertincal headers for rows (removing numbering)
        self.episode_table.verticalHeader().setVisible(False)
        # Making tables to fit to the window
        self.episode_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        # Uncomment line bellow to select rows instead of single cells
        # self.episode_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Uncomment line bellow to select nothing
        self.episode_table.setSelectionMode(QAbstractItemView.NoSelection)
        # Making table not editable
        self.episode_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # lastEpisodes.setShowGrid(False)
        # Setting 6 columns for the table
        self.episode_table.setColumnCount(self.table_column_count)
        # Setting lables for the columns 
        self.episode_table.setHorizontalHeaderLabels(self.table_horizontal_header_labels)
        # Setting different widths for different columns
        self.episode_table.setColumnWidth(0, 30)
        self.episode_table.setColumnWidth(1, 340)
        self.episode_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

    # Marks episode as watched and repopulates table with updated data.
    def mark_watched(self, IMDB_id, episode_IMDB_id):
        mark_episode = QtSql.QSqlQuery("UPDATE %s SET episode_watched = 1 WHERE episode_IMDB_id = '%s'" % (IMDB_id, episode_IMDB_id))
        mark_episode.exec_()
        self.episode_table.setRowCount(0)
        self.fill_episode_table()

    # Retrieves shows IMDB_id on which was clicked.
    def selected_show(self, row, col):
        show = QtSql.QSqlQuery("SELECT IMDB_id FROM shows WHERE title = '%s'" % self.episode_table.item(row, 1).text())
        show.first()
        print(show.value(0))

    def fill_episode_table(self):
        # Setting variable to 0 because row count is unknown
        rowCount = 0

        # Selecting using provided query
        selected = QtSql.QSqlQuery(self.sql_select_shows)

        # print(len(selected.result()))
        
        # Iterating thought every quary result
        while selected.next():
            
            # Selecting all episodes from show in the watchlist that has air_date longer than 4 digists and which has air_date beforte current date. Ordering results in descending order.
            episode = QtSql.QSqlQuery(self.sql_filter_episodes % (selected.value("IMDB_id"), self.current_year + "-" + self.current_month_day))
            # Selecting first result in query.
            if episode.last() == False:
                pass
            else:
                # Adding row to the table
                self.episode_table.insertRow(rowCount)
                # Getting value of shows episode_watched cell
                episode_state = episode.value("episode_watched")
                # Setting checkbox to checked or unchecked depending on episode beeing watched or not
                mark_watched_button = QPushButton("Watched")
                mark_watched_button.setFlat(True)
    
                show_watched = QTableWidgetItem()
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
                if episode.value("air_date") > self.current_year + "-" + self.current_month_day:
                    show_watched_color = QColor(255, 170, 175)
    
                # Setting different values to different culumns of the row for the query result.
                self.episode_table.setItem(rowCount, 0, show_watched)
                self.episode_table.item(rowCount, 0).setBackground(show_watched_color)
                self.episode_table.setItem(rowCount, 1, QTableWidgetItem(selected.value("title")))
                self.episode_table.item(rowCount, 1).setBackground(show_watched_color)
                self.episode_table.setItem(rowCount, 2, QTableWidgetItem(episode.value("episode_seasonal_id")))
                self.episode_table.item(rowCount, 2).setBackground(show_watched_color)
                self.episode_table.setItem(rowCount, 3, QTableWidgetItem(episode.value("air_date")))
                self.episode_table.item(rowCount, 3).setBackground(show_watched_color)
                self.episode_table.setItem(rowCount, 4, QTableWidgetItem(episode.value("episode_title")))
                self.episode_table.item(rowCount, 4).setBackground(show_watched_color)
                self.episode_table.setCellWidget(rowCount, 5, mark_watched_button)
                mark_watched_button.clicked.connect(partial(self.mark_watched, selected.value("IMDB_id"), episode.value("episode_IMDB_id")))
    
                # Adding +1 to the row count
                rowCount += 1


        self.episode_table.cellClicked.connect(self.selected_show)

class CreateShowTables:

    def __init__(self):
        # self.table_label_text = "All Shows"
        self.horizontal_header_labels = ["Title", "Seasons", "Status", "Years aired", "Synopsis"]
        self.sql_query = "SELECT * FROM shows"
    
    def create_buttons(self):

        # Innitiating box for buttons and adding layout for it.
        self.button_box = QGroupBox()
        self.button_box.layout = QHBoxLayout()

        btn_all_shows = QPushButton("All Shows")
        btn_watchlist = QPushButton("Watchlist")
        btn_finished_watching = QPushButton("Finished Watching") 
        btn_plan_to_watch = QPushButton("Plan to Watch")

        # Making buttons checkable to make them look differently, and to make them work exclusively
        btn_all_shows.setCheckable(True)
        btn_watchlist.setCheckable(True)
        btn_finished_watching.setCheckable(True)
        btn_plan_to_watch.setCheckable(True)

        # Setting default button
        btn_all_shows.setChecked(True)

        # Set buttons to work exclusively 
        btn_all_shows.setAutoExclusive(True)
        btn_watchlist.setAutoExclusive(True)
        btn_finished_watching.setAutoExclusive(True)
        btn_plan_to_watch.setAutoExclusive(True)

        self.button_box.layout.addWidget(btn_all_shows)
        self.button_box.layout.addWidget(btn_watchlist)
        self.button_box.layout.addWidget(btn_finished_watching)
        self.button_box.layout.addWidget(btn_plan_to_watch)

        # Linking buttons with function and passing different sql_query
        btn_all_shows.clicked.connect(partial(self.refill_table, "SELECT * FROM shows"))
        btn_watchlist.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE finished_watching = 0"))
        btn_finished_watching.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE  finished_watching = 1"))
        btn_plan_to_watch.clicked.connect(partial(self.refill_table, "SELECT * FROM shows WHERE finished_watching = 2"))

        self.button_box.setLayout(self.button_box.layout)

    def create_filter_box(self):
        
        # Adding 
        self.filter_box = QLineEdit()
        self.filter_box.textChanged.connect(self.filter_model.setFilterRegExp)

    def create_table(self):

        # Making table model that has to be added to QTableView, but in this case it will be added as a source model for QSortFilterProxyModel to be able to filter results on the go.
        self.table_model = QStandardItemModel()
        self.table_model.setColumnCount(5)
        self.table_model.setHorizontalHeaderLabels(self.horizontal_header_labels)

        # This intermediate model allows to filter show table
        self.filter_model = QSortFilterProxyModel()
        self.filter_model.setSourceModel(self.table_model)
        self.filter_model.setFilterKeyColumn(0) # Setting target of the filter function
        self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # Making filter regex not case sensitive

        # TableView model that actually displays show table
        self.shows_table = QTableView()
        self.shows_table.setModel(self.filter_model)
        self.shows_table.verticalHeader().setVisible(False)
        self.shows_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.shows_table.setColumnWidth(0, 200)
        self.shows_table.setColumnWidth(2, 110)
        self.shows_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.shows_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

    def fill_table(self):
        
        row_count = 0

        selected = QtSql.QSqlQuery(self.sql_query)

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
            

            row_count += 1
        
    def refill_table(self, new_query):
        self.sql_query = new_query
        self.table_model.setRowCount(0)
        self.fill_table()
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = mainWindow()
    sys.exit(app.exec_())
