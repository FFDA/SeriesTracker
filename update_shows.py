#!/usr/bin/python3

# This class will update tables of the shows.

import sqlite3

# Importing other programs modules writen by me.
from template import Templates
from add_show import AddShow 
from show_details import ShowDetails
import IMDB_id_validation as validate
from imdbpie import Imdb # This is the dependency that is written by someone else and my program is based on it. It download information in JSON files from IMDB.
import datetime # Used to compare the dates of the episode against the current date.
from bs4 import BeautifulSoup
import urllib.request as urllib
import re
import os
import pathlib #  needed to get $HOME folder
import configparser # Will be used to store path to the file of the database.

# Assingning names to the modules.
template = Templates()
add_show = AddShow()
show_details = ShowDetails()

imdb = Imdb()

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


class UpdateShows:

    def __init__(self):
        # self.current_IMDB_id = current_IMDB_id 
        # self.current_date = datetime.datetime.today().strftime("%Y-%m-%d")
        # self.none_season_in_IMDB = 0
        # self.none_season_in_DB = 0
        # self.current_season = season
        
        # Pattern for IMDB_id
        self.pattern_to_look_for = re.compile("tt\d+")
        
        # This labda should return just IMDB_id from given link
        self.get_IMDB_id_lambda = lambda x: self.pattern_to_look_for.search(x)[0]

    def update_show_info(self, current_IMDB_id):

        # Getting information about the show: season, finished_airing, years_aired
        cur.execute("SELECT seasons, years_aired, finished_airing FROM shows WHERE IMDB_id ='%s'" % current_IMDB_id)
        fetched_show_info = cur.fetchone()

        current_seasons = fetched_show_info[0]
        current_years_aired = fetched_show_info[1]
        current_finished_airing = fetched_show_info[2]

#         print(current_seasons)
#         print(current_years_aired)
#         print(current_finished_airing)
# 
        cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % current_IMDB_id)
        current_unknown_season = cur.fetchone()

        # Gathering information for the change check.
        fetched_show_data = imdb.get_title_episodes_detailed(current_IMDB_id, 1)

        fetched_season_list = fetched_show_data['allSeasons']
        if None in fetched_season_list:
            fetched_season_list.remove(None)
        fetched_seasons = len(fetched_season_list)
        
        
        if None in fetched_season_list:
            fetched_unknown_season = 1
            fetched_seasons = len(fetched_season_list) - 1
        else:
            fetched_unknown_season = 0
            fetched_seasons = len(fetched_season_list)
        
        # Downloadning HTML page of the website.
        html_page = urllib.urlopen("https://www.imdb.com/title/" + current_IMDB_id +"/")
        # Parsing downloaded HTML file to get title of the page.
        soup_title = BeautifulSoup(html_page, 'html.parser').title.contents[0]
        # Parsing years aired of the show.
        years_aired = re.findall("\d{4}", soup_title)

        fetched_finished_airing = len(years_aired)

        if len(years_aired) == 2:
            fetched_years_aired = years_aired[0] + " - " + years_aired[1]
        elif len(years_aired) == 1:
            fetched_years_aired = years_aired[0] + " - "

#         print("*")
#         print(fetched_seasons)
#         print(fetched_years_aired)
#         print(fetched_finished_airing)

        if current_seasons != fetched_seasons:
            cur.execute("UPDATE shows SET seasons = %d WHERE IMDB_id = '%s'" % (fetched_seasons, current_IMDB_id))
            con.commit()
            print(template.information.format("Season count updated"))
#         if current_unknown_season[0] != fetched_unknown_season:
#             print(template.information.format("There is change in unknow season status!"))
        if current_years_aired != fetched_years_aired:
            cur.execute("UPDATE shows SET years_aired = '%s' WHERE IMDB_id = '%s'" % (fetched_years_aired, current_IMDB_id))
            con.commit()
            print(template.information.format("Years aired updated"))
        if current_finished_airing != fetched_finished_airing:
            cur.execute("UPDATE shows SET finished_airing = %s WHERE IMDB_id = '%s'" % (fetched_finished_airing, current_IMDB_id))
            con.commit()
            print(template.information.format("Show status updated"))

    def update_show(self, current_IMDB_id):
        
        list_of_show_seasons = imdb.get_title_episodes_detailed(current_IMDB_id, 1)['allSeasons']
        if None in list_of_show_seasons:
            list_of_show_seasons.remove(None)
            list_of_show_seasons.append(0)

        for season in list_of_show_seasons[-3:]:
            self.update_season(current_IMDB_id, season)

    def update_season(self, current_IMDB_id, current_season):
        
        if current_season == 0:
            # cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % current_IMDB_id)
            # selection_check = cur.fetchone()
            # if selection_check[0] == 1:
            detailed_season_episodes = imdb.get_title_episodes_detailed(current_IMDB_id, 1)
            if None in detailed_season_episodes['allSeasons']:
                self.update_unknown_season(current_IMDB_id)
            else:
                print(template.information.format("Show does not have 'Unknown' season in IMDB"))
        else:
            cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE season = '%s')" % (current_IMDB_id, current_season))
            selection_check = cur.fetchone()
            if selection_check[0] == 1:
                self.update(current_IMDB_id, current_season)
            else:
                print(template.information.format("There is no season %s for this show" % current_season))
        
# # # # # # # # # # # # # # 
#         # Setting season from which this class will update shows DB.
#         cur.execute("SELECT season FROM %s WHERE air_date < '%s' ORDER BY air_date DESC" % (self.current_IMDB_id, self.current_date))
#         first_season_to_u)date = cur.fetchone()[0] - 1
# 
#         random_season = imdb.get_title_episodes_detailed(self.current_IMDB_id, first_season_to_update)
# 
#         last_season_to_update = len(random_season["allSeasons"])

        # Cheking if show has None season in IMDB or DB
        # if None in random_season['allSeasons']:
        #     self.none_season_in_IMDB = 1
        #     print("None season in IMDB")
        
        # cur.execute("SELECT EXISTS (SELECT * FROM %s WHERE season = '')" % self.current_IMDB_id)
        # check_if_season_none_exists = cur.fetchone()

        
        # if check_if_season_none_exists == 1:
        #     self.none_season_in_DM = 1
        #     print("None season in DB")
# # # # # # # # # # # # # # 

    # This function updates given season's epsidoes and add's extra episodes to the season if it detects them in the JSON file download from IMDB
    def update(self, current_IMDB_id, current_season):
        
        # Getting detailed episode JSON file from IMDB using IMDBpie
        detailed_season_episodes = imdb.get_title_episodes_detailed(current_IMDB_id, current_season)

        # Setting counter to print a message to user how many files where updated.
        updated_episode_count = 0
        added_episode_count = 0

        # Looping though episode in JSON file, assinging variable name to data that will be updated or inserted in to database.
        for episode in detailed_season_episodes['episodes']:
            
            fetched_episode_IMDB_id = self.get_IMDB_id_lambda(episode['id'])

            # Selecting episode from the database using it's IMDB_id
            cur.execute("SELECT * FROM %s WHERE episode_IMDB_id = '%s'" % (current_IMDB_id, fetched_episode_IMDB_id))  
            episode_from_database = cur.fetchone()
            
            # Checking if episode anctually axists. If it does, variables names are assing to it's information
            if episode_from_database != None:

                current_episode_number = episode_from_database[2]
                current_episode_year = episode_from_database[5]
                current_episode_title = episode_from_database[6]
                current_episode_air_date = episode_from_database[7]

                fetched_episode_number = episode["episodeNumber"]
                fetched_episode_year = episode["year"]
                fetched_episode_title = episode["title"]
                fetched_episode_air_date = episode["releaseDate"]["first"]["date"]

                # Checking if there is a difference between the fetched data from IMDB and database. If so data is formated and record is updated.
                if current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:
                
                    if current_season <= 9:
                        new_episode_seasonal_id_season = "S0" + str(current_season)
                    else:
                        new_episode_seasonal_id_season = "S" + str(current_season)
                    if fetched_episode_number <= 9:
                        new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
                    else:
                        new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
                    
                    fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
                    
                    # Updating episodes information
                    update_episode_string = ("UPDATE '%s' SET episode = ?, episode_seasonal_id = ?, episode_year = ?, episode_title = ?, air_date = ? WHERE episode_IMDB_id = ?" % current_IMDB_id)
                    cur.execute(update_episode_string, (fetched_episode_number, fetched_episode_seasonal_id, fetched_episode_year, fetched_episode_title, fetched_episode_air_date, fetched_episode_IMDB_id))
                    con.commit()
                    # Setting updated episode counter +1
                    updated_episode_count += 1
        
            # If episode does not exist in the database it is inserted in as a new record. The same steps are taken as in add new shows episodes in the add_show.py file.   
            else:
    
                fetched_episode_number = episode["episodeNumber"]
                fetched_episode_year = episode["year"]
                fetched_episode_title = episode["title"]
                fetched_episode_air_date = episode["releaseDate"]["first"]["date"]
    
                if current_season <= 9:
                    new_episode_seasonal_id_season = "S0" + str(current_season)
                else:
                    new_episode_seasonal_id_season = "S" + str(current_season)
                if fetched_episode_number <= 9:
                    new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
                else:
                    new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
                
                fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
    
    
                current_episode_insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % current_IMDB_id
                cur.execute(current_episode_insert_string, (0, int(current_season), fetched_episode_number, fetched_episode_IMDB_id, fetched_episode_seasonal_id, fetched_episode_year, fetched_episode_title, fetched_episode_air_date))
                con.commit()

                # Adding to the added episode count
                added_episode_count += 1


        # Printing message to the user with the count of how many episodes were updated/added.
        if updated_episode_count > 0:
            print(template.information.format("Updated %d episodes in %d season" % (updated_episode_count, current_season)))
        if added_episode_count > 0:
            print(template.information.format("Added %d episodes in %d season" % (added_episode_count, current_season)))

    # This class updated episodes that are in "None" season of JSON file.
    def update_unknown_season(self, current_IMDB_id):
        
        # Setting count to track updated records
        updated_episode_count = 0
        added_episode_count = 0

        # Getting the count of all seasons of the show, because "None" season is always last.
        show_season_count = len(imdb.get_title_episodes(current_IMDB_id)['seasons'])
        
        # Getting "None" season information.
        detailed_season_episodes = imdb.get_title_episodes_detailed(current_IMDB_id, show_season_count)

        for episode in detailed_season_episodes["episodes"]:

            fetched_episode_IMDB_id = self.get_IMDB_id_lambda(episode['id'])

            cur.execute("SELECT * FROM %s WHERE episode_IMDB_id = '%s'" % (current_IMDB_id, fetched_episode_IMDB_id))  
            episode_from_database = cur.fetchone()

            # Checking if episode anctually axists. If it does, variables names are assing to it's information
            if episode_from_database != None:

                fetched_episode_number = episode["episodeNumber"]
                fetched_episode_year = episode["year"]
                fetched_episode_title = episode["title"]
                fetched_episode_air_date = episode["releaseDate"]["first"]["date"]
    
                if fetched_episode_number != None:
                    if current_season <= 9:
                        new_episode_seasonal_id_season = "S0" + str(current_season)
                    else:
                        new_episode_seasonal_id_season = "S" + str(current_season)
                    if fetched_episode_number <= 9:
                        new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
                    else:
                        new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
                    
                    fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
                else:
                    fetched_episode_number = ""
                    fetched_episode_seasonal_id = ""
    
                if fetched_episode_year == None:
                    fetched_episode_year = ""
                if fetched_episode_title == None:
                    fetched_episode_title = ""
                if fetched_episode_air_date == None:
                    fetched_episode_air_date = ""
                    

                current_episode_number = episode_from_database[2]
                current_episode_year = episode_from_database[5]
                current_episode_title = episode_from_database[6]
                current_episode_air_date = episode_from_database[7]
                
                # Checking if there is a difference between the fetched data from IMDB and database. If so data is formated and record is updated.
                if current_episode_number != fetched_episode_number or current_episode_year != fetched_episode_year or current_episode_title != fetched_episode_title or current_episode_air_date != fetched_episode_air_date:

                    # Updating episodes information
                    
                    update_episode_string = ("UPDATE '%s' SET episode = ?, episode_seasonal_id = ?, episode_year = ?, episode_title = ?, air_date = ? WHERE episode_IMDB_id = ?" % current_IMDB_id)
                    cur.execute(update_episode_string, (fetched_episode_number, fetched_episode_seasonal_id, fetched_episode_year, fetched_episode_title, fetched_episode_air_date, fetched_episode_IMDB_id))
                    con.commit()
                    # Setting updated episode counter +1
                    updated_episode_count += 1
#                     print(fetched_episode_number)
#                     print(fetched_episode_IMDB_id)
#                     print(fetched_episode_seasonal_id)
#                     print(fetched_episode_air_date)
#                     print(fetched_episode_year)
#                     print(fetched_episode_title)
        
            # If episode does not exist in the database it is inserted in as a new record. The same steps are taken as in add new shows episodes in the add_show.py file.   
            else:
    
                fetched_episode_number = episode["episodeNumber"]
                fetched_episode_year = episode["year"]
                fetched_episode_title = episode["title"]
                fetched_episode_air_date = episode["releaseDate"]["first"]["date"]
    
                if fetched_episode_number != None:
                    if current_season <= 9:
                        new_episode_seasonal_id_season = "S0" + str(current_season)
                    else:
                        new_episode_seasonal_id_season = "S" + str(current_season)
                    if fetched_episode_number <= 9:
                        new_episode_seasonal_id_number = "E0" + str(fetched_episode_number)
                    else:
                        new_episode_seasonal_id_number = "E" + str(fetched_episode_number)
                    
                    fetched_episode_seasonal_id = new_episode_seasonal_id_season + new_episode_seasonal_id_number
                else:
                    fetched_episode_number = ""
                    fetched_episode_seasonal_id = ""
    
                if fetched_episode_year == None:
                    fetched_episode_year = ""
                if fetched_episode_title == None:
                    fetched_episode_title = ""
                if fetched_episode_air_date == None:
                    fetched_episode_air_date = ""
                    current_episode_insert_string = "INSERT INTO %s VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % current_IMDB_id
                    cur.execute(current_episode_insert_string, (0, "", fetched_episode_number, fetched_episode_IMDB_id, fetched_episode_seasonal_id, fetched_episode_year, fetched_episode_title, fetched_episode_air_date))
                    con.commit()

                    added_episode_count += 1
    
         # Printing message to the user with the count of how many episodes were updated/added.
        if updated_episode_count > 0:
            print(template.information.format("Updated %d episodes in 'None' season" % (updated_episode_count)))
        if added_episode_count > 0:
            print(template.information.format("Added %d episodes in 'None' season" % (added_episode_count)))
    
        # show_details.current_IMDB_id = current_IMDB_id
        # show_details.generate_self_variables()
