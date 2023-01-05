import mlbstatsapi

from multiprocessing.pool import ThreadPool

"""
While run expectancy charts can be produced based on league-wide statistics 
for any given period of time, they are more accurate when using 
ballpark-specific data. 
    - https://statcorner.com/mlb/stats/re24
"""

mlb = mlbstatsapi.Mlb()

def new_gamestatmatrix():
    """
    Creates a new matrix for storing the game state matrix data.
    """
    return [
    #           0o                    1o                   2o             1b 2b 3b
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # _ _ _ 
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # x _ _
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # _ x _
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # _ _ x
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # x x _
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # x _ x
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # _ x x
        [{"apps":0,"runs":0}, {"apps":0,"runs":0}, {"apps":0,"runs":0}],  # x x x
    ]

def new_runexpectedmatrix():
    """
    Creates a new matrix for storing the run expected matrix data.
    """
    return [
    #    0o 1o 2o             1b 2b 3b
        [0, 0, 0],  # _ _ _ 
        [0, 0, 0],  # _ _ _   # x _ _
        [0, 0, 0],  # _ _ _   # _ x _
        [0, 0, 0],  # _ _ _   # _ _ x
        [0, 0, 0],  # _ _ _   # x x _
        [0, 0, 0],  # _ _ _   # x _ x
        [0, 0, 0],  # _ _ _   # _ x x
        [0, 0, 0],  # _ _ _   # x x x
    ]

def get_REM_rownumber(first, second, third):
    """
    Returns the row number in a REM based on occupied bases

    Parameters:
    -----------
    first : bool 
        True if first base is occupied, False otherwise.
    second : bool 
        True if second base is occupied, False otherwise.
    third : bool 
        True if third base is occupied, False otherwise.
    """
    rownum = 0
    rownum += 1 if first else 0
    rownum += 2 if second else 0
    rownum += 3 if third else 0
    rownum += 1 if sum([first, second, third]) > 1 else 0
    return rownum

def add_gsm(source_gsm, target_gsm):
    """
    Adds the data from the source game state matrix to the target game state matrix.

    Parameters:
    -----------
    source_gsm : list 
        The source game state matrix.
    target_gsm : list 
        The target game state matrix.
    """
    for x, state_row in enumerate(source_gsm):
        for y, out_col in enumerate(state_row):
            target_gsm[x][y]["apps"] += out_col["apps"]
            target_gsm[x][y]["runs"] += out_col["runs"]
    return target_gsm

def calculate_gsm(source):
    """
    Calculates the game state matrix data based on the source data.

    Parameters:
    -----------
    source : dict 
        The source data for calculating the game state matrix.
    """
    calculated_REM = {}

    total_gsm = new_gamestatmatrix()

    for venue in source:

        calculated_REM[venue] = new_runexpectedmatrix()

        for x, state_row in enumerate(source[venue]):
            for y, out_col in enumerate(state_row):              

                if out_col["apps"]:
                    calculated_REM[venue][x][y] = out_col["runs"] / out_col["apps"]
                else:
                    calculated_REM[venue][x][y] = out_col["runs"]
                
                total_gsm[x][y]["apps"] += out_col["apps"]
                total_gsm[x][y]["runs"] += out_col["runs"]

    source["all"] = total_gsm

    calculated_REM["all"] = new_runexpectedmatrix()

    for x, state_row in enumerate(total_gsm):
        for y, out_col in enumerate(state_row):
            if out_col["apps"]:
                calculated_REM["all"][x][y] = out_col["runs"] / out_col["apps"]
            else:
                calculated_REM["all"][x][y] = out_col["runs"]

    return calculated_REM, source


def calculate_inningcord_gsm(inning, play_by_play):
    """
    Calculates the game state matrix data based on the inning data and play by play data.

    Parameters:
    -----------
    inning : list 
        A list of integers representing the index numbers of the plays in the inning.
    play_by_play : object 
        An object containing the play by play data for a game.
    """
    temp_gamestatmatrix = new_gamestatmatrix()    

    if inning:
        for inning_index in range (inning[0], inning[-1]+1): 
            atbat = play_by_play.allplays[inning_index]

            onfirst = False
            onsecond = False
            onthird = False
            outs = 0
            
            # If this is not the first at bat of the inning. Get the unknown 
            # inning state. If it is, inning state is known and remains unchanged
            # from the previous defined inning state variables
            if inning_index != inning[0]:               
                prev_atbat = play_by_play.allplays[inning_index-1]

                onfirst = True if prev_atbat.matchup.postonfirst else False
                onsecond = True if prev_atbat.matchup.postonsecond else False
                onthird = True if prev_atbat.matchup.postonthird else False
                outs = prev_atbat.count.outs
                
            rem_row = get_REM_rownumber(onfirst, onsecond, onthird)                

            temp_gamestatmatrix[rem_row][outs]["apps"] += 1

            if atbat.result.rbi > 0:
                for row in temp_gamestatmatrix:
                    for rowout in row:
                        if rowout["apps"] > 0:
                            rowout["runs"] += atbat.result.rbi

    return temp_gamestatmatrix

def output_gsm(gsm, gsm_stats, venues):
    """
    Outputs the game state matrix and game state matrix statistics in a formatted table.

    Parameters:
    -----------
    gsm : dict 
        The game state matrix data.
    gsm_stats : dict 
        The game state matrix statistics data.
    venues : dict 
        The venues data.
    """
    bsv = [
        "_  _  _",
        "x  _  _",
        "_  x  _",
        "_  _  x",
        "x  x  _",
        "x  _  x",
        "_  x  x",
        "x  x  x"
    ]
    bs_info = "    1b 2b 3b    "
    out_info = '{:^9}'.format("0 out") + " " + '{:^9}'.format("1 out") + " " + '{:^9}'.format("2 out")
    ts_info = '{:^46}'.format("Table Stats (Abs/Rtie)")

    for venue in gsm:

        venue_name = venues[venue].name if venue != "all" else "Overall run expectancy matrix"

        print ()
        print (F"    {venue_name}")
        print ("   ", '-' * len(venue_name))
        print ()
        print (bs_info, out_info, "           ", ts_info)
        print ()
        print ("               -------------------------------            ----------------------------------------------")

        for bsnumb,basestate in enumerate(gsm[venue]): #rows 0-7
            left_bs = F"    {bsv[bsnumb]}    |"

            zero_out = '{:^7.3f}'.format(basestate[0])
            one_out = '{:^7.3f}'.format(basestate[1])
            two_out = '{:^7.3f}'.format(basestate[2])

            stat_zero_out = '{:^12}'.format(f'{gsm_stats[venue][bsnumb][0]["apps"]}/{gsm_stats[venue][bsnumb][0]["runs"]}')
            stat_one_out = '{:^12}'.format(f'{gsm_stats[venue][bsnumb][1]["apps"]}/{gsm_stats[venue][bsnumb][1]["runs"]}')
            stat_two_out = '{:^12}'.format(f'{gsm_stats[venue][bsnumb][2]["apps"]}/{gsm_stats[venue][bsnumb][2]["runs"]}')

            print (left_bs, zero_out, "|", one_out, "|", two_out, "|            |", stat_zero_out, "|", stat_one_out, "|", stat_two_out, "|")
            print ("               -------------------------------            ----------------------------------------------")

def multithread_rem_calculator(game):
    """
    Calculates the run expectancy matrix data for a game using multithreading.

    Parameters:
    -----------
    game : object
        An object containing information about the game.
    """
    sl_1 = F"{game.gamepk} {game.gamedate}  {game.teams.away.team.name[:4]} "
    sl_2 = '{:<8}'.format(f"({game.teams.away.score})")
    sl_3 = F"@ {game.teams.home.team.name[:4]} "
    sl_4 = '{:<8}'.format(f"({game.teams.home.score})")

    threadPrintString = F"  {sl_1} {sl_2} {sl_3} {sl_4}"

    temp_runexpectancymatrix = new_gamestatmatrix()

    play_by_play = mlb.get_game_play_by_play(game_id=game.gamepk)
    
    threadPrintString += "  Inning: "

    if not play_by_play:
        print (threadPrintString + "                           failed", flush=True)
        return temp_runexpectancymatrix, game.venue

    if play_by_play.allplays and play_by_play.playsbyinning:

        inningCompletionString = ""

        for inning in play_by_play.playsbyinning:

            inningCompletionString += ". "

            top_gsm = calculate_inningcord_gsm(inning.top, play_by_play)
            bottom_gsm = calculate_inningcord_gsm(inning.bottom, play_by_play)

            add_gsm(bottom_gsm, temp_runexpectancymatrix)
            add_gsm(top_gsm, temp_runexpectancymatrix)

        threadPrintString += F"{'{:<24}'.format(inningCompletionString)} Complete"
    
    else:
        threadPrintString += " Failed"

    
    print (threadPrintString, flush=True)
    return temp_runexpectancymatrix, game.venue

def calculate_runexpectancymatrix():
    """
    Calculates the run expectancy matrix data for the season using multithreading.
    """
    # Gather the information that is to be used to create the Run Expectancty Matrix (REM)
    seasoninfo = mlb.get_season(season_id = 2022, fields='seasons,seasonId,seasonStartDate,seasonEndDate')
    venues = mlb.get_venues(sportIds=1, season=2022)
    seasongames = mlb.get_scheduled_games_by_date(start_date = seasoninfo.seasonstartdate, end_date = seasoninfo.seasonenddate)
    # seasongames = mlb.get_scheduled_games_by_date(start_date = start_date, end_date = end_date)
    numberofgamesinseason = len(seasongames)
    
    venues = {}
    runexpectancymatrix = {}

    pool = ThreadPool() 

    # For every game in the date range, use multithreading to efficiently 
    # compute its REM.
    for rem, venue in pool.imap(multithread_rem_calculator, seasongames):
        if venue.id not in runexpectancymatrix:            
            venues[venue.id] = venue # Add venue to our venue dict            
            runexpectancymatrix[venue.id] = new_gamestatmatrix() # Initialize new venue matrix
        # Add game rem matrix to venue total rem matrix    
        add_gsm(rem, runexpectancymatrix[venue.id])

    gsm_table, gsm_table_stats = calculate_gsm(runexpectancymatrix)

    # Output the gsm tables for each venue as well as overall
    output_gsm(gsm_table, gsm_table_stats, venues)