def convert_anime_data(anime_list):
            converted = []
            for anime in anime_list:
                converted.append({
                    "title": anime.get("name", "Sem título"),
                    "score": str(anime.get("rank", "N/A")),
                    "status": "Em andamento",
                    "poster": anime.get("poster", ""),
                    "id": anime.get("id", "")
                })
            return converted