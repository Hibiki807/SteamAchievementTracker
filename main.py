import datetime
import requests
import pandas
import json
import os

from config import *


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
    print(f"\t\tDownloading game icon for {game_name} with hash {hash}")

    url = f"http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/{hash}.jpg"
    response = requests.get(url)

    if response.status_code == 200:
        with open(f"outputs/{game_name}/GameIcon.jpg", "wb") as f:
            f.write(response.content)
    else:
        print(f"\t\tFailted to fetch game icon for {game_name}")


def download_achievement_icon(game_name, app_id, hashs):
    for hash in hashs:
        print(f"\t\tDownloading achievement icon for {game_name} with {hash}")

        # Check if achievement icon has downloaded
        # TODO: Deprecated achievement icons clean up
        if os.path.exists(f"outputs/{game_name}/AchievementIcons/{hash}.jpg"):
            continue

        url = f"https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/{app_id}/{hash}.jpg"
        response = requests.get(url)

        if response.status_code == 200:
            with open(f"outputs/{game_name}/AchievementIcons/{hash}.jpg", "wb") as f:
                f.write(response.content)
        else:
            print(f"\t\tFailted to fetch achievement icon for {game_name} with hash {hash}")


if not os.path.exists("outputs"):
    os.mkdir("outputs")

# Get all games
print("Getting owned games...")
games = get_owned_game()
games = list(filter(lambda x: x["playtime_forever"] > played_minutes_threshold, games))
games.sort(key=lambda x: x["playtime_forever"], reverse=True)
print(f"Found {len(games)} games played over {played_minutes_threshold} minutes.")

games = games[:2]
for game in games:
    app_id = game["appid"]
    game_name = game["name"]
    print(f"\tProcessing {game_name}")

    if not os.path.exists(f"outputs/{game_name}"):
        os.mkdir(f"outputs/{game_name}")
    
    print(f"\tProcessing game icon for {game_name}...")
    download_game_icon(game_name, app_id, game["img_icon_url"])

    # Get achievements data. If percentage returns empty, means this game has no achievement
    print(f"\tProcessing achievements data for {game_name}...")
    percentages = get_achievement_percentages(app_id)
    if percentages is None or len(percentages) == 0:
        print("\t\tNo achievements found.")
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
    merged = merged.drop(columns=["name_x", "name_y", "defaultvalue", "description_y", "icon", "icongray"])
    merged.rename(columns={"description_x": "description"}, inplace=True)
    achievement_details = merged.to_dict(orient="records")

    print(f"\tFound {len(achievement_details)} achievements for {game_name}")

    for language in languages:
        if language == "english":
            continue
        print(f"\t\tGetting achievements data for {game_name} in {language}...")
        achievements_tmp = pandas.DataFrame(get_player_achievements(app_id, language))
        if language in languages_code.keys():
            merged[f"description_{languages_code[language]}"] = achievements_tmp["description"]
            merged[f"displayName_{languages_code[language]}"] = achievements_tmp["name"]

    if not os.path.exists(f"outputs/{game_name}/AchievementIcons"):
        os.mkdir(f"outputs/{game_name}/AchievementIcons")

    print(f"\tProcessing achievement icons for {game_name}...")
    # TODO: Use threading to make downloading icon faster
    download_achievement_icon(game_name, app_id, merged["iconHash"].tolist() + merged["icongrayHash"].tolist())

    merged.to_json(f"outputs/{game_name}/Achievements.json", orient="records", indent=4, force_ascii=False)
    merged.to_csv(f"outputs/{game_name}/Achievements.csv", index=False)

    print(f"\tFinished getting data for {game_name}\n\n")

games_info = pandas.DataFrame(games)\
    .drop(columns=["has_community_visible_stats", "playtime_windows_forever", "playtime_mac_forever", "playtime_linux_forever", "playtime_deck_forever", "playtime_disconnected", "content_descriptorids"])

# Check if we have previous data
if os.path.exists(f"outputs/GamesInfo.json"):
    # We use the year as the column name to store the playtime at certain year
    # e.g. games_info[0]["2024"] will return the playtime at 2024
    # This is used to calculate the playtime last year and store your playtime every year
    previous_games_info = pandas.DataFrame(json.load(open(f"outputs/GamesInfo.json", "r")))\
        .drop(columns=["name", "playtime_forever", "img_icon_url", "rtime_last_played", "playtime_2weeks"])
    games_info = pandas.merge(games_info, previous_games_info, how="left", on="appid")

current_year = datetime.datetime.now().year
games_info[str(current_year)] = games_info["playtime_forever"]

last_year = current_year - 1
if str(last_year) in games_info.columns:
    games_info["playtime_last_year"] = games_info[str(current_year)] - games_info[str(last_year)]
else:
    games_info["playtime_last_year"] = 0

games_info.to_json(f"outputs/GamesInfo.json", orient="records", indent=4)
games_info.to_csv(f"outputs/GamesInfo.csv", index=False)
