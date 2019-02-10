#!/usr/bin/python3

# Importing Python3 dependencies
import sqlite3
import sys
import os
import pathlib #  needed to get $HOME folder
import textwrap # Wraps text to make it more presentable
import datetime # Used to compare the dates of the episode against the current date.
import configparser # Will be used to store path to the file of the database.

# Importing other programs modules writen by me.
from template import Templates
import IMDB_id_validation as validate

# Setting up config parser
config = configparser.ConfigParser()

# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")

# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

# Connecting to the database
con = sqlite3.connect(config["DATABASE"]["Path"])
cur = con.cursor()

# Assingning names to the modules.
template = Templates()

class ShowDetails:

    def __init__(self):
        # Empty string to place IMDB_id of the show user plans to look at.
        self.current_IMDB_id = ""
        self.current_title = ""
        self.current_image = ""
        self.current_synopsis = ""
        self.current_full_seasons = "" # This variable contains ALL seasons in INTEGER
        self.current_all_seasons = "" # This variable contains seasons as INTEGET without None season
        self.unknown_season = "" # This valiable was introduced to make a decent way of adding and displayng unknown season episodes.
        self.current_running_time = ""
        self.current_finished_airing = ""
        self.current_genres = ""
        self.current_years_aired = ""
        self.current_finished_watching = ""
        self.current_episodes_watched = ""

    # This function was created to fix a problem were after updating show seasons "None" season wasn't shown in printed list because function used not updated variable.
    def generate_self_variables(self):
        
        cur.execute("SELECT * FROM shows WHERE IMDB_id = '%s'" % self.current_IMDB_id)
        show_info = cur.fetchone()

        self.current_title = show_info[1]
        self.current_image = show_info[2]
        self.current_synopsis = show_info[3]
        self.current_full_seasons = show_info[4]
        self.current_genres = show_info[5]
        self.current_running_time = show_info[6]
        self.current_finished_airing = show_info[7]
        self.current_years_aired = show_info[8]
        self.current_finished_watching = show_info[9]

        cur.execute("SELECT DISTINCT season FROM %s" % self.current_IMDB_id)
        self.current_all_seasons = cur.fetchall()
        
        # Getting count of how many episodes are actually marked as watched.
        cur.execute("SELECT COUNT(*) FROM %s WHERE episode_watched = 1" % self.current_IMDB_id)
        self.current_episodes_watched = cur.fetchone()

        if len(self.current_all_seasons) > self.current_full_seasons:
            self.unknown_season = 1


    def latest_episodes(self):
        # Variable containing currrent date and year.
        current_date = datetime.datetime.today().strftime("%Y-%m-%d") 

        print(template.show_info.format("Latest aired episodes"))
        print(template.seperator)
        print(template.latest_next_episode_table_header.format("Watched", "Title", "Episode #", "Air Date", "Episode Title"))
        print(template.seperator)
        
        # Getting IMDB_id of shows, that are in Watchlist.
        cur.execute("SELECT IMDB_id FROM shows WHERE finished_watching = 0")
        shows_to_scan = cur.fetchall()
        
        for show in shows_to_scan:
        
            cur.execute("SELECT title FROM shows WHERE IMDB_id = '%s'" % show[0])    
            current_watchlist_show_title = cur.fetchone()[0]

            cur.execute("SELECT * FROM %s WHERE LENGTH(air_date) > 4 AND air_date < '%s' ORDER BY air_date DESC" % (show[0], current_date))
            latest_episode_row = cur.fetchone()
            if latest_episode_row != None:
                print(self.add_colors_to_row_latest_next(latest_episode_row, current_watchlist_show_title))

        print(template.seperator)
        print(template.seperator)

    # Function to print next airing episodes from Watchlist.
    def next_episodes(self):
        # Variable containing currrent date and year.
        current_date = datetime.datetime.today().strftime("%Y-%m-%d") 

        print(template.show_info.format("Next Episodes"))
        print(template.seperator)
        print(template.latest_next_episode_table_header.format("Watched", "Title", "Episode #", "Air Date", "Episode Title"))
        
        # Getting IMDB_id of shows, that are in Watchlist.
        cur.execute("SELECT IMDB_id FROM shows WHERE finished_watching = 0")
        shows_to_scan = cur.fetchall()
        
        # Goes though every episode of the Watchlist and finds episode that is next by comparing air_date to current date and selecting the closiest bigest ep.
        for show in shows_to_scan:
        
            cur.execute("SELECT title FROM shows WHERE IMDB_id = '%s'" % show[0])    
            current_watchlist_show_title = cur.fetchone()[0]

            cur.execute("SELECT * FROM %s WHERE LENGTH(air_date) > 4 AND air_date > '%s' ORDER BY air_date ASC" % (show[0], current_date))
            latest_episode_row = cur.fetchone()
            if latest_episode_row != None:
                print(self.add_colors_to_row_latest_next(latest_episode_row, current_watchlist_show_title))
        print(template.seperator)
        print(template.seperator)

    # Search function to search in titles of the shows of shows table.
    # If function finds a single match it will return the IMDB_id
    # If function finds multiple matches it will print a table to choose from and then will return IMDB_id to main function. At thus point user can chose to exit the search.
    # If search returns 0 results function return False.
    def search_show_title(self, search_string):

        # Selecting everything that matched in the database's shows table's title column.
        cur.execute("SELECT * FROM shows WHERE title like '%%%s%%'" % search_string)
        found_shows = cur.fetchall()
        # Returning IMDB_id if only one show was found.
        if len(found_shows) == 1:
            
            return found_shows[0][0]

        # If more than one show was found printing a table contianing them and letting user choose from one of them then returning the table. User can choose to quit search when he is promted to choose from one of the shows.
        elif len(found_shows) > 1:
            
            print(template.tracked_shows.format("IMDB ID", "Title", "Show Status", "Synopsis"))
            print(template.seperator)
            print(template.seperator)
            
            for show in found_shows:
                
                # Printing all shows that were found in database.
                IMDB_id = show[0]
                title = textwrap.shorten(show[1], width=20)
                synopsis = textwrap.shorten(show[3], width=50)
                if show[7] == 1:
                    finished_airing = "Still airing"
                else:
                    finished_airing = "Finished airing"
                print(template.tracked_shows.format(IMDB_id, title, finished_airing, synopsis))
                print(template.seperator)

            print(template.text.format("Please select a show or press 0 to go to main menu."))
            chosen_show = input()

            if chosen_show == "0":

                return 0

            elif validate.check_if_input_contains_IMDB_id(chosen_show) and validate.title_exists_in_database:

                
                return validate.check_if_input_contains_IMDB_id(chosen_show)

                # self.show_info()
                # return self.current_IMDB_id()

        # Returning False if nothing was found.
        else:
            return False

    # Changes color of the line depending if episode already watched/aired. LATEST EPISODE and NEXT EPISODE table.
    def add_colors_to_row_latest_next(self, row, current_title):
        # lambda for printing checkmark if episode watched.
        checkmark = lambda x: u'\u2713' if x == 1 else ""
        current_date = datetime.datetime.today()
        # Not all episodes that are in the future has all the information. This if statement is to fix one of these tipe of problems.
        if row[7] == None:
            return(template.latest_next_episodes_unaired.format(checkmark(row[0]), textwrap.shorten(current_title, 30), row[4], "", textwrap.shorten(row[6], 40)))
        elif len(row[7]) < 8:
            # Marks line red if date is less than 5 digits. It means that imdb doesn't know exact date when the show aired and wrote just the year. It also shortens episode title text if it exeeds 40 charcters.
            return(template.latest_next_episodes_unaired.format(checkmark(row[0]), textwrap.shorten(current_title, 30), row[4], row[7], textwrap.shorten(row[6], 40)))
        elif datetime.datetime.strptime(row[7], '%Y-%m-%d') > current_date:
            # Marks line red if date that episode aired is the future.
            return(template.latest_next_episodes_unaired.format(checkmark(row[0]), textwrap.shorten(current_title, 30), row[4], row[7], textwrap.shorten(row[6], 40)))
        elif datetime.datetime.strptime(row[7], '%Y-%m-%d') < current_date:
            if row[0] == 1:
                    # Marks line green if colum episode_watched has 1. Meaning that episode is marked as seen.
                    return(template.latest_next_episodes_seen.format(checkmark(row[0]), textwrap.shorten(current_title, 30), row[4], row[7], textwrap.shorten(row[6], 40)))
            else:
                    # Marks every other line blue, because apisode is available to watch, but wasn't.
                    return(template.latest_next_episodes_unseen.format(checkmark(row[0]), textwrap.shorten(current_title, 30), row[4], row[7], textwrap.shorten(row[6], 40)))

    # Prints shows from the database. Have to provide variable (int) as finished_watching. 0 means currently watching (Watchlist), 1 - Finished watching and 2 - Plan to Watch. There is a 4th variable - 4. It will print contents of the table.
    def tracked_shows(self, finished_watching):
        # Setting initial table
        print(template.seperator)
        print(template.tracked_shows.format("IMDB ID", "Title", "Show Status", "Synopsis"))
        print(template.seperator)
        print(template.seperator)
        
        if finished_watching == 4:
            for row in cur.execute("SELECT * FROM shows"):
                IMDB_id = row[0]
                title = textwrap.shorten(row[1], width=20)
                synopsis = textwrap.shorten(row[3], width=50)
                if row[7] == 1:
                    finished_airing = "Still airing"
                else:
                    finished_airing = "Finished airing"
                print(template.tracked_shows.format(IMDB_id, title, finished_airing, synopsis))
                print(template.seperator)
        else:
            for row in cur.execute("SELECT * FROM shows WHERE finished_watching = %d" % finished_watching):
                IMDB_id = row[0]
                title = textwrap.shorten(row[1], width=20)
                synopsis = textwrap.shorten(row[3], width=50)
                if row[7] == 1:
                    finished_airing = "Still airing"
                else:
                    finished_airing = "Finished airing"
                print(template.tracked_shows.format(IMDB_id, title, finished_airing, synopsis))
                print(template.seperator)
    
        print(template.seperator)
    
    # Printing information about the show thats was chosen.
    def show_info(self):

        # Lambda for printing airing / finsihed airing message
        airing_or_finished = lambda x: "Still airing" if x == 1 else "Finished Airing"
        # Lambda for printing info if there is a extra "Unknown" season
        unknown_season_exists = lambda x: " + 'Unknow' season" if x == 1 else ""

        self.generate_self_variables()

        current_watched_minutes = self.current_episodes_watched[0] * self.current_running_time
    
        print(template.empty.format(" "))
        print(template.seperator)
        print(template.show_info.format(self.current_title))
        print(template.show_info.format(self.current_years_aired + " (" + airing_or_finished(self.current_finished_airing) + ")" ))
        print(template.show_info.format("Genres: " + self.current_genres))
        print(template.show_info.format("Episode runtime: " + str(self.current_running_time) + " minutes"))
        print(template.show_info.format(str(self.current_full_seasons) + " season(s)" + unknown_season_exists(self.unknown_season)))
        print(template.show_info.format("You watched this show for %s minutes (%s hours/%s days)" % (str(current_watched_minutes), str(round(current_watched_minutes / 60)), str(round(current_watched_minutes/1440, 1)))))

        if self.current_finished_watching == 0:
            list_name = "Watchlist"
        elif self.current_finished_watching == 1:
            list_name = "Finished Watching"
        elif self.current_finished_watching == 2:
            list_name = "Plan to Watch"

        print(template.show_info.format("Currently in - %s - list" % list_name))
        if self.unknown_season == 1:
            print(template.empty.format("  "))
            print(template.seperator)
            print(template.show_info.format("This show also has unknown season, that might contain future/uneired/pilot episodes"))
            print(template.seperator)
        print(template.empty.format(" "))
        print(template.empty.format(textwrap.fill(self.current_synopsis, 100)))
        print(template.empty.format(" "))
        print(template.seperator)
        print(template.empty.format(" "))
    
    # Changes color of the line depending if episode already watched/aired
    def add_colors_to_row(self, row):
        # lambda for printing checkmark if episode watched.
        checkmark = lambda x: u'\u2713' if x == 1 else ""
        current_date = datetime.datetime.today()
        # Not all episodes that are in the future has all the information. This if statement is to fix one of these tipe of problems.
        if row[7] == None:
            return(template.episodes_unaired.format(checkmark(row[0]), row[4], row[3], "", textwrap.shorten(row[6], 40)))
        elif len(row[7]) < 8:
            # Marks line red if date is less than 5 digits. It means that imdb doesn't know exact date when the show aired and wrote just the year. It also shortens episode title text if it exeeds 40 charcters.
            return(template.episodes_unaired.format(checkmark(row[0]), row[4], row[3], row[7], textwrap.shorten(row[6], 40)))
        elif datetime.datetime.strptime(row[7], '%Y-%m-%d') > current_date:
            # Marks line red if date that episode aired is the future.
            return(template.episodes_unaired.format(checkmark(row[0]), row[4], row[3], row[7], textwrap.shorten(row[6], 40)))
        elif datetime.datetime.strptime(row[7], '%Y-%m-%d') < current_date:
            if row[0] == 1:
                    # Marks line green if colum episode_watched has 1. Meaning that episode is marked as seen.
                    return(template.episodes_seen.format(checkmark(row[0]), row[4], row[3], row[7], textwrap.shorten(row[6], 40)))
            else:
                    # Marks every other line blue, because apisode is available to watch, but wasn't.
                    return(template.episodes_unseen.format(checkmark(row[0]), row[4], row[3], row[7], textwrap.shorten(row[6], 40)))
    
    # Prints all seasons of the show. Prints unknows season at the end of the list.
    def print_show_eps(self):
        print(template.seperator)
        print(template.episode_table_header.format("Watched", "Episode Number", "IMDB_id", "Air Date", "Episode Title"))
        print(template.seperator)
        for season in range(1, self.current_full_seasons + 1):
            print(template.show_info.format("Season " + str(season)))
            print(template.seperator)
            for row in cur.execute("SELECT * FROM %s WHERE season = %d ORDER BY episode_seasonal_id ASC" % (self.current_IMDB_id, season)):
                print(self.add_colors_to_row(row))
            print(template.seperator)
        if self.unknown_season == 1:
            print(template.show_info.format("Unknown"))
            print(template.seperator)
            for row in cur.execute("SELECT * FROM %s WHERE season = '%s'" % (self.current_IMDB_id, '')):
                print(self.add_colors_to_row(row))
        print(template.empty.format(" "))
        print(template.seperator)

    # Askes user to choose from one of the available seasons of the show. input() function has to be in a different function. This function is just to print the season numbers.
    def choose_single_season(self):
        print(template.request_response.format("Choose the season to print (1-%s)" % self.current_full_seasons))
        # Offers to print unknown season if it exists.
        if self.unknown_season == 1:
            print(template.request_response.format("There is a 'Unknown' seasons. If you want to select it - type 0"))

    # Prints season from user input.
    def print_single_season(self):
        season_to_print = input()
        print(template.seperator)
        print(template.episode_table_header.format("Watched", "Episode Number", "Air Date", "Episode Title"))
        if season_to_print == '0':
            for row in cur.execute("SELECT * FROM %s WHERE season = '%s' ORDER BY episode_seasonal_id ASC" % (self.current_IMDB_id, '')):
                print(self.add_colors_to_row(row))
        else:
            for row in cur.execute("SELECT * FROM %s WHERE season = '%s' ORDER BY episode_seasonal_id ASC" % (self.current_IMDB_id, season_to_print)):
                print(self.add_colors_to_row(row))
        print(template.empty.format(" "))
        print(template.seperator)
