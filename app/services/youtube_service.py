import time

from googleapiclient.discovery import build
from langdetect import detect
from flask import current_app


class YouTubeService:
    """Handles YouTube API interactions for comment scraping and video metadata."""

    @staticmethod
    def get_video_metadata(video_id):
        """Fetch video title, channel name, thumbnail, view count."""
        api_key = current_app.config["YOUTUBE_API_KEY"]
        youtube = build("youtube", "v3", developerKey=api_key)

        request = youtube.videos().list(part="snippet,statistics", id=video_id)
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Video not found: {video_id}")

        item = response["items"][0]
        snippet = item["snippet"]
        stats = item.get("statistics", {})

        return {
            "video_title": snippet.get("title", ""),
            "channel_name": snippet.get("channelTitle", ""),
            "thumbnail_url": snippet.get("thumbnails", {})
            .get("high", {})
            .get("url", ""),
            "view_count": int(stats.get("viewCount", 0)),
        }

    @staticmethod
    def scrape_comments(video_id, max_comments=10, on_progress=None):
        """
        Scrape English-only comments from a YouTube video.
        
        Args:
            video_id: YouTube video ID
            max_comments: Maximum number of comments to fetch
            on_progress: Optional callback(fetched, max_comments) for progress updates
            
        Returns:
            List of comment text strings
        """
        api_key = current_app.config["YOUTUBE_API_KEY"]
        youtube = build("youtube", "v3", developerKey=api_key)
        comments = []
        next_page_token = None

        while len(comments) < max_comments:
            try:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=next_page_token,
                    maxResults=100,
                    textFormat="plainText",
                )
                response = request.execute()
            except Exception as e:
                raise RuntimeError(f"YouTube API error: {e}")

            for item in response.get("items", []):
                if len(comments) >= max_comments:
                    break

                comment = item["snippet"]["topLevelComment"]["snippet"]
                text = comment.get("textDisplay", "").strip()

                if not text:
                    continue

                # Filter English-only comments
                try:
                    if detect(text) != "en":
                        continue
                except Exception:
                    continue

                comments.append(text)

            # Report progress
            if on_progress:
                on_progress(len(comments), max_comments)

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

            time.sleep(0.3)  # Respect YouTube API rate limits

        return comments
