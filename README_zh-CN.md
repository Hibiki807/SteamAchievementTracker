# SteamAchievementTracker

<div align="center">

[English](./README.md) | **简体中文**

</div>

## 介绍

Python 脚本用于获取 Steam 中的游戏数据，包括游戏时间、玩家的成就、游戏图标和成就图标，最后导出到 outputs 目录下。

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

## 要求

- 获取一个 Steam API token：https://steamcommunity.com/dev
- 拿到你的 Steam 用户 ID
- 已安装 Python 3.12.x

## 使用

Windows:

```bash
git clone https://github.com/Hibiki807/SteamAchievementTracker.git

cd SteamAchievementTracker

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

将先前获取到的 Steam API token 和 Steam 用户 ID 填写到 config.py 中

```python
api_key = "YourKey"
user_id = "YourUserId"
```

运行程序

```bash
.\.venv\Scripts\python main.py
```

## TODOs

- [ ] 展示用的前端示例代码

## 参考资料

- Steam API 文档：https://developer.valvesoftware.com/wiki/Steam_Web_API#Implementations
- Steam Language code 文档：https://partner.steamgames.com/doc/store/localization/languages
