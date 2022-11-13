from datetime import datetime, timezone
from typing import Dict, List

import googleapiclient.discovery


class Youtube:
    channel_id = "UCnXVz_l-_r_sLXNe1ESDhHA" # https://www.youtube.com/c/CoffeeStainStudios/
    youtube_base_url = "https://www.youtube.com/watch?v="
    youtube = None

    def __init__(self, token: str):
        self.youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=token)

    def get_videos(self, count: int = 5) -> List[Dict]:
        request = self.youtube.search().list(
            part="snippet",
            channelId=self.channel_id,
            maxResults=count,
            order="date"
        )
        response = request.execute()
        return response.get("items")

    def get_new_videos(self, age: int = 60) -> List[str]:
        videos = self.get_videos()
        result = []
        now = datetime.now(timezone.utc)
        for video in videos:
            video_time_raw = video.get("snippet").get("publishTime")
            video_time = datetime.fromisoformat(video_time_raw[:-1]).astimezone(timezone.utc)
            video_age = now - video_time
            if video_age.total_seconds() / 60 < age:
                video_id = video.get("id").get("videoId")
                result.append("%s%s" % (self.youtube_base_url, video_id))
        return result
