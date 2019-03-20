#! /usr/bin/python3

import os
import configparser # Will be used to store path to the file of the database.
import pathlib #  needed to get $HOME folder

from PyQt5.QtSql import QSqlDatabase, QSqlQuery

# Setting up config parser
config = configparser.ConfigParser()
# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")
# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

class DatabaseConnection():

	# Opening a database.
	database = QSqlDatabase().addDatabase("QSQLITE")
	database.setDatabaseName(config["DATABASE"]["Path"])
	database.open() 
	
	sql_create_show_table_if_do_not_exists = QSqlQuery("CREATE TABLE IF NOT EXISTS shows (IMDB_id TEXT NOT NULL PRIMARY KEY, title TEXT NOT NULL, image TEXT NOT NULL, synopsis TEXT NOT NULL, seasons INTEGER NOT NULL, genres TEXT NOT NULL, running_time INTEGER NOT NULL, finished_airing INTEGER NOT NULL, years_aired TEXT NOT NULL, finished_watching INTEGER NOT NULL, unknown_season INTEGER NOT NULL)")
	sql_create_show_table_if_do_not_exists.exec_()
