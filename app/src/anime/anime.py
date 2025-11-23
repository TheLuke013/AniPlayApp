class Anime:
    def __init__(self, anime_data: dict):
        self.id = anime_data.get("id", "")
        self.type = anime_data.get("type", "")
        self.title = anime_data.get("name", "")
        self.description = anime_data.get("description", "")
        self.episodes = anime_data.get("episodes", "sub", [])
        self.poster = anime_data.get("poster", "")