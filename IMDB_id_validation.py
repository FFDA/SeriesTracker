#!/usr/bin/python3

# This modude has functions that are used thougout all other files.

# Importing Python3 dependencies
import sqlite3
import re
import os
import pathlib #  needed to get $HOME folder
import configparser # Will be used to store path to the file of the database.

# Importing other programs modules writen by me.
from template import Templates

# Assingning names to the modules.
template = Templates()

# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")

# Setting up config parser
config = configparser.ConfigParser()

# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

# Connecting to the database
con = sqlite3.connect(config["DATABASE"]["Path"])
cur = con.cursor()

# Regex pattern that is used to detect IMDB_id.
pattern_to_look_for = re.compile("tt\d+")

# This fucntionf checks user input and returns False if does not contain IMDB_id or returns string with IMDB_id.
def check_if_input_contains_IMDB_id(user_input):
    if pattern_to_look_for.search(user_input):
        if len(pattern_to_look_for.search(user_input)[0]) == 9:
            return pattern_to_look_for.search(user_input)[0]
    else:
        return False


# Checking if show already exist in the database
def title_exists_in_database(IMDB_id):
    cur.execute("SELECT EXISTS (SELECT title FROM shows WHERE IMDB_id=?)", (IMDB_id,))
    check_if_show_exists = cur.fetchone()
    # If show exists user will be prompted with the message and program will finish.
    if check_if_show_exists[0] == 1:
        return True
    # Adding show that doesn't exists in the database.
    else:
        # self.ask_if_finished_watching()
        return False

# This quick funkction came out of frustration that I have to check IMDB_id to often with both functions.
def input_contains_IMDB_id_and_exists_in_database(user_input):
    if check_if_input_contains_IMDB_id(user_input):
        IMDB_id = check_if_input_contains_IMDB_id(user_input) 
        if title_exists_in_database(IMDB_id):
            return IMDB_id
    else:
        False

