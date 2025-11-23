from loguru import logger
from modules.anime.anime_data import get_animes_home_page
import json

class Home():
    def __init__(self, home_layout, create_anime_section):
        home_animes_data = get_animes_home_page()
        spotlight_animes = home_animes_data["data"]["spotlightAnimes"]
        trending_animes = home_animes_data["data"]["trendingAnimes"]
        latest_episode_animes = home_animes_data["data"]["latestEpisodeAnimes"]
        top_uncoming_animes = home_animes_data["data"]["topUpcomingAnimes"]
        top_airing_animes = home_animes_data["data"]["topAiringAnimes"]
        popular_animes = home_animes_data["data"]["mostPopularAnimes"]
        favorite_animes = home_animes_data["data"]["mostFavoriteAnimes"]
        latest_completed_animes = home_animes_data["data"]["latestCompletedAnimes"]
        
        logger.info("✅ Dados dos animes obtidos com sucesso")

        for i in reversed(range(home_layout.count())):
            widget = home_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

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

        spotlight_section = create_anime_section("Animes em Destaque", convert_anime_data(spotlight_animes))
        trending_section = create_anime_section("Animes em Alta", convert_anime_data(trending_animes))
        latest_episode_section = create_anime_section("Último Episódio de Animes", convert_anime_data(latest_episode_animes))
        top_uncoming_section = create_anime_section("Animes Mais aguardados", convert_anime_data(top_uncoming_animes))
        top_airing_section = create_anime_section("Animes Mais Populares em Exibição", convert_anime_data(top_airing_animes))
        popular_section = create_anime_section("Animes Mais populares", convert_anime_data(popular_animes))
        favorite_section = create_anime_section("Animes Mais Favoritados", convert_anime_data(favorite_animes))
        latest_completed_section = create_anime_section("Animes Concluídos Mais Recentes", convert_anime_data(latest_completed_animes))

        home_layout.addWidget(spotlight_section)
        home_layout.addWidget(trending_section)
        home_layout.addWidget(latest_episode_section)
        home_layout.addWidget(top_uncoming_section)
        home_layout.addWidget(top_airing_section)
        home_layout.addWidget(popular_section)
        home_layout.addWidget(favorite_section)
        home_layout.addWidget(latest_completed_section)