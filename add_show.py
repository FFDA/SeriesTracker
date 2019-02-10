#! /usr/bin/python3

# This is a module in episode tracker program that will add new TV series to database.

# Importing Python3 dependencies
from bs4 import BeautifulSoup
import urllib.request as urllib
from imdbpie import Imdb # This is the dependency that is written by someone else and my program is based on it. It download information in JSON files from IMDB.
import sqlite3
import re
import sys
import os
import pathlib #  needed to get $HOME folder
import configparser # Will be used to store path to the file of the database.

# Importing other programs modules writen by me.
import IMDB_id_validation as validate
from template import Templates

# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")

# Assingning names to the modules.
template = Templates()

# Setting up config parser
config = configparser.ConfigParser()

# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

# Connecting to the database
con = sqlite3.connect(config["DATABASE"]["Path"])
cur = con.cursor()

# Creating the database "shows" if it doesn't exist.
cur.execute('''CREATE TABLE IF NOT EXISTS shows
    (IMDB_id TEXT NOT NULL PRIMARY KEY, title TEXT NOT NULL, image TEXT NOT NULL, synopsis TEXT NOT NULL, seasons INTEGER NOT NULL, genres TEXT NOT NULL, running_time INTEGER NOT NULL, finished_airing INTEGER NOT NULL, years_aired TEXT NOT NULL, finished_watching INTEGER NOT NULL)''')

# Setting variable name for the imdbpie.
imdb = Imdb()


class AddShow:

    def __init__(self):
        self.IMDB_id = ""
        # Pattern for IMDB_id
        self.pattern_to_look_for = re.compile("tt\d+")
        self.finished_watching = ""
        self.show_seasons = ""

        # This labda should return just IMDB_id from given link
        self.get_IMDB_id_lambda = lambda x: self.pattern_to_look_for.search(x)[0]
    
    # Code to process one link or id.
    def validate_IMDB_id(self, IMDB_id_str):
        if validate.check_if_input_contains_IMDB_id(IMDB_id_str):
            self.IMDB_id = self.pattern_to_look_for.search(IMDB_id_str)[0]
            # Checks if IMDB_id actually represents a IMDB page.
            if imdb.title_exists(self.IMDB_id):
                self.title_exists_in_database()
            else:
                print(template.information.format("This show does not exist in IMDB!"))
        else:
            print(template.information.format("This is not valid IMDB id!"))

    # Checking if show already exist in the database
    def title_exists_in_database(self):
        if validate.title_exists_in_database(self.IMDB_id):
            print(template.information.format("This show - " + self.IMDB_id + " - is already in your library"))
        # Adding show that doesn't exists in the database.
        else:
            print(template.information.format("Will be adding the show"))
            self.add_show()

#     # THIS FUNCTION NO LONGER NEEDED. KEEPING JUST IN CASE.
#     # This fucntion asks User if he has finished watching the show. User will be prompted only if series have finneshed airing. It is determend by checking if IMDB page has two dates near shows name. Depending on User's response program will add 0 or 1 to finished_watching field. 0 means that user haven't finnished watching show, while 1 means he did.
#     def ask_if_finished_watching(self):
#         print(template.request_response.format("Have you finished watching the show? yes (y) / no (n)"))
#         ask1 = input()
#         if ask1.lower() == "yes" or ask1.lower() == "y":
#             self.finished_watching = 1
#         elif ask1.lower() == "no" or ask1.lower() == "n":
#             self.finished_watching = 0
#         else:
#             print(template.request_response.format("Please type yes/y or no/n"))
#             self.ask_if_finished_watching()
# 
#     # THIS FUNCTION NO LONGER NEEDED. KEEPING JUST IN CASE.
#     # This funktion asks User if he is current watching this show or it wants to add the show as "Plan to watch". If user is currently watching show 1 will be added to field finneshed_watching, while 2 will be added if user plans to watch the series.
#     def ask_if_currently_watching(self):
#         print(template.request_response.format("Are you watching this show currently? yes(y) / no (n). If you choose <no> show will be added to plan to watch list."))
#         ask2 = input()
#         if ask2.lower() == "yes" or ask2.lower() == "y":
#             self.finished_watching = 0
#         elif ask2.lower() == "no" or ask2.lower() == "n":
#             self.finished_watching = 2
#         else:
#             print(template.request_response.format("Please type yes/y or no/n"))
#             self.ask_if_finished_watching()
    
    def add_show(self):
        # Getting title of the show using imdbpie.
        title = imdb.get_title_auxiliary(self.IMDB_id)
        # Getting a list of seasons to iterate throught
        self.show_seasons = imdb.get_title_episodes_detailed(self.IMDB_id, 1)['allSeasons']
        # Following part is needed because some shows have 'Unknowsn'/None season. This season should not show up in full season list, but should still be printed out, when printing the all episodes.
        full_seasons = self.show_seasons.copy()
        if None in full_seasons:
            full_seasons.remove(None)


        # Sometime Show has a None season. This if function will make a variable that will containt a list of seasons without it.
        title_type = title['titleType']

        if title_type == 'movie':
            print(template.information.format("You privded link to the movie, not a series"))
            sys.exit()
        print(template.information.format("Adding show - %s - to the database" % self.IMDB_id))
        # Downloadning HTML page of the website.
        html_page = urllib.urlopen("https://www.imdb.com/title/" + self.IMDB_id +"/")
        # Parsing downloaded HTML file to get title of the page.
        soup_title = BeautifulSoup(html_page, 'html.parser').title.contents[0]
        # Parsing years aired of the show.
        years_aired = re.findall("\d{4}", soup_title)
    
        # Getting title of the show.
        show_title = title['title']
        # Getting link to the image of the show.
        try:
            show_image = title["image"]["url"]
        except KeyError:
            show_image = ""
        # Getting summary of the show.
        try:
            show_summary = title['plot']['outline']['text']
        except KeyError:
            show_summary = title['plot']['summaries'][0]['text']
        except TypeError:
            show_summary = "There is no summary available at this time"
        # Getting length of the episode.
        try:
            show_running_time = title['runningTimeInMinutes']
        except KeyError:
            show_running_time = 0
        # Getting show's genres
        show_genres = title['genres']

        # assigning variable finished watching to default value 0 (no). User will be asked if he finished watchin the show just if show finished airing.

        # Printing title of the chosen IMDB_id
        print(show_title)
        print()
        # Printing number of seasons
        print("Number of seasons: " + str(len(self.show_seasons)))
        print()
        # Printing link to image
        print("Link to the image: " + show_image)
        print()
        # Printing summary 
        print("Outline: " + show_summary)
        print()
        if len(years_aired) == 2:
            print("Finised airing (" + years_aired[0] + " - " + years_aired[1] + ")")
            show_years_aired = years_aired[0] + " - " + years_aired[1]
#             if len(self.finished_watching) == 0: 
#                 self.ask_if_finished_watching()
        else:
            print ("Still Airing")
            show_years_aired = years_aired[0] + " - "
#             if len(self.finished_watching) == 0: 
#                 self.ask_if_currently_watching()
        print()
        
        print("Inserting data in to database")
        
        con.execute("INSERT INTO shows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.IMDB_id, show_title, show_image, show_summary, len(full_seasons), " ".join(show_genres), show_running_time, len(years_aired), show_years_aired, self.finished_watching))
        con.commit()
        self.add_show_episodes()
    
    def add_show_episodes(self):
        cur.execute("CREATE TABLE IF NOT EXISTS %s (episode_watched INTEGER, season INTEGGER, episode INTEGER, episode_IMDB_id TEXT NOT NULL PRIMARY KEY, episode_seasonal_id TEXT, episode_year INTEGER, episode_title TEXT NOT NULL, air_date TEXT)" % self.IMDB_id
        )
        # Creating table for the show episodes if it doesn't exist.
        print("Episode data will be downloaded and added to the database")
        for season in self.show_seasons:
            
            if season == None:
                # This has a lot of errors and most likely holds episodes for upcoming seasons
                print(template.information.format("Adding season 'Unknown' to the database"))
                current_season = imdb.get_title_episodes_detailed(self.IMDB_id, len(self.show_seasons))
                for episodes in current_season['episodes']:
                    # Had to add this if statement, because I added new state for the series, that other functions do not recognized this status of the episode.
                    if self.finished_watching == 2:
                        finished_watching = 0
                    else:
                        finished_watching = self.finished_watching

                    print("++++++~~~~~~++++++")
                    current_ep_season = ''
                    print("Episode's season " + current_ep_season)
                    current_ep_number = episodes['episodeNumber']
                    print("Episode's number: " + str(current_ep_number))
                    current_ep_IMDB_id = self.get_IMDB_id_lambda(episodes['id'])
                    print("Episode's IMDB_id: "+ current_ep_IMDB_id)
                    current_ep_seasonal_id = ''
                    print("Episode's seasonal ID: " + current_ep_seasonal_id)
                    current_ep_year = episodes['year']
                    print("Episode's air year : " + str(current_ep_year))
                    current_ep_title = episodes['title']
                    print("Episode's title: " + current_ep_title)
                    current_ep_air_date = ""
                    print("Episode's air date: " + current_ep_air_date)
                    current_ep_insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % self.IMDB_id
                    con.execute(current_ep_insert_string, (finished_watching, current_ep_season, current_ep_number, current_ep_IMDB_id, current_ep_seasonal_id, current_ep_year, current_ep_title, current_ep_air_date))
                    con.commit()


            else:
                print(template.information.format("Adding season " + str(season) + " episodes."))
                current_season = imdb.get_title_episodes_detailed(self.IMDB_id, season)
                for episodes in current_season['episodes']:   

                    # Had to add this if statement, because I added new state for the series, that other functions do not recognized this status of the episode.
                    if self.finished_watching == 2:
                        finished_watching = 0
                    else:
                        finished_watching = self.finished_watching

                    print("++++++~~~~~~++++++")
                    current_ep_season = season
                    print("Episode's season: " + str(current_ep_season))
                    current_ep_number = episodes['episodeNumber']
                    print("Episode's number: " + str(current_ep_number))
                    current_ep_IMDB_id = self.get_IMDB_id_lambda(episodes['id'])
                    print("Episode's IMDB_id: "+ current_ep_IMDB_id)
                    if current_ep_season <= 9:
                        current_ep_seasonal_id_season = "S0" + str(current_ep_season)
                    else:
                        current_ep_seasonal_id_season = "S" + str(current_ep_season)
                    if current_ep_number <= 9:
                        current_ep_seasonal_id_ep_number = "E0" + str(current_ep_number)
                    else:
                        
                        current_ep_seasonal_id_ep_number = "E" + str(current_ep_number)
                    current_ep_seasonal_id = current_ep_seasonal_id_season + current_ep_seasonal_id_ep_number
                    print("Episode's seasonal ID: " + current_ep_seasonal_id)
                    current_ep_year = episodes['year']
                    print("Episode's air year : " + str(current_ep_year))
                    current_ep_title = episodes['title']
                    print("Episode's title: "+ current_ep_title)
                    current_ep_air_date = episodes['releaseDate']['first']['date']
                    print("Episode's air date: " + str(current_ep_air_date))
                    current_ep_insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % self.IMDB_id
                    con.execute(current_ep_insert_string, (finished_watching, current_ep_season, current_ep_number, current_ep_IMDB_id, current_ep_seasonal_id, current_ep_year, current_ep_title, current_ep_air_date))
                    con.commit()
