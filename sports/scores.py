import re
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

from sports import constants, errors


class Match:
    def __init__(self, sport, match_info):
        score = match_info['match_score'].split('-')
        self.sport = sport
        self.home_score = score[0]
        self.away_score = score[1]
        self.match_date = datetime.strptime(match_info['match_date'], '%a, %d %b %Y %H:%M:%S %Z')
        self.raw = match_info

        for key, value in match_info.items():
            if key not in ('match_score', 'match_date'):
                setattr(self, key, value)

    def __repr__(self):
        return '{} {}-{} {}'.format(self.home_team, self.home_score,
                                    self.away_score, self.away_team)

    def __str__(self):
        return '{} {}-{} {}'.format(self.home_team, self.home_score,
                                    self.away_score, self.away_team)


def _load_xml(sport):
    """
    Parse XML file containing match details using ElementTree

    :param sport: sport being played
    :type sport: string
    :return: ElementTree instance containing data from XML file
    :rtyp: ElementTree instance
    """
    try:
        url = 'http://www.scorespro.com/rss2/live-{}.xml'.format(sport)
        r = requests.get(url)
        return ET.fromstring(r.content).find('channel').findall('item')
    except ET.ParseError:
        raise errors.SportError(sport)


def _parse_match_info(match, soccer=False):
    """
    Parse string containing info of a specific match

    :param match: Match data
    :type match: string
    :param soccer: Set to true if match contains soccer data, defaults to False
    :type soccer: bool, optional
    :return: Dictionary containing match information
    :rtype: dict
    """

    match_info = {}

    i_open = match.index('(')
    i_close = match.index(')')
    match_info['league'] = match[i_open + 1:i_close].strip()

    match = match[i_close + 1:]
    i_vs = match.index('vs')
    i_colon = match.index(':')
    match_info['home_team'] = match[0:i_vs].replace('#', ' ').strip()
    match_info['away_team'] = match[i_vs + 2:i_colon].replace('#', ' ').strip()
    match = match[i_colon:]

    if soccer:
        i_hyph = match.index('-')
        match_info['match_score'] = match[1:i_hyph + 2].strip()
        match = match[i_hyph + 1:]
        i_hyph = match.index('-')
        match_info['match_time'] = match[i_hyph + 1:].strip()
    else:
        match_info['match_score'] = match[1:].strip()
        match_info['match_time'] = match.find('description').text.strip()

    match_info['match_date'] = match.find('pubDate').text.strip()
    match_info['match_link'] = match.find('guid').text.strip()

    return match_info


def get_sport_scores(sport):
    """
    Get live scores for all matches in a particular sport

    :param sport: the sport being played
    :type sport: string
    :return: List containing Match objects
    :rtype: list
    """
    sport = sport.lower()
    data = _load_xml(sport)

    matches = []
    for match in data:
        if sport == constants.SOCCER:
            desc = match.find('description').text
            match_info = _parse_match_info(desc, soccer=True)
        else:
            desc = match.find('title').text
            match_info = _parse_match_info(desc)

        matches.append(Match(sport, match_info))

    return matches


def match(sport, team1, team2):
    """
    Get live scores for a single match

    :param sport: the sport being played
    :type sport: string
    :param team1: first team participating in the match
    :ttype team1: string
    :param team2: second team participating in the match
    :type team2: string
    :return: A specific match
    :rtype: Match
    """
    sport = sport.lower()
    team1_pattern = re.compile(team1, re.I)
    team2_pattern = re.compile(team2, re.I)

    matches = get_sport_scores(sport)
    for match in matches:
        if re.search(team1_pattern, match.home_team) or re.search(team1_pattern, match.away_team) \
                and re.search(team2_pattern, match.away_team) or re.search(team2_pattern, match.home_team):
            return match

    raise errors.MatchError(sport, [team1, team2])


def all_matches():
    """
    Get a list of lists containing all live matches.
    Each sport is contained within its own list

    :return: List containing lists of match objects
    :rtype: list
    """
    sports = ['baseball', 'basketball', 'hockey', 'football', 'rugby-union',
              'rugby-league', 'tennis', 'soccer', 'handball', 'volleyball']

    matches = {}
    for sport in sports:
        matches[sport] = get_sport_scores(sport)
    return matches
