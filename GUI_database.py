#! /usr/bin/python3

import os
import configparser # Will be used to store path to the file of the database.
import pathlib #  needed to get $HOME folder

from PyQt5.QtSql import QSqlDatabase

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
