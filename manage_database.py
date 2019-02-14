#!/usr/bin/python3

# This is the main program. From it all other modules will be access from now on.
# This file mainly contains menu options to access other parts of the program.

# Importing Python3 dependencies
import re
import sys
import os
import sqlite3
import pathlib #  needed to get $HOME folder
import configparser # Will be used to store path to the file of the database.

# Importing other programs modules writen by me.
from template import Templates
from add_show import AddShow 
from show_details import ShowDetails
import IMDB_id_validation as validate

# Assingning names to the modules.
template = Templates()
add_show = AddShow()
show_details = ShowDetails()

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

class ManageDatabase:

    def __init__(self):
        pass

    def mark_show_as_finished(self, chosen_show):
        cur.execute("UPDATE shows SET finished_watching = 1 WHERE IMDB_id = ?", (chosen_show,))
        con.commit()
        print(template.information.format("Show - %s - marked as 'Finished'" % chosen_show))

    def add_show_to_watchlist(self, chosen_show):
        cur.execute("UPDATE shows SET finished_watching = 0 WHERE IMDB_id = ?", (chosen_show,))
        con.commit()
        print(template.information.format("Show - %s - added to 'Watchlist'" % chosen_show))

    def mark_show_as_plan_to_watch(self, chosen_show):
        cur.execute("UPDATE shows SET finished_watching = 2 WHERE IMDB_id = ?", (chosen_show,))
        con.commit()
        print(template.information.format("Show - %s - marked as 'Plan to Watch'" % chosen_show))

    def delete_show(self, chosen_show):
        cur.execute("DELETE FROM shows WHERE IMDB_id = ?", (chosen_show,))
        cur.execute("DROP TABLE %s" % chosen_show)
        con.commit()

    def mark_next_episode_watched(self, current_IMDB_id):
        cur.execute("SELECT finished_watching FROM shows WHERE IMDB_id='%s'" % current_IMDB_id)
        still_watching = cur.fetchone()[0]
        if still_watching == 1:
            print(template.information.format("You already finished watching this show."))
            print(template.information.format("Returning to previous menu"))
        else:
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_watched = 0)" % current_IMDB_id)
            not_seen_episodes_exists = cur.fetchone()[0]
            if not_seen_episodes_exists == 0:
                print(template.information.format("You have seen all the episodes there are. Are you sure this show is still running?"))
                template.empty.format(" ")
                print(template.seperator)
            else:
                cur.execute("SELECT episode_seasonal_id FROM %s WHERE episode_watched = 0" % current_IMDB_id)
                next_unwatched_episode = cur.fetchone()[0]
                cur.execute("UPDATE %s SET episode_watched = 1 WHERE episode_seasonal_id = '%s'" % (current_IMDB_id, next_unwatched_episode))
                con.commit()
                print(template.information.format("Marked episode %s as watched" % next_unwatched_episode))
                template.empty.format(" ")
                print(template.seperator)

    def mark_episode_as_watched(self, current_IMDB_id):
        print(template.request_response.format("Type episodes id (sXXeXX), season and episode number (XXX) or episode IMDB id."))
        chosen_episode = input()
        
        # Checking if user input is an IMDB_id. If it is - marks episode based on this id.
        if validate.check_if_input_contains_IMDB_id(chosen_episode):
            episode_IMDB_id = validate.check_if_input_contains_IMDB_id(chosen_episode)
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_IMDB_id = '%s')" % (current_IMDB_id, episode_IMDB_id))
            # Checking if episode exists.
            if cur.fetchone()[0] == 1:
                cur.execute("UPDATE %s SET episode_watched = 1 WHERE episode_IMDB_id = '%s'" % (current_IMDB_id, episode_IMDB_id))
                con.commit()
            # Printing error if episode doesn't exist.
            else:
                print("There is no episode with id %s" % episode_IMDB_id)

        # If user input is not IMDB_id it functions tries to operate as user provided a episode_seasonal_id
        else:

            if len(chosen_episode) == 2:
                episode_to_mark = "S0" + chosen_episode[0] + "E0" + chosen_episode[1:]
            elif len(chosen_episode) == 3:
                episode_to_mark = "S0" + chosen_episode[0] + "E" + chosen_episode[1:]
            elif len(chosen_episode) == 4:
                episode_to_mark = "S" + chosen_episode[:2] + "E" + chosen_episode[2:]
            elif len(chosen_episode) == 6:
                episode_to_mark = chosen_episode.upper()
            else:
                print("I'm not familiar with this type of episode: " + chosen_episode)
                template.empty.format(" ")
                print(template.seperator)
    
            # Cheking if episode really exists in the in the show's table.
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_seasonal_id = '%s')" % (current_IMDB_id, episode_to_mark))
            # If episode exists markig it as watched.
            if cur.fetchone()[0] == 1:
                cur.execute("UPDATE %s SET episode_watched = 1 WHERE episode_seasonal_id = '%s'" % (current_IMDB_id, episode_to_mark))
                con.commit()
            # Printing error message if show doesn't exists.
            else:
                print(template.information.format("%s episode do not exist." % episode_to_mark))
            template.empty.format(" ")
            print(template.seperator)

    def mark_up_to_episode(self, current_IMDB_id):
        print(template.request_response.format("Type episodes id (sXXeXX) or season and episode number (XXX)."))
        chosen_episode = input()
        if len(chosen_episode) == 2:
            episode_to_mark = "S0" + chosen_episode[0] + "E0" + chosen_episode[1:]
        elif len(chosen_episode) == 3:
            episode_to_mark = "S0" + chosen_episode[0] + "E" + chosen_episode[1:]
        elif len(chosen_episode) == 4:
            episode_to_mark = "S" + chosen_episode[:2] + "E" + chosen_episode[2:]
        elif len(chosen_episode) == 6:
            episode_to_mark = chosen_episode.upper()
        else:
            print("I'm not familiar with this type of episode: " + chosen_episode)
            template.empty.format(" ")
            print(template.seperator)

        # Cheking if episode really exists in the in the show's table.
        cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_seasonal_id = '%s')" % (current_IMDB_id, episode_to_mark))
        # If episode exists markig it as watched.
        if cur.fetchone()[0] == 1:
            cur.execute("UPDATE %s SET episode_watched = 1 WHERE episode_seasonal_id <= '%s' AND episode != ''" % (current_IMDB_id, episode_to_mark))
            con.commit()
        # Printing error message if show doesn't exists.
        else:
            print(template.information.format("%s episode do not exist." % episode_to_mark))
        template.empty.format(" ")
        print(template.seperator)

    def mark_season_as_watched(self, current_IMDB_id, chosen_season):
        # Printing available seasons to choose from
        show_details.current_IMDB_id = current_IMDB_id
        template.empty.format(" ")

        # Setting season to empty if user chose "None" season.
        if chosen_season == 0:
            chosen_season = ""

        # Checking if there are apisodes that are marked as not seen.
        cur.execute("SELECT EXISTS (SELECT * FROM '%s' WHERE season = '%s' AND episode_watched = 0)" % (current_IMDB_id, chosen_season))
        not_seen_episodes_exists = cur.fetchone()[0]
        # Marking episodes as seen
        if not_seen_episodes_exists == 1:
            print(template.information.format("Marking season %s as watched" % chosen_season))
            cur.execute("UPDATE %s SET episode_watched = 1 WHERE season = '%s'" % (current_IMDB_id, chosen_season))
            con.commit()
            print(template.information.format("All episodes in season %s marked as watched" % chosen_season)) 
        # Notifing User that all episodes in chosen season are marked as seen.
        else:
            print(template.information.format("All episdes in season %s are already marked as seen" % chosen_season))

        template.empty.format(" ")
        print(template.seperator)

    # Marks season as not watched.
    def mark_season_as_not_watched(self, current_IMDB_id, chosen_season):
        # Printing available seasons to choose from
        template.empty.format(" ")
        
        # Setting season to empty if user chose "None" season.
        if chosen_season == 0:
            chosen_season = ""

        # Checking if there are apisodes that are not seen.
        cur.execute("SELECT EXISTS (SELECT * FROM '%s' WHERE season = '%s' AND episode_watched = 1)" % (current_IMDB_id, chosen_season))
        seen_episodes_exists = cur.fetchone()[0]
        # Marking episodes as seen
        if seen_episodes_exists == 1:
            print(template.information.format("Marking season %s as watched" % chosen_season))
            cur.execute("UPDATE %s SET episode_watched = 0 WHERE season = '%s'" % (current_IMDB_id, chosen_season))
            con.commit()
            print(template.information.format("All episodes in season %s marked as not watched" % chosen_season)) 
        # Notifing User that all episodes in chosen season are marked as seen.
        else:
            print(template.information.format("All episdes in season %s are already marked as not seen" % chosen_season))

        template.empty.format(" ")
        print(template.seperator)

    def mark_episode_as_not_watched(self, current_IMDB_id):

        print(template.request_response.format("Type episodes id (sXXeXX), season and episode number (XXX) or episode IMDB id."))
        chosen_episode = input()
        
        # Checking if user input is an IMDB_id. If it is - marks episode based on this id.
        if validate.check_if_input_contains_IMDB_id(chosen_episode):
            episode_IMDB_id = validate.check_if_input_contains_IMDB_id(chosen_episode)
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_IMDB_id = '%s')" % (current_IMDB_id, episode_IMDB_id))
            if cur.fetchone()[0] == 1:
                cur.execute("UPDATE %s SET episode_watched = 0 WHERE episode_IMDB_id = '%s'" % (current_IMDB_id, episode_IMDB_id))
                con.commit()
            else:
                print("There is no episode with id %s" % episode_IMDB_id)

        # If user input is not IMDB_id it functions tries to operate as user provided a episode_seasonal_id
        else:
            chosen_episode = input()
            if len(chosen_episode) == 2:
                episode_to_mark = "S0" + chosen_episode[0] + "E0" + chosen_episode[1:]
            elif len(chosen_episode) == 3:
                episode_to_mark = "S0" + chosen_episode[0] + "E" + chosen_episode[1:]
            elif len(chosen_episode) == 4:
                episode_to_mark = "S" + chosen_episode[:2] + "E" + chosen_episode[2:]
            elif len(chosen_episode) == 6:
                episode_to_mark = chosen_episode.upper()
            else:
                print("I'm not familiar with this type of episode: " + chosen_episode)
                template.empty.format(" ")
                print(template.seperator)
    
            # Cheking if episode really exists in the in the show's table.
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE episode_seasonal_id = '%s')" % (current_IMDB_id, episode_to_mark))
            # If episode exists markig it as watched.
            if cur.fetchone()[0] == 1:
                cur.execute("UPDATE %s SET episode_watched = 0 WHERE episode_seasonal_id = '%s'" % (current_IMDB_id, episode_to_mark))
                con.commit()
            # Printing error message if show doesn't exists.
            else:
                print(template.information.format("%s episode do not exist." % episode_to_mark))
            template.empty.format(" ")
            print(template.seperator)
