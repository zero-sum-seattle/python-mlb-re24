import mlbstatsapi

# For all parks
# Calculated from 
# '2022-04-07' - '2022-05-07' 
# date range
test_rem = [         
    [0.419, 0.222, 0.079],
    [0.779, 0.466, 0.171],
    [1.017, 0.637, 0.300],
    [1.105, 0.836, 0.323],
    [1.282, 0.827, 0.395],
    [1.432, 0.936, 0.430],
    [1.860, 1.333, 0.529],
    [1.912, 1.280, 0.662],
]

def get_matrix_rownumber(first, second, third):
    """
    Returns the row number based on occupied bases
    """
    rownum = 0
    rownum += 1 if first else 0
    rownum += 2 if second else 0
    rownum += 3 if third else 0
    rownum += 1 if sum([first, second, third]) > 1 else 0
    return rownum

def new_player_re24(id, name):
    """
    This function creates and returns a new dictionary representing a player 
    object with the given id and name, and an initial re24 value of 0.
    """
    return {
        "id": id,
        "name": name,
        "re24": 0
    }


def calculate_re24():
    """
    Calculates the run expectation of each play in a game and updates the RE24 value for each player.
    """
    mlb = mlbstatsapi.Mlb()

    # gameid
    game_pk = 661750

    players = {}

    play_by_play = mlb.get_game_play_by_play(game_id=game_pk)
    
    for inning in play_by_play.playsbyinning:
        # Iterate through each at bat in the inning
        for atbat_index in range(inning.startindex, inning.endindex+1):

            atbat = play_by_play.allplays[atbat_index]
            
            # Get the batter and pitcher information
            batter_id = atbat.matchup.batter.id
            batter_name = atbat.matchup.batter.fullname

            # If the player hasn't been seen before, create a new entry for them in the players dictionary
            if batter_id not in players:
                players[f"{batter_id}"] = new_player_re24(batter_id, batter_name)

            pitcher_id = atbat.matchup.pitcher.id
            pitcher_name = atbat.matchup.pitcher.fullname

            # Get the inning and half inning information
            half_inning = atbat.about.halfinning
            inning_num = atbat.about.inning

            result = atbat.result.event
            rbi = atbat.result.rbi

            # Get the base and out information at the end of the at bat
            end_onfirst = True if atbat.matchup.postonfirst else False
            end_onsecond = True if atbat.matchup.postonsecond else False
            end_onthird = True if atbat.matchup.postonthird else False
            end_outs = atbat.count.outs

            # If this is the first at bat of the inning, base and out information is known
            if atbat_index == inning.top[0] or atbat_index == inning.bottom[0]:
                onfirst = False
                onsecond = False
                onthird = False
                outs = 0

                if atbat_index == inning.top[0]:
                    # print ("    Inning over")
                    print ()
                    print (F"   Top of inning {inning_num}")
                    print ("   ----------------")
                else:
                    print (F"   Bottom of inning {inning_num}")
                    print ("   -------------------")

            # If this is not the first at bat of the inning, base and out information must be obtained from the previous at bat
            else:
                prev_atbat = play_by_play.allplays[atbat_index-1]

                onfirst = True if prev_atbat.matchup.postonfirst else False
                onsecond = True if prev_atbat.matchup.postonsecond else False
                onthird = True if prev_atbat.matchup.postonthird else False
                outs = prev_atbat.count.outs

            rebeggining = test_rem[get_matrix_rownumber(onfirst, onsecond, onthird)][outs]

            if end_outs == 3:
                reend = 0
            else :
                reend = test_rem[get_matrix_rownumber(end_onfirst, end_onsecond, end_onthird)][end_outs]

            # re24 = RE end - RE begging + Runs scored
            re24 = reend - rebeggining + rbi

            players[f"{batter_id}"]["re24"] += re24

            ab_bid = batter_id
            ab_bname = '{:>20}'.format(batter_name)
            ab_pid = pitcher_id
            ab_pname = '{:<20}'.format(pitcher_name)
            ab_result = '{:<20}'.format(result)

            ab_runs = rbi

            ab_re_calc = F"({'{:^5.3f}'.format(reend)} - {rebeggining} + {rbi})"
            ab_re24 = '{:>6.3f}'.format(re24)

            gm_re24 = '{:>6.3f}'.format(players[f"{ab_bid}"]["re24"])


            print ("  ", ab_bid, ab_bname, "vs", ab_pname, ab_pid, "   ", ab_result, ab_runs, "   ", gm_re24, "|", ab_re24, " ", ab_re_calc)

    print ()
    print ()
    print ("RE24 for players for game")
    print ("-------------------------")
    
    for player in players:
        p_id = players[player]["id"]
        p_name = '{:<20}'.format(players[player]["name"])
        p_re24 = '{:>6.3f}'.format(players[player]["re24"])

        print ("  ", p_id, p_name, p_re24) 

    print ()