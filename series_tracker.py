#!/usr/bin/python3

# This is the main program. From it all other modules will be access from now on.
# This file mainly contains menu options to access other parts of the program.

# Importing Python3 dependencies
import re
import sys
import sqlite3
import webbrowser
import os
import pathlib #  needed to get $HOME folder
import time # Needed to delay update function because of the new IMDB API that detects if you using API too fast?
import configparser # Will be used to store path to the file of the database.

# Setting up config parser
config = configparser.ConfigParser()

# Path to config file directory.
config_dir = os.path.join(pathlib.Path.home(), ".config/SeriesTracker/")

# Opening config file.
config.read(config_dir + "config.ini")
config.sections()

# Importing template module writen by my now because I will need to use it next.
from template import Templates
template = Templates()

try:
    con = sqlite3.connect(config["DATABASE"]["Path"])
except KeyError:
    # Creating config.ini file.
    print("Can't find database")
    print("Type full path to the folder you want to store the database:")
    database_path = input()
    config["DATABASE"] = {"Path" : database_path + "shows.db"}
    

    # Creating directory if it do not exist
    os.makedirs(os.path.dirname(config_dir), exist_ok=True)

    # Opening config file and writing file path.
    with open(config_dir + "config.ini", "w") as configfile:
        config.write(configfile)
        configfile.close()

# Importing other programs modules writen by me.
from add_show import AddShow 
from show_details import ShowDetails
from manage_database import ManageDatabase
from update_shows import UpdateShows
import IMDB_id_validation as validate

# Assingning names to the modules.
add_show = AddShow()
show_details = ShowDetails()
manage_database = ManageDatabase()
update_shows = UpdateShows()

# Connecting to the database
con = sqlite3.connect(config["DATABASE"]["Path"])
cur = con.cursor()

class SeriesTracker:

    # def __init__(self):

    def innitial_options(self):
    
        # Asking user to choose one of the options from main menu.
        print(template.request_response.format("Please choose from the option bellow or paste IMDB id"))
        user_option_list = ["Watchlist", "Plan to Watch", "Finished", "Latest Episodes", "Upcoming Episodes", "Print All Shows", "Search Database", "Add Shows to the Database", "Manage Database"]
    
        for option in range(len(user_option_list)):
            print(template.menu_option.format(str(option + 1) + ".", user_option_list[option]))
        print(template.menu_option.format("0.", "Exit"))

        user_chosen_option = input()
    
        # Executing chosen option or prompting with error.
        if validate.check_if_input_contains_IMDB_id(user_chosen_option):
            self.current_IMDB_id = validate.check_if_input_contains_IMDB_id(user_chosen_option)
            self.fetch_show_info()
        elif user_chosen_option == "1":
            show_details.tracked_shows(0)
            self.innitial_options()
        elif user_chosen_option == "2":
            show_details.tracked_shows(2)
            self.innitial_options()
        elif user_chosen_option == "3":
            show_details.tracked_shows(1)
            self.innitial_options()
        elif user_chosen_option == "4":
            show_details.latest_episodes()
            self.innitial_options()
        elif user_chosen_option == "5":
            show_details.next_episodes()
            self.innitial_options()
        elif user_chosen_option == "6":
            show_details.tracked_shows(4)
            self.innitial_options()
        elif user_chosen_option == "7":
            self.search_database_to_show_info()
            self.show_info_menu()
        elif user_chosen_option == "8":
            self.add_shows()
        elif user_chosen_option == "9":
            self.manage_database_menu()
        elif user_chosen_option == "0":
            self.exit_program()
            
        else:
            print(template.information.format("There is no such option. Please try again."))
            self.innitial_options()

    # Printing ALL shows in the database
    def print_latest_and_next_episodes(self):
        show_details.latest_episodes()
        print(template.empty.format("  "))
        show_details.next_episodes()
        print(template.empty.format("  "))
    
    # This function fetches show info from shows table and assigns variables.
#     def generate_self_variables(self, IMDB_id):
#         
#         cur.execute("SELECT * FROM shows WHERE IMDB_id = '%s'" % IMDB_id)
#         show_info = cur.fetchone()
# 
#         self.current_title = show_info[1]
#         self.current_image = show_info[2]
#         self.current_synopsis = show_info[3]
#         self.current_full_seasons = show_info[4]
#         self.current_genres = show_info[5]
#         self.current_running_time = show_info[6]
#         self.current_finished_airing = show_info[7]
#         self.current_years_aired = show_info[8]
#         self.current_finished_watching = show_info[9]
#         self.current_unknown_season = show_info[10]
# 
#         # Getting count of how many episodes are actually marked as watched.
#         cur.execute("SELECT COUNT(*) FROM %s WHERE episode_watched = 1" % self.current_IMDB_id)
#         self.current_episodes_watched = cur.fetchone()
# 
#         self.current_all_seasons = self.current_full_seasons + self.unknown_season

    def fetch_show_info(self):
        if validate.title_exists_in_database(self.current_IMDB_id):
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
            self.current_unknown_season = show_info[10]
    
            # Getting count of how many episodes are actually marked as watched.
            cur.execute("SELECT COUNT(*) FROM %s WHERE episode_watched = 1" % self.current_IMDB_id)
            self.current_episodes_watched = cur.fetchone()
    
            self.current_all_seasons = self.current_full_seasons + self.current_unknown_season

            show_details.show_info(self.current_episodes_watched, self.current_title, self.current_years_aired, self.current_finished_airing, self.current_genres, self.current_running_time, self.current_full_seasons, self.current_unknown_season, self.current_finished_watching, self.current_synopsis)
            self.show_info_menu()
        else:
            print(template.information.format("Show - " + self.current_IMDB_id + " - doesn't exists in the database or not valid ID."))
            self.innitial_options()

    def add_shows(self):

        # List containing all the shows IMDB_ids in the file.
        IMDB_id_list = []

        # Asking user to choose to withc list he/she wants to add the show.
        import_list_option_list = ["Watchlist", "Plan to Watch", "Finished Watching"]
        print(template.request_response.format("To whitch list do you want to import show(s)?"))
        for option in range(len(import_list_option_list)):
            print(template.menu_option.format(str(option + 1) + ".", import_list_option_list[option]))
        print(template.menu_option.format("0.", "Back to main menu"))
        import_list_option = input()
        if import_list_option == "1":
            self.finished_watching = 0
        elif import_list_option == "2":
            self.finished_watching = 2
        elif import_list_option == "3":
            self.finished_watching = 1
        elif import_list_option == "0":
            self.innitial_options()
        else:
            print(template.information.format("There is no such option. Please try again."))
            self.add_shows()

        # Setting list variable.
        add_show.finished_watching = self.finished_watching

        # Asking user to choose the way he/she wants to import shows.
        import_method_option_list = ["Use LINK", "Use FILE", "Return to previous menu"]
        print(template.request_response.format("Do you want to add show using file or link to the show?"))
        # Printing menu options for user to choose from.
        for option in range(len(import_method_option_list)):
            print(template.menu_option.format(str(option + 1) + ".", import_method_option_list[option]))
        chosen_import_method_option = input()
        if chosen_import_method_option == "1":
            print(template.request_response.format("Please paste IMDB id or link to the series you want to import"))
            # This input from user should contain string with IMDB_id. It can be IMDB_id or text with it (i.e. imdb.com link to the show).
            user_provided_IMDB_str = input()
            # Checking if there is a IMDB_id in the provided link
            if len(user_provided_IMDB_str) != 0:
                add_show.validate_IMDB_id(user_provided_IMDB_str)
            else:
                print(template.information.format("You provided NOTHING!!!!"))
                self.add_shows()

        # Validating user input and looping though user provided file for the option to import shows using file.
        elif chosen_import_method_option == "2":
            print(template.request_response.format("Please type name of the file that contains the list. It has to be in the same folder"))
            filename_of_file_containing_list = input()
            if len(filename_of_file_containing_list) != 0: 
                try: 
                    file_containing_list = open(filename_of_file_containing_list, "r")
                except Exception:
                    print(template.information.format("File not found!"))
                    print(template.information.format("Returning to main menu. Press <ENTER>"))
                    input()
                    self.innitial_options()
                
                for line in file_containing_list:
                    add_show.validate_IMDB_id(line)
            else:
                print(template.information.format("You provided NOTHING!!!!"))
                self.add_shows()
        elif chosen_import_method_option == "3":
            self.innitial_options()

        else:
            print(template.information.format("There is no such option. Please try again."))
            self.add_shows()

        self.innitial_options()
      
    # This funtions uses search_show_title function in show_details class to find a show in the database and get it's IMDB_id.
    # If search is successful show_info table and menu will be printed.    
    # If search was unsuccessful user will be promted and offered and option to do the search again or go to main manu.
    def search_database_to_show_info(self):
        print(template.request_response.format("Please type show title."))
        search_string = input()
        
        # Checking if sting is not empty.
        if len(search_string) > 0:
            search_result = show_details.search_show_title(search_string)
        else:
            print(template.information.format("You have to provide at least ONE symbol!"))
            self.search_database()
        
        # Checking result of the search. 0 means user decided to quit mid search.
        if search_result == '0':
            self.innitial_options()
        # Prints show info of chosen show.
        elif search_result:
            self.current_IMDB_id = search_result
            self.fetch_show_info()
        # Prints error if search came up empty.
        else:
            print(template.information.format("Could not find anything."))
            self.innitial_options()


    # This function is a clone of function above, that made to work to other functions that need to find show in the DB and get IMDB_id instead of printing show info with menu.
    def search_database(self):
        print(template.request_response.format("Please type show title."))
        search_string = input()
        
        # Checking if sting is not empty.
        if len(search_string) > 0:
            search_result = show_details.search_show_title(search_string)
        else:
            print(template.information.format("You have to provide at least ONE symbol!"))
            self.search_database()
        
        # Checking result of the search. 0 means user decided to quit mid search.
        if search_result == '0':
            self.innitial_options()
        # Prints show info of chosen show.
        elif search_result:
            self.current_IMDB_id = search_result
            show_details.current_IMDB_id = self.current_IMDB_id
            show_details.show_info()
        # Prints error if search came up empty.
        else:
            print(template.information.format("Could not find anything."))
            self.innitial_options()

    # Printing information meniu that deals with ways of printing shows in the database.
    def show_info_menu(self):
        option_list = ["Mark next episode as watched", "Print all episodes", "Print single season", "Mark seasons/episodes as watched/not watched", "Update show/season", "Fix season", "Open IMDB page", "Main menu"]
        print(template.request_response.format("Choose one from available options:"))
        for option in range(len(option_list)):
            print(template.menu_option.format(str(option + 1) + ".", option_list[option]))
        print(template.menu_option.format("0.", "Exit program"))
        template.empty.format(" ")
        chosen_option = input()
        self.execute_show_info_menu_option(chosen_option)

    # Executes options available in option menu.
    def execute_show_info_menu_option(self, chosen_option):
        if chosen_option == "1":
            manage_database.mark_next_episode_watched(self.current_IMDB_id)
            self.show_info_menu()
        elif chosen_option == "2":
            show_details.print_show_eps(self.current_IMDB_id, self.current_full_seasons, self.current_unknown_season)
            self.show_info_menu()
        elif chosen_option == "3":
            season_to_print = show_details.choose_single_season(self.current_full_seasons, self.current_unknown_season)
            show_details.print_single_season(self.current_IMDB_id, season_to_print)
            self.show_info_menu()
        elif chosen_option == "4":
            self.mark_seasons_episodes_as_watched_menu()
            self.show_info_menu()
        elif chosen_option == "5":
            self.update_menu()
            self.show_info_menu()
        elif chosen_option == "6":
            self.fix_season()
            self.show_info_menu()
        elif chosen_option == "7":
            self.open_imdb_page()
            self.show_info_menu()
        elif chosen_option == "8":
            self.innitial_options()
        elif chosen_option == "0":
            self.exit_program()
        else:
            print(template.information.format("There is no such option. Please try again."))
            self.show_info_menu()

    # function to open show IMDB page
    def open_imdb_page(self):
        imdb_url = "https://www.imdb.com/title/" + self.current_IMDB_id
        webbrowser.open(imdb_url, new=2, autoraise=True)

    def fix_season(self):
        chosen_season = show_details.choose_single_season(self.current_full_seasons, self.current_unknown_season)
        update_shows.fix_season(self.current_IMDB_id, chosen_season, self.current_full_seasons)

    def update_menu(self):
        update_info_menu_options = ["Update show info", "Update single season", "Update show"]
        print(template.request_response.format("Chose one out of available options"))
        for option in range(len(update_info_menu_options)):
            print(template.menu_option.format(str(option + 1) + ".",  update_info_menu_options[option]))
        print(template.menu_option.format("0.", "Return to previous menu"))
        chosen_update_menu_option = input()
        self.execute_update_menu_option(chosen_update_menu_option)
        
    def execute_update_menu_option(self, chosen_option):
        if chosen_option == "1":
            update_shows.update_show_info(self.current_IMDB_id)
            self.fetch_show_info()
            self.show_info_menu()
        elif chosen_option == "2":
            chosen_season = show_details.choose_single_season(self.current_full_seasons, self.current_unknown_season)
            update_shows.update_season(self.current_IMDB_id, chosen_season)
            self.show_info_menu()
        elif chosen_option == "3":
            update_shows.update_show(self.current_IMDB_id)
            self.show_info_menu()
        elif chosen_option == "0":
            self.show_info_menu()
        else:
            print(template.information.format("There is no such option. Please try again."))
            self.update_menu()

    def mark_seasons_episodes_as_watched_menu(self):
        mark_seasons_episodes_as_watched_menu_options = ["Mark season as watched", "Mark episode as watched", "Mark up to episode as watched", "Mark season as not watched", "Mark episode as not watched"]
        print(template.request_response.format("Choose one out of available options"))
        for option in range(len(mark_seasons_episodes_as_watched_menu_options)):
            print(template.menu_option.format(str(option + 1) + ".", mark_seasons_episodes_as_watched_menu_options[option]))
        print(template.menu_option.format("0.", "Return to previous menu"))
        chosen_mark_as_watched_option = input()
        self.execute_chosen_mark_as_watched_option(chosen_mark_as_watched_option)

    def execute_chosen_mark_as_watched_option(self, chosen_option):
        if chosen_option == "1":
            chosen_season = show_details.choose_single_season(self.current_full_seasons, self.current_unknown_season)
            manage_database.mark_season_as_watched(self.current_IMDB_id, chosen_season)
        elif chosen_option == "2":
            manage_database.mark_episode_as_watched(self.current_IMDB_id)
        elif chosen_option == "3":
            manage_database.mark_up_to_episode(self.current_IMDB_id)
        elif chosen_option == "4":
            chosen_season = show_details.choose_single_season(self.current_full_seasons, self.current_unknown_season)
            manage_database.mark_season_as_not_watched(self.current_IMDB_id, chosen_season)
        elif chosen_option == "5":
            manage_database.mark_episode_as_not_watched(self.current_IMDB_id)
        elif chosen_option == "0":
            self.show_info_menu()
        else:
            print(template.information.format("There is no such option. Returning to previous menu."))
            self.show_info_menu()

    # This function manages "Manage Database" menu.
    def manage_database_menu(self):
        manage_database_options = ["Mark show as 'Finished'", "Add show to 'Watchlist'", "Mark show as 'Plan to Watch'", "Update shows in 'Watchlist'", "Delete show"]
        print(template.request_response.format("Choose one out of available options"))
        for option in range(len(manage_database_options)):
            print(template.menu_option.format(str(option + 1) + ".", manage_database_options[option]))
        print(template.menu_option.format(str(len(manage_database_options) + 1) + ".", "Main menu"))
        print(template.menu_option.format("0.", "Exit"))
        manage_database_chosen_option = input()
        self.execute_manage_database_option(manage_database_chosen_option)

    # Executes manage database menu option
    def execute_manage_database_option(self, chosen_option):
        if chosen_option == "1":
            self.mark_show_as_finished()
            self.manage_database_menu()
        elif chosen_option == "2":
            self.add_show_to_watchlist()
            self.manage_database_menu()
        elif chosen_option == "3":
            self.mark_show_as_plan_to_watch()
            self.manage_database_menu()
        elif chosen_option == "4":
            self.update_watchlist_shows()
            self.manage_database_menu()
        elif chosen_option == "5":
            self.delete_show()
            self.manage_database_menu()
        elif chosen_option == "6":
            self.innitial_options()
        elif chosen_option == "0":
            self.exit_program()
        else:
            print(template.information.format("There is no such option. Please try again."))
            self.manage_database_menu()

    # Marks chosen show as watched (finished). User can choose from printed watchlist, search the database or cancel operation.
    def mark_show_as_finished(self):
        
        # Printing available options to the user.
        mark_as_finished_menu_options = ["Choose show from Watchlist", "Search the database"]
        print(template.request_response.format("Please choose from the following options:"))
        for option in range(len(mark_as_finished_menu_options)):
            print(template.menu_option.format(str(option +1) + ".", mark_as_finished_menu_options[option]))
        print(template.menu_option.format("0.", "Cancel"))

        chosen_option = input()
       
        # Prints watchlist, validates user input and marks show as watched.
        if chosen_option == "1":
            print(template.request_response.format("Choose from the following shows and copy IMDB id or press 0 to cancel."))
            show_details.tracked_shows(0)
            user_chosen_show_input = input()
            # Checks if user chose to cancel operation.
            if user_chosen_show_input == '0':
                print(template.information.format("Returning to previous menu"))
                self.manage_database_menu()
            # Validates user input and assings it to currrent_IMDB_id
            elif validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input):
               self.current_IMDB_id = validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input) 
            # Prints error if user did not provide a valid IMDB_id
            else:
                print(template.information.format("You did not provide correct IMDB_id or show does not exists in the database."))
                self.mark_show_as_finished()
        # Lets user search the database and marks show as watched.
        elif chosen_option == "2":
            self.search_database()
            print(template.request_response.format("Do you really want to mark this show as watched? Yes (y) / No (n)"))
            user_input = input()
            if user_input.lower() == "no" or user_input.lower() == "n":
                print(template.information.format("Canceling Operation!"))
                self.manage_database_menu()
            elif user_input.lower() == "yes" or user_input.lower() == "y":
                pass
            else:
                print(template.information.format("Plase choose between yes (y) and no (n)!"))

        # Quits function and prints innitial option menu.
        elif chosen_option == "0":
            self.manage_database_menu()
        # Shows a message that user chose an option that does not exists and reprints the same menu.
        else:
            print(template.information.format("There is no such option!"))
            self.mark_show_as_finished()

        manage_database.mark_show_as_finished(self.current_IMDB_id)
        
    # Function that allows add show to watchlist. User can choose from "Plan to Watch' list, search database or cancel.
    def add_show_to_watchlist(self):
        # Printing available options to the user.
        add_show_to_watchlist_menu_options = ["Choose show from 'Plan to Watch'", "Search the database"]
        print(template.request_response.format("Please choose from the following options:"))
        for option in range(len(add_show_to_watchlist_menu_options)):
            print(template.menu_option.format(str(option +1) + ".", add_show_to_watchlist_menu_options[option]))
        print(template.menu_option.format("0.", "Cancel"))

        chosen_option = input()

        # Prints watchlist, validates user input and marks show as watched.
        if chosen_option == "1":
            print(template.request_response.format("Choose from the following shows and copy IMDB id or press 0 to cancel."))
            show_details.tracked_shows(2)
            user_chosen_show_input = input()
            # Checks if user chose to cancel operation.
            if user_chosen_show_input == '0':
                print(template.information.format("Returning to previous menu"))
                self.manage_database_menu()
            # Validates user input and assings it to currrent_IMDB_id
            elif validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input):
               self.current_IMDB_id = validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input) 
            # Prints error if user did not provide a valid IMDB_id
            else:
                print(template.information.format("You did not provide correct IMDB_id or show does not exists in the database."))
                self.mark_show_as_finished()
        # Lets user search the database and marks show as watched.
        elif chosen_option == "2":
            self.search_database()
            print(template.request_response.format("Do you really want to add this show to 'Watchlist'? Yes (y) / No (n)"))
            user_input = input()
            if user_input.lower() == "no" or user_input.lower() == "n":
                print(template.information.format("Canceling Operation!"))
                self.manage_database_menu()
            elif user_input.lower() == "yes" or user_input.lower() == "y":
                pass
            else:
                print(template.information.format("Plase choose between yes (y) and no (n)!"))

        # Quits function and prints innitial option menu.
        elif chosen_option == "0":
            self.manage_database_menu()
        # Shows a message that user chose an option that does not exists and reprints the same menu.
        else:
            print(template.information.format("There is no such option!"))
            self.mark_show_as_finished()

        manage_database.add_show_to_watchlist(self.current_IMDB_id)

    # Marks chosen show as plan to watch. User can choose from printed watchlist, search the database or cancel operation.
    def mark_show_as_plan_to_watch(self):
        
        # Printing available options to the user.
        mark_show_as_plan_to_watch_menu_options = ["Choose show from Watchlist", "Search the database"]
        print(template.request_response.format("Please choose from the following options:"))
        for option in range(len(mark_show_as_plan_to_watch_menu_options)):
            print(template.menu_option.format(str(option +1) + ".", mark_show_as_plan_to_watch_menu_options[option]))
        print(template.menu_option.format("0.", "Cancel"))

        chosen_option = input()
       
        # Prints watchlist, validates user input and marks show as watched.
        if chosen_option == "1":
            print(template.request_response.format("Choose from the following shows and copy IMDB id or press 0 to cancel."))
            show_details.tracked_shows(0)
            user_chosen_show_input = input()
            # Checks if user chose to cancel operation.
            if user_chosen_show_input == '0':
                print(template.information.format("Returning to previous menu"))
                self.manage_database_menu()
            # Validates user input and assings it to currrent_IMDB_id
            elif validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input):
               self.current_IMDB_id = validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input) 
            # Prints error if user did not provide a valid IMDB_id
            else:
                print(template.information.format("You did not provide correct IMDB_id or show does not exists in the database."))
                self.mark_show_as_finished()
        # Lets user search the database and marks show as watched.
        elif chosen_option == "2":
            self.search_database()
            print(template.request_response.format("Do you really want to mark this show as 'Plan to Watch'? Yes (y) / No (n)"))
            user_input = input()
            if user_input.lower() == "no" or user_input.lower() == "n":
                print(template.information.format("Canceling Operation!"))
                self.manage_database_menu()
            elif user_input.lower() == "yes" or user_input.lower() == "y":
                pass
            else:
                print(template.information.format("Plase choose between yes (y) and no (n)!"))

        # Quits function and prints innitial option menu.
        elif chosen_option == "0":
            self.manage_database_menu()
        # Shows a message that user chose an option that does not exists and reprints the same menu.
        else:
            print(template.information.format("There is no such option!"))
            self.mark_show_as_finished()

        manage_database.mark_show_as_plan_to_watch(self.current_IMDB_id)

    def update_watchlist_shows(self):
        
        cur.execute("SELECT IMDB_id, title FROM shows WHERE finished_watching = 0")
        
        watchlist_IMDB_id_list = cur.fetchall()

        for current_IMDB_id in watchlist_IMDB_id_list:
            print(template.information.format("Updating %s" % current_IMDB_id[1]))
            update_shows.update_show(current_IMDB_id[0])
            # Delaying downloading next JSON file to not trigger API protection
            time.sleep(5)


    def delete_show(self):

        # Printing available options to the user.
        delete_show_menu_options = ["Print all show in the database", "Search the database"]
        print(template.request_response.format("Please choose from the following options:"))
        for option in range(len(delete_show_menu_options)):
            print(template.menu_option.format(str(option +1) + ".", delete_show_menu_options[option]))
        print(template.menu_option.format("0.", "Cancel"))

        chosen_option = input()
       
        # Prints watchlist, validates user input and marks show as watched.
        if chosen_option == "1":
            print(template.request_response.format("Choose from the following shows and copy IMDB id or press 0 to cancel."))
            show_details.tracked_shows(4)
            user_chosen_show_input = input()
            # Checks if user chose to cancel operation.
            if user_chosen_show_input == '0':
                print(template.information.format("Returning to previous menu"))
                self.manage_database_menu()
            # Validates user input and assings it to currrent_IMDB_id
            elif validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input):
               self.current_IMDB_id = validate.input_contains_IMDB_id_and_exists_in_database(user_chosen_show_input) 
            # Prints error if user did not provide a valid IMDB_id
            else:
                print(template.information.format("You did not provide correct IMDB_id or show does not exists in the database."))
                self.mark_show_as_finished()
        # Lets user search the database and marks show as watched.
        elif chosen_option == "2":
            self.search_database()
            print(template.request_response.format("Do you really want to delete this show? Yes (y) / No (n)"))
            user_input = input()
            if user_input.lower() == "no" or user_input.lower() == "n":
                print(template.information.format("Canceling Operation!"))
                self.manage_database_menu()
            elif user_input.lower() == "yes" or user_input.lower() == "y":
                pass
            else:
                print(template.information.format("Plase choose between yes (y) and no (n)!"))
        # Quits function and prints innitial option menu.
        elif chosen_option == "0":
            self.manage_database_menu()
        # Shows a message that user chose an option that does not exists and reprints the same menu.
        else:
            print(template.information.format("There is no such option!"))
            self.mark_show_as_finished()

        manage_database.delete_show(self.current_IMDB_id)

    def exit_program(self):
        sys.exit()


def main():
    
    series_tracker = SeriesTracker()

    print(template.text.format("Welcome to Series Tracker."))
    print(template.text.format("This program uses information gathered from IMDB to make a database from the shows you have selected."))
    print(template.text.format("It helps you track a shows you want to watch by letting you mark watched episodes and displaying the latest aired episode."))
    print(template.seperator)
    print(template.seperator)
    print(template.empty.format("  "))

    series_tracker.print_latest_and_next_episodes()
    series_tracker.innitial_options()

if __name__ == "__main__": 
    main()


