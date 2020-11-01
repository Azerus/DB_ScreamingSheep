from enum import Enum

profanity_ignore_groups = ["загон", "владыка мира нексуса"]
level_system_ignore = ["владыка мира нексуса"]
moderation_groups = ["загон", "владыка мира нексуса"]
non_user_channels = ["заходившие"]
command_channel = ["загон"]
music_channel = ["KozaDJ"]
log_channel = "логи-бота"
PREFIX = "!"
games = ["Heroes of the Storm",
         "Skyrim: Goat Edition",
         "Warcraft 3: Refunded",
         "сыщика",
         "грязные игры"]
watching = ["на тебя!",
            "стрим HappyDerg",
            "Netflix",
            "акции Activision Blizzard",
            "темы на форуме",
            "фильм Паршивая овца"]
special = "трансляцию Blizzcon 2021"
listening = ["Авторадио",
             "Хард Рок",
             "музыку в Spotify",
             "сплетни бабки"]
reaction = ["Коза хочет прописать в табло {}",
            "Коза с подозрением смотрит на {}",
            "Коза бьет по земле копытами и хочет боднуть {}",
            "Коза хочет поорать с {}",
            "Коза выехала на дом к {}",
            "Коза хочет в отпуск подальше от {}",
            "Коза не понимает {}",
            "Коза, одетая в скафандр, парит в открытом космосе и ее крик слышит {}",
            "Коза орет над {}",
            "Коза хочет чтобы {} не беспокоил ее",
            "Коза улетела на орбиту планеты Плутон от {}"]


class MusicStatus(Enum):
    NONE = 1
    DOWNLOADING = 2
    PLAYING = 3
