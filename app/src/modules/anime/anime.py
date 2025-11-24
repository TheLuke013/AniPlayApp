def convert_anime_data(anime_list):
            converted = []
            for anime in anime_list:
                converted.append({
                    "name": anime.get("name", "Sem título"),
                    "rank": str(anime.get("rank", "N/A")),
                    "status": "Em andamento",
                    "episodes": str(get_episodes(anime)),
                    "poster": anime.get("poster", ""),
                    "id": anime.get("id", ""),
                    "type": anime.get("type", "N/A")
                })
            return converted

def get_episodes(anime):
        if anime.get("episodes"):
            return anime["episodes"]["sub"]
        else:
            return "?"