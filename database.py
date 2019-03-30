#! /usr/bin/python3

from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSettings

settings = QSettings("SeriesTracker", "SeriesTracker")

class DatabaseConnection():
	
	def check(self):
	# Checks if there is a path to database. If not it will ask user to choose one.
		if settings.value("DB_path") == None:
			db_path = QFileDialog().getExistingDirectory(self, "Select database location")
			f_db_path = db_path + "/shows.db"
			settings.setValue("DB_path", f_db_path)
	
	def connect():
		# Opening a database.
		database = QSqlDatabase().addDatabase("QSQLITE")
		database.setDatabaseName(settings.value("DB_path"))
		database.open() 
		
		sql_create_show_table_if_do_not_exists = QSqlQuery("CREATE TABLE IF NOT EXISTS shows (IMDB_id TEXT NOT NULL PRIMARY KEY, title TEXT NOT NULL, image TEXT NOT NULL, synopsis TEXT NOT NULL, seasons INTEGER NOT NULL, genres TEXT NOT NULL, running_time INTEGER NOT NULL, finished_airing INTEGER NOT NULL, years_aired TEXT NOT NULL, finished_watching INTEGER NOT NULL, unknown_season INTEGER NOT NULL)")
		sql_create_show_table_if_do_not_exists.exec_()
