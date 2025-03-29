import datetime
import math
import threading
import requests
import pandas
import json
import os

from config import *
from log import logger


def get_player_achievements(app_id, language):
    url = f"{base_url}ISteamUserStats/GetPlayerAchievements/v0001/?appid={app_id}&key={api_key}&steamid={user_id}&l={language}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data["playerstats"]["achievements"]
    else:
        return None


def get_achievement_percentages(app_id):
    url = f"{base_url}ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={app_id}&format=json"
    reponse = requests.get(url)

    if reponse.status_code == 200:
        data = reponse.json()
        return data["achievementpercentages"]["achievements"]
    else:
        return None


def get_owned_game():
    url = f"{base_url}IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={user_id}&format=json&include_appinfo=true&include_played_free_games=true"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data["response"]["games"]
    else:
        return None


def get_achievement_icon_urls(app_id):
    url = f"{base_url}ISteamUserStats/GetSchemaForGame/v0002/?key={api_key}&appid={app_id}&l=english&format=json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data["game"]["availableGameStats"]["achievements"]
    else:
        return None


def download_game_icon(game_name, app_id, hash):
    # logger.info(f"{app_id} - Downloading game icon for {game_name} with hash {hash}")

    url = f"http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/{hash}.jpg"
    response = requests.get(url)

    if response.status_code == 200:
        with open(f"outputs/{app_id}/GameIcon.jpg", "wb") as f:
            f.write(response.content)
    else:
        logger.error(f"{app_id} - Failted to fetch game icon for {game_name}")


def download_achievement_icon(game_name, app_id, hashs):
    for hash in hashs:
        # logger.info(f"{app_id} - Downloading achievement icon for {game_name} with {hash}")

        # Check if achievement icon has downloaded
        # TODO: Deprecated achievement icons clean up
        if os.path.exists(f"outputs/{app_id}/AchievementIcons/{hash}.jpg"):
            continue
        if hash is None or len(hash) == 0 or str.isspace(hash):
            logger.warning(f"{app_id} - Achievement icon for {game_name} with hash {hash} is invalid")
            continue

        url = f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/{app_id}/{hash}.jpg"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"outputs/{app_id}/AchievementIcons/{hash}.jpg", "wb") as f:
                f.write(response.content)
        else:
            logger.error(f"{app_id} - Failted to fetch achievement icon for {game_name} with hash {hash}")


def process_games(games):
    for game in games:
        try:
            app_id = game["appid"]
            game_name = game["name"]
            logger.info(f"{app_id} - Processing {game_name}")

            if not os.path.exists(f"outputs/{app_id}"):
                os.mkdir(f"outputs/{app_id}")
            
            logger.info(f"{app_id} - Processing game icon for {game_name}...")
            download_game_icon(game_name, app_id, game["img_icon_url"])

            # Get achievements data. If percentage returns empty, means this game has no achievement
            logger.info(f"{app_id} - Processing achievements data for {game_name}...")
            percentages = get_achievement_percentages(app_id)
            if percentages is None or len(percentages) == 0:
                logger.info(f"{app_id} - No achievements found for {game_name}.")
                continue
            achievements = get_player_achievements(app_id, "english")
            icon_list = get_achievement_icon_urls(app_id)

            # Merge and format achievements data
            pdAchievements = pandas.DataFrame(achievements)
            pdPercentages = pandas.DataFrame(percentages)
            pdIconList = pandas.DataFrame(icon_list)

            pdAP = pandas.merge(pdAchievements, pdPercentages, how="left", left_on="apiname", right_on="name")
            merged = pandas.merge(pdAP, pdIconList, how="left", left_on="apiname", right_on="name")
            merged["iconHash"] = merged["icon"].apply(lambda icon: icon.split("/")[-1].split(".")[0] if isinstance(icon, str) else None)
            merged["icongrayHash"] = merged["icongray"].apply(lambda icongray: icongray.split("/")[-1].split(".")[0] if isinstance(icongray, str) else None)
            merged = merged.drop(columns=["name_x", "name_y", "defaultvalue", "description_y", "icon", "icongray"], errors="ignore")
            merged.rename(columns={"description_x": "description"}, inplace=True, errors="ignore")
            achievement_details = merged.to_dict(orient="records")

            logger.info(f"{app_id} - Found {len(achievement_details)} achievements for {game_name}")

            for language in languages:
                if language == "english":
                    continue
                logger.info(f"{app_id} - Getting achievements data for {game_name} in {language}...")
                achievements_tmp = pandas.DataFrame(get_player_achievements(app_id, language))
                if language in languages_code.keys():
                    merged[f"description_{languages_code[language]}"] = achievements_tmp["description"]
                    merged[f"displayName_{languages_code[language]}"] = achievements_tmp["name"]

            if not os.path.exists(f"outputs/{app_id}/AchievementIcons"):
                os.mkdir(f"outputs/{app_id}/AchievementIcons")

            logger.info(f"{app_id} - Processing achievement icons for {game_name}...")
            icon_hashes = merged["iconHash"].tolist() + merged["icongrayHash"].tolist()
            icon_threading_size = math.ceil(len(icon_hashes) / icon_threading_num)
            splitted_icon_hashes = [icon_hashes[i:i + icon_threading_size] for i in range(0, len(icon_hashes), icon_threading_size)]
            icon_threads = []
            for hashes in splitted_icon_hashes:
                t = threading.Thread(target=download_achievement_icon, args=(game_name, app_id, hashes))
                icon_threads.append(t)
                t.start()
            for t in icon_threads:
                t.join()
            
            merged.to_json(f"outputs/{app_id}/Achievements.json", orient="records", indent=4, force_ascii=False)
            merged.to_csv(f"outputs/{app_id}/Achievements.csv", index=False)

            logger.info(f"{app_id} - Finished getting data for {game_name}")
        except Exception as e:
            logger.error(f"{app_id} - Failed to process game for {game_name}: {e}")


start = datetime.datetime.now()
if not os.path.exists("outputs"):
    os.mkdir("outputs")

# Get all games
logger.info("Getting owned games...")
games = get_owned_game()
games = list(filter(lambda x: x["playtime_forever"] > played_minutes_threshold, games))
games.sort(key=lambda x: x["playtime_forever"], reverse=True)
logger.info(f"Found {len(games)} games played over {played_minutes_threshold} minutes.")

game_threading_size = math.ceil(len(games) / game_threading_num)
splitted_games = [games[i:i + game_threading_size] for i in range(0, len(games), game_threading_size)]
game_threads = []
for s_games in splitted_games:
    t = threading.Thread(target=process_games, args=(s_games,))
    game_threads.append(t)
    t.start()
for t in game_threads:
    t.join()

logger.info(f"Processing games info table.")
games_info = pandas.DataFrame(games)[["appid", "name", "playtime_forever", "img_icon_url", "rtime_last_played"]]

# Check if we have previous data
if os.path.exists(f"outputs/GamesInfo.json"):
    # We use the year as the column name to store the playtime at certain year
    # e.g. games_info[0]["2024"] will return the playtime at 2024
    # This is used to calculate the playtime last year and store your playtime every year
    previous_games_info = pandas.DataFrame(json.load(open(f"outputs/GamesInfo.json", "r", encoding="utf-8")))\
        .drop(columns=["name", "playtime_forever", "img_icon_url", "rtime_last_played"])
    games_info = pandas.merge(games_info, previous_games_info, how="left", on="appid")

current_year = datetime.datetime.now().year
games_info[str(current_year)] = games_info["playtime_forever"]

last_year = current_year - 1
if str(last_year) in games_info.columns:
    games_info["playtime_last_year"] = games_info[str(current_year)] - games_info[str(last_year)]
else:
    games_info["playtime_last_year"] = None

games_info.to_json(f"outputs/GamesInfo.json", orient="records", indent=4, force_ascii=False)
games_info.to_csv(f"outputs/GamesInfo.csv", index=False)

logger.info(f"Finished generate or update {len(games)} games info table.")

end = datetime.datetime.now()
logger.info(f"All Done. Total time: {end - start}")
