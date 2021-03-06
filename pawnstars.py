import json
import requests
from enum import Enum


# Only have all query prototypes finished for games endpoint
class Endpoints(Enum):
    GAMES = "games"
    TEAMS = "teams"
    PERSONS = "persons"
    ACHIEVEMENTS = "achievements"
    CURRENT_WEEK = "currentWeek"
    PGS = "playerGameStats"
    PTS = "playerTeamStats"
    SPTS = "seasonPlayerTeamStats"
    PCS = "prospectCombineStats"
    DRAFTS = "drafts"
    LISTS = "lists"
    VIDEOS = "videos"
    ARTICLES = "articles"
    SCORE_FEED = "score-feed"


# Will use this object for fetching play by play data
class PlayByPlay(object):
    def __init__(self):
        super().__init__()


# will use this object for fetching next gen stats
class NextGenStats(object):
    def __init__(self):
        super().__init__()


class ApiWrapper(object):
    def __init__(self, **kwargs):
        super().__init__()
        if 'endpt_root' in kwargs.keys():
            self.endpt_root = kwargs.get('endpt_root') + "/"
        else:
            self.endpt_root = "v1/"
        self.base_api_endpt = "https://api.nfl.com/" + self.endpt_root
        self.token_api_endpt = "https://api.nfl.com/v1/reroute"
        self.token_req_headers = \
            {"Host": "api.nfl.com",
             "User-Agent": "PawnStar - Python API Wrapper for NFL Statistics and Related Subject-matter",
             "Accept": "*/*",
             "Accept-Language": "en-US,en;q=0.5",
             "Accept-Encoding": "gzip, deflate, br",
             "Referer": "https://www.nfl.com/",
             "Content-Type": "application/x-www-form-urlencoded",
             "X-Domain-Id": "100",
             "Origin": "https://www.nfl.com",
             "Content-Length": "29",
             "Connection": "keep-alive",
             "TE": "Trailers",
             "Pragma": "no-cache",
             "Cache-Control": "no-cache"}
        self.token_req_body = "grant_type=client_credentials"
        self.access_token = {}
        self.api_req_headers = {"Content-Type": "application/json"}

    def request_new_token(self):
        self.access_token.clear()
        req = requests.post(self.token_api_endpt, headers=self.token_req_headers, data=self.token_req_body)
        if req.status_code == 200:
            self.access_token.update(json.loads(req.text))
        else:
            raise InvalidTokenException

    # Using positional arg for prototype differentiation
    # Still very basic, no field selection or logical operator selection
    # Couldn't get this to work using {}.format() method due to curly braces, may be refactored later
    @staticmethod
    def build_query(prototype, endpoint, qp):
        if endpoint == "games":
            if prototype == "week":
                return '{"$query":{"week.season":' + qp[0] + ',"week.seasonType":' + "\"" + qp[1] + "\"" + ',"week.week":' \
                    + qp[2] + '}}&fs={week{season,seasonType,week},id,gameTime,gameStatus,homeTeam{id,abbr},' \
                    'visitorTeam{id,abbr},homeTeamScore,visitorTeamScore}'
            elif prototype == "week_type":
                return '{"$query":{"week.weekType":' + "\"" + qp[0] + "\"" + \
                    '},"$take":10,"$skip":0}&fs={week{season,seasonType,week},id,gameTime,gameStatus,homeTeam' \
                    '{id,abbr},visitorTeam{id,abbr},homeTeamScore,visitorTeamScore}'
            elif prototype == "team":
                return '{"$query":{"week.season":' + qp[0] + ',"$or":[{"homeTeam.abbr":' + "\"" + qp[1] + "\"" + \
                    '},{"visitorTeam.abbr":' + "\"" + qp[2] + "\"" + \
                    '}]}}&fs={week{season,seasonType,week},homeTeam{id,abbr},visitorTeam' \
                    '{id,abbr},homeTeamScore,visitorTeamScore,gameStatus,homeTeamScore,visitorTeamScore}'
            elif prototype == "historical":
                return '{"$query":{"$or":[{"visitorTeam.abbr":' + "\"" + qp[0] + "\"" + \
                    ',"homeTeam.abbr":' + "\"" + qp[1] + "\"" + '},{"homeTeam.abbr":' + "\"" + qp[2] + "\"" + \
                    ',"visitorTeam.abbr":' + "\"" + qp[3] + "\"" + '}]},"$sort":{"gameTime":1},"$take":10}&fs=' \
                    '{id,type,week{season,seasonType,name,week},id,gameTime,gameStatus,homeTeam{id,type,abbr}' \
                    ',visitorTeam{id,type,abbr},homeTeamScore,visitorTeamScore}'

    def api_request(self, endpoint, **kwargs):
        if endpoint not in Endpoints:
            raise InvalidEndpointException
        if endpoint == Endpoints.SCORE_FEED:
            req = requests.get('https://feeds.nfl.com/feeds-rs/scores.json')
            return json.loads(req.text)
        if 'prototype' in kwargs.keys():
            prototype = kwargs.get("prototype")
        else:
            prototype = ''
        if 'qp' in kwargs.keys():
            qp = kwargs.get('qp')
        else:
            qp = ''
        endpoint = endpoint.value
        if 'raw_query' in kwargs.keys():
            query = kwargs.get('raw_query')
        else:
            query = self.build_query(prototype, endpoint, qp)
        if self.access_token == {}:
            self.request_new_token()
            print("\nFetched new token {}\n".format(self.access_token['access_token']))
        if "Authorization" not in self.api_req_headers:
            self.api_req_headers.update({"Authorization": "Bearer " + self.access_token['access_token']})
        req = requests.get(self.base_api_endpt + endpoint + "?s=" + query, headers=self.api_req_headers)
        if req.status_code == 401:
            print("Token {} is expired.. Fetching a new one!\n".format(self.access_token['access_token']))
            self.request_new_token()
        elif req.status_code == 500 or req.status_code == 400 or req.status_code == 404:
            raise MalformedApiRequest
        else:
            return json.loads(req.text)


class InvalidTokenException(Exception):
    """The token request returned a non 200 status code, wait a few seconds and try again"""
    pass


class MalformedApiRequest(Exception):
    """The API request wasn't understood by the server or the requested API endpoint doesn't exist!"""
    pass


class InvalidEndpointException(Exception):
    """The specified endpoint must exist in the Endpoints enum!"""
    pass

