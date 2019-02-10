#!/usr/bin/python3
# This file contains one classs that has templates to do the formating of the output to the terminal
class Templates:

    from sty import bg, fg, Rule, Render

    # Printing an empty line. In the format function you only need to add "  ".
    bg.indigo_ink = Rule(Render.rgb_bg, 40, 54, 85) #  dark blue
    bg.blueberry = Rule(Render.rgb_bg, 77, 100, 141) # light blue
    bg.fig = Rule(Render.rgb_bg, 76, 63, 84) # purple?
    bg.berry = Rule(Render.rgb_bg, 161, 1, 21) # red
    bg.basil = Rule(Render.rgb_bg, 72, 104, 36) # green
    empty = bg.indigo_ink + "{0:100}" + bg.rs
    # Printing seperator line. It's a line with 100 *.
    seperator = bg.indigo_ink + "*" * 100 + bg.rs
    # Printing line that requires response from User. Mostly before imput() command.
    request_response = bg.da_magenta + "{0:^100}" + bg.rs
    # Printing the line that informas User if something is done or happened.
    # Printing normal text for the user.
    text = bg(142) + fg.black + "{0:^100}" + bg.rs + fg.rs
    information = bg(166) + fg.red + "{0:^100}" + bg.rs + fg.rs
    # Printing line that list option that can be chosen.
    menu_option = bg.fig + "{0:3}{1:97}" + bg.rs
    # Printing line for the table that displays all available shows.
    tracked_shows = bg.indigo_ink + "{0:10}{1:20}{2:20}{3:50}" + bg.rs
    # Printing line that displays information of the chosen show.
    show_info = bg.indigo_ink + "{0:^100}" + bg.rs
    # Header for Next Episode Table
    latest_next_episode_table_header = bg.indigo_ink + "{0:<10}{1:30}{2:15}{3:15}{4:30}" + bg.rs
    latest_next_episodes_unaired = bg.berry + fg.black + "{0:<10}{1:30}{2:15}{3:15}{4:30}" + bg.rs + fg.rs
    # Printing line that displays episode that is already watched. BLUE.
    latest_next_episodes_seen = bg.blueberry + fg.black + "{0:<10}{1:30}{2:15}{3:15}{4:30}" + bg.rs + fg.rs
    # Printing line that displays epidose that is available to watch. GREEN.
    latest_next_episodes_unseen = bg.basil + fg.black + "{0:<10}{1:30}{2:15}{3:15}{4:30}" + bg.rs + fg.rs
    # Printing line that shows header of the episode table.
    episode_table_header = bg.indigo_ink + "{0:<10}{1:18}{2:12}{3:20}{4:40}" + bg.rs
    # Printing line that displays episode that is not available to watch yet. RED
    episodes_unaired = bg.berry + fg.black + "{0:<10}{1:18}{2:12}{3:20}{4:40}" + bg.rs + fg.rs
    # Printing line that displays episode that is already watched. BLUE.
    episodes_seen = bg.blueberry + fg.black + "{0:<10}{1:18}{2:12}{3:20}{4:40}" + bg.rs + fg.rs
    # Printing line that displays epidose that is available to watch. GREEN.
    episodes_unseen = bg.basil + fg.black + "{0:<10}{1:18}{2:12}{3:20}{4:40}" + bg.rs + fg.rs
