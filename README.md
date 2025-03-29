# SteamAchievementTracker

<div align="center">
**[English]** | [简体中文](./README_zh-CN.md)
</div>

## Introduction

A Python script to get game data from Steam, including game time, player achievements, game icons and achievement icons. And finally export to the outputs directory.

```
outputs
│   GamesInfo.csv
│   GamesInfo.json
│
└───{app_id}
│   │   GameIcon.jpg
│   │   Achievements.csv
|   |   Achievements.json
│   │
│   └───AchievementIcons
│       │   {icon_hash}.jpg
│       │   ...
```

## Prerequisite

- You need a Steam API token：https://steamcommunity.com/dev
- Get your Steam User ID
- Install Python 3.12.x

## How to use

Windows:

```bash
git clone https://github.com/Hibiki807/SteamAchievementTracker.git

cd SteamAchievementTracker

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Fill your Steam API token and Steam User ID into config.py

```python
api_key = "YourKey"
user_id = "YourUserId"
```

Run

```bash
.\.venv\Scripts\python main.py
```

## TODOs

- [ ] Frontend sample code for display

## Reference

- Steam API doc：https://developer.valvesoftware.com/wiki/Steam_Web_API#Implementations
- Steam Language code doc：https://developer.valvesoftware.com/wiki/Steam_Condenser
