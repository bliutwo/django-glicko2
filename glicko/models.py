from django.db import models
import math
import sys
import requests
import os
import getopt
import os.path
import operator

# Create your models here.

class MatchMaker(models.Model):
    def find_subdomain(self, url):
        pattern = "://"
        s = url.split(pattern,1)[1]
        if s.startswith('challonge'):
            return ''
        else:
            subdomain = s.split('.challonge', 1)[0]
            total = subdomain + '-'
            return total

    def parse_link(self, url):
        pattern = "challonge.com/"
        end = url.split(pattern, 1)[1]
        subdomain = self.find_subdomain(url)
        combo = subdomain + end
        return combo

    def get_info(self, username, api_key, url, info_str, t_str):
        info = []
        data = requests.get
        data = requests.get("https://api.challonge.com/v1/tournaments/" + \
                             t_str + info_str, auth = (username, api_key))
        for line in data:
            info.append(line)
        print("sizeof " + info_str + "_data: " + str(len(self.info)))
        return info

    # arguments:
    # m: matches_str, this is a string that contains the contents of the matches json
    # i: ids_str, this is a string that contains the contents of the ids json
    def parse_matches_ids_strs(self, m, i):
        m_list = m.split("}}")
        i_list = i.split("}}")
        # make a list of matches (winner, loser)
        match_pairs = []
        for item in m_list:
            if item == "]":
                break
            begin_index = item.find("winner_id")
            end_index = item.find(",\"started")
            substr = item[begin_index:end_index]
            # get winner and loser id
            win_begin_index = substr.find("\":") + 2
            win_end_index = substr.find(",\"")
            winid = substr[win_begin_index:win_end_index]
            los_begin_index = substr.find("loser_id\":") + 10
            losid = substr[los_begin_index:]
            match_pairs.append((winid, losid))
        # make a dictionary of ids {id: username}
        id_pairs = {}
        for item in i_list:
            begin_index = item.find("\"id\"") + 5
            end_index = item.find(",\"tournament")
            id_num = item[begin_index:end_index]
            bi = item.find("\"name\":") + 8
            ei = item.find("\"seed\":") - 2
            name = item[bi:ei]
            name = name.replace(" ", "_")
            # name = name.lower()
            id_pairs[id_num] = name
        # using list of matches, replace ids with usernames
        print("number of participants: %d" % (len(id_pairs) - 1))
        pairs = []
        for match in match_pairs:
            w = id_pairs[match[0]]
            l = id_pairs[match[1]]
            pairs.append((w, l))
        # return pairs
        print("number of matches: %d\n" % len(pairs))
        return pairs

    # returns a list of tuples (winner, loser)
    def get_matches(self, username, api_key, multiple_urls):
        all_match_pairs = []
        with open(multiple_urls) as f:
            for line in f:
                if line[len(line) - 1] == '\n':
                    url = line[:-1] # we don't want the newline char included
                else:
                    url = line
                print("BRACKET: %s" % url)
                t_str = self.parse_link(url)
                matches = self.get_info(username, api_key, url, "/matches.json", t_str)
                ids = self.get_info(username, api_key, url, "/participants.json", t_str)
                matches_str = ""
                for l in matches:
                    matches_str += l.decode('utf-8')
                ids_str = ""
                for l in ids:
                    ids_str += l.decode('utf-8')
                match_pairs = self.parse_matches_ids_strs(matches_str, ids_str)
                print
                for p in match_pairs:
                    all_match_pairs.append(p)
        return all_match_pairs

# TODO: clean for class type
# TODO: don't output a file?
# TODO: do i even need to return something? just change a class variable
class RankingCreator(models.Model):
    def verify_file_exists(self, fstring):
        if os.path.isfile(fstring):
            return True
        else:
            print("%s does NOT exist!") % fstring
            return False

    def match(self, a, b, d):
        aRatingList = []
        aRatingList.append(d[a].rating)
        aDevList = []
        aDevList.append(d[a].rd)
        aBool = []
        aBool.append(1)
        bRatingList = []
        bRatingList.append(d[b].rating)
        bDevList = []
        bDevList.append(d[b].rd)
        bBool = []
        bBool.append(0)
        d[a].update_player(aRatingList, aDevList, aBool)
        d[b].update_player(bRatingList, bDevList, bBool)

    def update_players(self, a, b, d):
        if (a not in d) and (b not in d):
            d[a] = Player()
            d[b] = Player()
            self.match(a, b, d)
        elif (a not in d) and (b in d):
            d[a] = Player()
            self.match(a, b, d)
        elif (a in d) and (b not in d):
            d[b] = Player()
            self.match(a, b, d)
        else:
            self.match(a, b, d)

    # TODO: don't output a file?
    # TODO: do i even need to return something? just change a class variable
    def create_ratings(self, fstring):
        f = open(fstring, 'r')
        i = 1
        d = {}
        for line in f:
            l = line.split()
            self.update_players(l[0], l[1], d)
        return d

    def print_rankings(self, l, d):
        i = 1
        for key in l:
            print("%d.  %s (%.2f, %.2f)" % (i, key[0], key[1], d[key[0]].rd))
            i += 1

# Taken from http://www.glicko.net/glicko.html
class Player(models.Model):
    # Class attribute
    # The system constant, which constrains
    # the change in volatility over time.
    _tau = 0.5

    def getRating(self):
        return (self.__rating * 173.7178) + 1500 

    def setRating(self, rating):
        self.__rating = (rating - 1500) / 173.7178

    rating = property(getRating, setRating)

    def getRd(self):
        return self.__rd * 173.7178

    def setRd(self, rd):
        self.__rd = rd / 173.7178

    rd = property(getRd, setRd)
     
    def __init__(self, rating = 1500, rd = 350, vol = 0.06):
        # For testing purposes, preload the values
        # assigned to an unrated player.
        self.setRating(rating)
        self.setRd(rd)
        self.vol = vol
            
    def _preRatingRD(self):
        """ Calculates and updates the player's rating deviation for the
        beginning of a rating period.
        
        preRatingRD() -> None
        
        """
        self.__rd = math.sqrt(math.pow(self.__rd, 2) + math.pow(self.vol, 2))
        
    def update_player(self, rating_list, RD_list, outcome_list):
        """ Calculates the new rating and rating deviation of the player.
        
        update_player(list[int], list[int], list[bool]) -> None
        
        """
        # Convert the rating and rating deviation values for internal use.
        rating_list = [(x - 1500) / 173.7178 for x in rating_list]
        RD_list = [x / 173.7178 for x in RD_list]

        v = self._v(rating_list, RD_list)
        self.vol = self._newVol(rating_list, RD_list, outcome_list, v)
        self._preRatingRD()
        
        self.__rd = 1 / math.sqrt((1 / math.pow(self.__rd, 2)) + (1 / v))
        
        tempSum = 0
        for i in range(len(rating_list)):
            tempSum += self._g(RD_list[i]) * \
                       (outcome_list[i] - self._E(rating_list[i], RD_list[i]))
        self.__rating += math.pow(self.__rd, 2) * tempSum
        
        
    def _newVol(self, rating_list, RD_list, outcome_list, v):
        """ Calculating the new volatility as per the Glicko2 system.
        
        _newVol(list, list, list) -> float
        
        """
        i = 0
        delta = self._delta(rating_list, RD_list, outcome_list, v)
        a = math.log(math.pow(self.vol, 2))
        tau = self._tau
        x0 = a
        x1 = 0
        
        while x0 != x1:
            # New iteration, so x(i) becomes x(i-1)
            x0 = x1
            d = math.pow(self.__rating, 2) + v + math.exp(x0)
            h1 = -(x0 - a) / math.pow(tau, 2) - 0.5 * math.exp(x0) \
            / d + 0.5 * math.exp(x0) * math.pow(delta / d, 2)
            h2 = -1 / math.pow(tau, 2) - 0.5 * math.exp(x0) * \
            (math.pow(self.__rating, 2) + v) \
            / math.pow(d, 2) + 0.5 * math.pow(delta, 2) * math.exp(x0) \
            * (math.pow(self.__rating, 2) + v - math.exp(x0)) / math.pow(d, 3)
            x1 = x0 - (h1 / h2)

        return math.exp(x1 / 2)
        
    def _delta(self, rating_list, RD_list, outcome_list, v):
        """ The delta function of the Glicko2 system.
        
        _delta(list, list, list) -> float
        
        """
        tempSum = 0
        for i in range(len(rating_list)):
            tempSum += self._g(RD_list[i]) * (outcome_list[i] - self._E(rating_list[i], RD_list[i]))
        return v * tempSum
        
    def _v(self, rating_list, RD_list):
        """ The v function of the Glicko2 system.
        
        _v(list[int], list[int]) -> float
        
        """
        tempSum = 0
        for i in range(len(rating_list)):
            tempE = self._E(rating_list[i], RD_list[i])
            tempSum += math.pow(self._g(RD_list[i]), 2) * tempE * (1 - tempE)
        return 1 / tempSum
        
    def _E(self, p2rating, p2RD):
        """ The Glicko E function.
        
        _E(int) -> float
        
        """
        return 1 / (1 + math.exp(-1 * self._g(p2RD) * \
                                 (self.__rating - p2rating)))
        
    def _g(self, RD):
        """ The Glicko2 g(RD) function.
        
        _g() -> float
        
        """
        return 1 / math.sqrt(1 + 3 * math.pow(RD, 2) / math.pow(math.pi, 2))
        
    def did_not_compete(self):
        """ Applies Step 6 of the algorithm. Use this for
        players who did not compete in the rating period.

        did_not_compete() -> None
        
        """
        self._preRatingRD()
