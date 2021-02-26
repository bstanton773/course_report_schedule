import os
import arrow
import schedule
import requests
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()
client = WebClient(token=os.getenv('SLACK_BOT_API_KEY'))


class Match:
    @classmethod
    def from_dict(cls, a_dict):
        new_match = cls()
        for key, value in a_dict.items():
            setattr(new_match, key, value)
        return new_match

    def slack_message(self):
        return f'''
Full Name: {self.full_name}
Email: {self.email}
Phone Number: {self.phone_number}
Experience: {self.experience}
Created At: {self.created_at}
        '''


class CourseReportAPI:
    def __init__(self):
        self.base_url = "https://api.coursereport.com"
        self.headers = {
            'Authorization': os.getenv('COURSE_REPORT_API_KEY')
        }

    def _get(self, url, data={}):
        r = requests.get(url, headers=self.headers, data=data)
        response = r.json()
        return response

    def _clean_matches(self, matches):
        clean_matches = []
        for match in matches:
            match_time = match['created_at']
            match_time = match_time.replace('at', '')
            try:
                arrow_time = arrow.get(match_time, 'MMMM DD, YYYY h:mma ZZZ')
            except:
                arrow_time = arrow.get(match_time, 'MMMM DD, YYYY  h:mma ZZZ')
            if arrow_time.to('UTC') > arrow.utcnow().shift(minutes=-35):
                clean_match = Match.from_dict(match)
                clean_matches.append(clean_match)
        return clean_matches

    def get_recent_matches(self):
        url = self.base_url + "/matches"
        now = arrow.now()
        response = self._get(url)
        response_matches = response['matches']
        response_matches = self._clean_matches(response_matches)
        
        return response_matches

def job():
    api = CourseReportAPI()
    matches = api.get_recent_matches()
    if matches:
        send_message(f"There are {len(matches)} new leads:")
        for match in matches:
            send_message(match.slack_message())


def send_message(message):
    try:
        res = client.chat_postMessage(channel="#course_report_leads", text=message)
        assert response["message"]["text"] == message
    except SlackApiError as e:
        assert e.response['ok'] is False


schedule.every(30).minutes.do(job)
while True:
    schedule.run_pending()
    time.sleep(1)
