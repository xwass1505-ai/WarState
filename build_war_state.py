#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WAR STATE - one-command project generator (Python -> files -> Rojo -> Roblox Studio)

    python build_war_state.py                 # generate/update, validate, test, rojo build, rojo serve
    python build_war_state.py --no-serve      # same, but do not start live sync
    python build_war_state.py --no-rojo       # generate + tests only (Rojo not installed)
    python build_war_state.py --check-only    # write nothing; validate existing files, test, rojo build
    python build_war_state.py --install-plugin  # also build the optional Studio bridge plugin
    python build_war_state.py --force         # overwrite files you edited by hand (backups are kept)

Standard library only. Requires Python 3.8+ and Rojo 7.x (https://rojo.space) on PATH.
This single file contains every generated source file, so it can recreate the project in an empty folder.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import http.server
import json
import os
import platform
import queue
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

GENERATOR_VERSION = "0.1.0"
PROJECT_NAME = "War State"
ROJO_PORT = 34872
BRIDGE_PORT = 34873
MIN_PYTHON = (3, 8)
CURRENT_PHASE = "Phase 1 - First playable foundation"

# ---------------------------------------------------------------------------
# COUNTRY REGISTRY: 195 sovereign states (193 UN members + Holy See + State of Palestine)
# (Id = ISO 3166-1 alpha-2, DisplayNameEN, DisplayNameRU, Continent)
# ---------------------------------------------------------------------------
CONTINENTS = ["Europe", "Asia", "Africa", "North America", "South America", "Oceania"]

COUNTRIES = [
    # Europe (45)
    ("AL", "Albania", "Албания", "Europe"),
    ("AD", "Andorra", "Андорра", "Europe"),
    ("AT", "Austria", "Австрия", "Europe"),
    ("BY", "Belarus", "Беларусь", "Europe"),
    ("BE", "Belgium", "Бельгия", "Europe"),
    ("BA", "Bosnia and Herzegovina", "Босния и Герцеговина", "Europe"),
    ("BG", "Bulgaria", "Болгария", "Europe"),
    ("HR", "Croatia", "Хорватия", "Europe"),
    ("CY", "Cyprus", "Кипр", "Europe"),
    ("CZ", "Czechia", "Чехия", "Europe"),
    ("DK", "Denmark", "Дания", "Europe"),
    ("EE", "Estonia", "Эстония", "Europe"),
    ("FI", "Finland", "Финляндия", "Europe"),
    ("FR", "France", "Франция", "Europe"),
    ("DE", "Germany", "Германия", "Europe"),
    ("GR", "Greece", "Греция", "Europe"),
    ("HU", "Hungary", "Венгрия", "Europe"),
    ("IS", "Iceland", "Исландия", "Europe"),
    ("IE", "Ireland", "Ирландия", "Europe"),
    ("IT", "Italy", "Италия", "Europe"),
    ("LV", "Latvia", "Латвия", "Europe"),
    ("LI", "Liechtenstein", "Лихтенштейн", "Europe"),
    ("LT", "Lithuania", "Литва", "Europe"),
    ("LU", "Luxembourg", "Люксембург", "Europe"),
    ("MT", "Malta", "Мальта", "Europe"),
    ("MD", "Moldova", "Молдова", "Europe"),
    ("MC", "Monaco", "Монако", "Europe"),
    ("ME", "Montenegro", "Черногория", "Europe"),
    ("NL", "Netherlands", "Нидерланды", "Europe"),
    ("MK", "North Macedonia", "Северная Македония", "Europe"),
    ("NO", "Norway", "Норвегия", "Europe"),
    ("PL", "Poland", "Польша", "Europe"),
    ("PT", "Portugal", "Португалия", "Europe"),
    ("RO", "Romania", "Румыния", "Europe"),
    ("RU", "Russia", "Россия", "Europe"),
    ("SM", "San Marino", "Сан-Марино", "Europe"),
    ("RS", "Serbia", "Сербия", "Europe"),
    ("SK", "Slovakia", "Словакия", "Europe"),
    ("SI", "Slovenia", "Словения", "Europe"),
    ("ES", "Spain", "Испания", "Europe"),
    ("SE", "Sweden", "Швеция", "Europe"),
    ("CH", "Switzerland", "Швейцария", "Europe"),
    ("UA", "Ukraine", "Украина", "Europe"),
    ("GB", "United Kingdom", "Великобритания", "Europe"),
    ("VA", "Holy See (Vatican City)", "Ватикан", "Europe"),
    # Asia (47)
    ("AF", "Afghanistan", "Афганистан", "Asia"),
    ("AM", "Armenia", "Армения", "Asia"),
    ("AZ", "Azerbaijan", "Азербайджан", "Asia"),
    ("BH", "Bahrain", "Бахрейн", "Asia"),
    ("BD", "Bangladesh", "Бангладеш", "Asia"),
    ("BT", "Bhutan", "Бутан", "Asia"),
    ("BN", "Brunei", "Бруней", "Asia"),
    ("KH", "Cambodia", "Камбоджа", "Asia"),
    ("CN", "China", "Китай", "Asia"),
    ("GE", "Georgia", "Грузия", "Asia"),
    ("IN", "India", "Индия", "Asia"),
    ("ID", "Indonesia", "Индонезия", "Asia"),
    ("IR", "Iran", "Иран", "Asia"),
    ("IQ", "Iraq", "Ирак", "Asia"),
    ("IL", "Israel", "Израиль", "Asia"),
    ("JP", "Japan", "Япония", "Asia"),
    ("JO", "Jordan", "Иордания", "Asia"),
    ("KZ", "Kazakhstan", "Казахстан", "Asia"),
    ("KW", "Kuwait", "Кувейт", "Asia"),
    ("KG", "Kyrgyzstan", "Киргизия", "Asia"),
    ("LA", "Laos", "Лаос", "Asia"),
    ("LB", "Lebanon", "Ливан", "Asia"),
    ("MY", "Malaysia", "Малайзия", "Asia"),
    ("MV", "Maldives", "Мальдивы", "Asia"),
    ("MN", "Mongolia", "Монголия", "Asia"),
    ("MM", "Myanmar", "Мьянма", "Asia"),
    ("NP", "Nepal", "Непал", "Asia"),
    ("KP", "North Korea", "КНДР", "Asia"),
    ("OM", "Oman", "Оман", "Asia"),
    ("PK", "Pakistan", "Пакистан", "Asia"),
    ("PS", "State of Palestine", "Государство Палестина", "Asia"),
    ("PH", "Philippines", "Филиппины", "Asia"),
    ("QA", "Qatar", "Катар", "Asia"),
    ("SA", "Saudi Arabia", "Саудовская Аравия", "Asia"),
    ("SG", "Singapore", "Сингапур", "Asia"),
    ("KR", "South Korea", "Республика Корея", "Asia"),
    ("LK", "Sri Lanka", "Шри-Ланка", "Asia"),
    ("SY", "Syria", "Сирия", "Asia"),
    ("TJ", "Tajikistan", "Таджикистан", "Asia"),
    ("TH", "Thailand", "Таиланд", "Asia"),
    ("TL", "Timor-Leste", "Восточный Тимор", "Asia"),
    ("TR", "Turkey", "Турция", "Asia"),
    ("TM", "Turkmenistan", "Туркменистан", "Asia"),
    ("AE", "United Arab Emirates", "ОАЭ", "Asia"),
    ("UZ", "Uzbekistan", "Узбекистан", "Asia"),
    ("VN", "Vietnam", "Вьетнам", "Asia"),
    ("YE", "Yemen", "Йемен", "Asia"),
    # Africa (54)
    ("DZ", "Algeria", "Алжир", "Africa"),
    ("AO", "Angola", "Ангола", "Africa"),
    ("BJ", "Benin", "Бенин", "Africa"),
    ("BW", "Botswana", "Ботсвана", "Africa"),
    ("BF", "Burkina Faso", "Буркина-Фасо", "Africa"),
    ("BI", "Burundi", "Бурунди", "Africa"),
    ("CV", "Cabo Verde", "Кабо-Верде", "Africa"),
    ("CM", "Cameroon", "Камерун", "Africa"),
    ("CF", "Central African Republic", "Центральноафриканская Республика", "Africa"),
    ("TD", "Chad", "Чад", "Africa"),
    ("KM", "Comoros", "Коморы", "Africa"),
    ("CG", "Republic of the Congo", "Республика Конго", "Africa"),
    ("CD", "DR Congo", "ДР Конго", "Africa"),
    ("CI", "Cote d'Ivoire", "Кот-д'Ивуар", "Africa"),
    ("DJ", "Djibouti", "Джибути", "Africa"),
    ("EG", "Egypt", "Египет", "Africa"),
    ("GQ", "Equatorial Guinea", "Экваториальная Гвинея", "Africa"),
    ("ER", "Eritrea", "Эритрея", "Africa"),
    ("SZ", "Eswatini", "Эсватини", "Africa"),
    ("ET", "Ethiopia", "Эфиопия", "Africa"),
    ("GA", "Gabon", "Габон", "Africa"),
    ("GM", "Gambia", "Гамбия", "Africa"),
    ("GH", "Ghana", "Гана", "Africa"),
    ("GN", "Guinea", "Гвинея", "Africa"),
    ("GW", "Guinea-Bissau", "Гвинея-Бисау", "Africa"),
    ("KE", "Kenya", "Кения", "Africa"),
    ("LS", "Lesotho", "Лесото", "Africa"),
    ("LR", "Liberia", "Либерия", "Africa"),
    ("LY", "Libya", "Ливия", "Africa"),
    ("MG", "Madagascar", "Мадагаскар", "Africa"),
    ("MW", "Malawi", "Малави", "Africa"),
    ("ML", "Mali", "Мали", "Africa"),
    ("MR", "Mauritania", "Мавритания", "Africa"),
    ("MU", "Mauritius", "Маврикий", "Africa"),
    ("MA", "Morocco", "Марокко", "Africa"),
    ("MZ", "Mozambique", "Мозамбик", "Africa"),
    ("NA", "Namibia", "Намибия", "Africa"),
    ("NE", "Niger", "Нигер", "Africa"),
    ("NG", "Nigeria", "Нигерия", "Africa"),
    ("RW", "Rwanda", "Руанда", "Africa"),
    ("ST", "Sao Tome and Principe", "Сан-Томе и Принсипи", "Africa"),
    ("SN", "Senegal", "Сенегал", "Africa"),
    ("SC", "Seychelles", "Сейшельские Острова", "Africa"),
    ("SL", "Sierra Leone", "Сьерра-Леоне", "Africa"),
    ("SO", "Somalia", "Сомали", "Africa"),
    ("ZA", "South Africa", "ЮАР", "Africa"),
    ("SS", "South Sudan", "Южный Судан", "Africa"),
    ("SD", "Sudan", "Судан", "Africa"),
    ("TZ", "Tanzania", "Танзания", "Africa"),
    ("TG", "Togo", "Того", "Africa"),
    ("TN", "Tunisia", "Тунис", "Africa"),
    ("UG", "Uganda", "Уганда", "Africa"),
    ("ZM", "Zambia", "Замбия", "Africa"),
    ("ZW", "Zimbabwe", "Зимбабве", "Africa"),
    # North America (23)
    ("AG", "Antigua and Barbuda", "Антигуа и Барбуда", "North America"),
    ("BS", "Bahamas", "Багамские Острова", "North America"),
    ("BB", "Barbados", "Барбадос", "North America"),
    ("BZ", "Belize", "Белиз", "North America"),
    ("CA", "Canada", "Канада", "North America"),
    ("CR", "Costa Rica", "Коста-Рика", "North America"),
    ("CU", "Cuba", "Куба", "North America"),
    ("DM", "Dominica", "Доминика", "North America"),
    ("DO", "Dominican Republic", "Доминиканская Республика", "North America"),
    ("SV", "El Salvador", "Сальвадор", "North America"),
    ("GD", "Grenada", "Гренада", "North America"),
    ("GT", "Guatemala", "Гватемала", "North America"),
    ("HT", "Haiti", "Гаити", "North America"),
    ("HN", "Honduras", "Гондурас", "North America"),
    ("JM", "Jamaica", "Ямайка", "North America"),
    ("MX", "Mexico", "Мексика", "North America"),
    ("NI", "Nicaragua", "Никарагуа", "North America"),
    ("PA", "Panama", "Панама", "North America"),
    ("KN", "Saint Kitts and Nevis", "Сент-Китс и Невис", "North America"),
    ("LC", "Saint Lucia", "Сент-Люсия", "North America"),
    ("VC", "Saint Vincent and the Grenadines", "Сент-Винсент и Гренадины", "North America"),
    ("TT", "Trinidad and Tobago", "Тринидад и Тобаго", "North America"),
    ("US", "United States", "США", "North America"),
    # South America (12)
    ("AR", "Argentina", "Аргентина", "South America"),
    ("BO", "Bolivia", "Боливия", "South America"),
    ("BR", "Brazil", "Бразилия", "South America"),
    ("CL", "Chile", "Чили", "South America"),
    ("CO", "Colombia", "Колумбия", "South America"),
    ("EC", "Ecuador", "Эквадор", "South America"),
    ("GY", "Guyana", "Гайана", "South America"),
    ("PY", "Paraguay", "Парагвай", "South America"),
    ("PE", "Peru", "Перу", "South America"),
    ("SR", "Suriname", "Суринам", "South America"),
    ("UY", "Uruguay", "Уругвай", "South America"),
    ("VE", "Venezuela", "Венесуэла", "South America"),
    # Oceania (14)
    ("AU", "Australia", "Австралия", "Oceania"),
    ("FJ", "Fiji", "Фиджи", "Oceania"),
    ("KI", "Kiribati", "Кирибати", "Oceania"),
    ("MH", "Marshall Islands", "Маршалловы Острова", "Oceania"),
    ("FM", "Micronesia", "Микронезия", "Oceania"),
    ("NR", "Nauru", "Науру", "Oceania"),
    ("NZ", "New Zealand", "Новая Зеландия", "Oceania"),
    ("PW", "Palau", "Палау", "Oceania"),
    ("PG", "Papua New Guinea", "Папуа - Новая Гвинея", "Oceania"),
    ("WS", "Samoa", "Самоа", "Oceania"),
    ("SB", "Solomon Islands", "Соломоновы Острова", "Oceania"),
    ("TO", "Tonga", "Тонга", "Oceania"),
    ("TV", "Tuvalu", "Тувалу", "Oceania"),
    ("VU", "Vanuatu", "Вануату", "Oceania"),
]

EXPECTED_CONTINENT_COUNTS = {
    "Europe": 45,
    "Asia": 47,
    "Africa": 54,
    "North America": 23,
    "South America": 12,
    "Oceania": 14,
}

# Real flag assets: ONLY add verified Roblox asset ids here ("rbxassetid://<id>").
# Never invent ids. Empty -> EmojiFallback is used in the UI.
REAL_FLAG_ASSETS: dict = {}


def emoji_flag(iso2: str) -> str:
    return "".join(chr(0x1F1E6 + ord(ch) - ord("A")) for ch in iso2.upper())


def country_registry() -> dict:
    countries = []
    for iso, en, ru, continent in COUNTRIES:
        countries.append(
            {
                "Id": iso,
                "Iso2": iso,
                "DisplayNameEN": en,
                "DisplayNameRU": ru,
                "Continent": continent,
                "FlagAsset": REAL_FLAG_ASSETS.get(iso, ""),
                "EmojiFallback": emoji_flag(iso),
            }
        )
    return {
        "RegistryVersion": 1,
        "Continents": CONTINENTS,
        "ExpectedContinentCounts": EXPECTED_CONTINENT_COUNTS,
        "Countries": countries,
    }


# ---------------------------------------------------------------------------
# CONFIGURATION (written as JSON; Rojo turns *.json into ModuleScripts returning the table)
# ---------------------------------------------------------------------------
GAME_CONFIG = {
    "SchemaVersion": 1,
    "DataStoreName": "WarState_Slots_v1",
    "DataStoreRetries": 3,
    "AutosaveSeconds": 60,
    "SlotCount": 3,
    "Slots": [
        {"Index": 1, "Unlocked": True, "Label": "FREE"},
        {"Index": 2, "Unlocked": False, "Label": "LOCKED"},
        {"Index": 3, "Unlocked": False, "Label": "LOCKED"},
    ],
    "CountryName": {"MinLength": 3, "MaxLength": 24},
    "Territory": {
        "Size": 480,
        "Spacing": 640,
        "OriginX": 2000,
        "OriginZ": 0,
        "SurfaceY": 0,
        "Thickness": 4,
        "MaxPlots": 12,
        "BorderWidth": 2,
        "Color": [0.45, 0.68, 0.38],
        "BorderColor": [0.38, 0.6, 0.33],
    },
    "Population": {"TickSeconds": 4, "GrowthFraction": 0.15, "MinGrowth": 1, "WorkerRatio": 0.5},
    "Construction": {
        "PlannedSeconds": 2,
        "TickSeconds": 0.5,
        "GhostTransparency": 0.8,
        "ProgressBarMaxDistance": 160,
    },
    "EmptyCountry": {
        "Money": 0,
        "Oil": 0,
        "Fuel": 0,
        "Steel": 0,
        "Supplies": 0,
        "Population": 0,
        "Workers": 0,
        "HousingCapacity": 0,
        "Buildings": {},
        "Roads": {},
        "Military": {},
    },
}

PLACEMENT_CONFIG = {
    "GridSize": 4,
    "RoadTileSize": 8,
    "MaxRoadDistance": 20,
    "RequireRoadAccess": True,
    "OverlapTolerance": 0.05,
    "MaxPlacementRayDistance": 1000,
    "PreviewTransparency": 0.35,
    "PreviewInvalidColor": [235, 90, 90],
    "RequestCooldown": 0.15,
}

BUILDING_CONFIG = {
    "Buildings": [
        {
            "Id": "SmallHouse",
            "DisplayName": "Small House",
            "Category": "Housing",
            "Footprint": [8, 8],
            "HousingCapacity": 4,
            "BuildTimeSeconds": 12,
            "Variants": ["SmallHouse_A", "SmallHouse_B", "SmallHouse_C", "SmallHouse_D"],
            "Active": True,
        },
        {
            "Id": "MediumHouse",
            "DisplayName": "Medium House",
            "Category": "Housing",
            "Footprint": [12, 8],
            "HousingCapacity": 8,
            "BuildTimeSeconds": 20,
            "Variants": ["MediumHouse_A", "MediumHouse_B", "MediumHouse_C", "MediumHouse_D"],
            "Active": True,
        },
        {
            "Id": "LargeHouse",
            "DisplayName": "Large House",
            "Category": "Housing",
            "Footprint": [16, 12],
            "HousingCapacity": 14,
            "BuildTimeSeconds": 30,
            "Variants": ["LargeHouse_A", "LargeHouse_B", "LargeHouse_C", "LargeHouse_D"],
            "Active": True,
        },
    ]
}

ROAD_CONFIG = {
    "TileSize": 8,
    "RoadWidth": 6,
    "Colors": {"Asphalt": [74, 78, 86], "Sidewalk": [200, 202, 204], "Marking": [240, 240, 236]},
    "Types": [
        {"Id": "Straight", "DisplayName": "Straight", "Openings": ["N", "S"], "Active": True},
        {"Id": "Corner", "DisplayName": "Corner", "Openings": ["N", "E"], "Active": True},
        {"Id": "TJunction", "DisplayName": "T-Junction", "Openings": ["N", "E", "W"], "Active": True},
        {"Id": "Crossroad", "DisplayName": "Crossroad", "Openings": ["N", "E", "S", "W"], "Active": True},
    ],
}

BUILD_MENU_CONFIG = {
    "Categories": [
        {"Id": "Roads", "DisplayName": "Roads", "Status": "IMPLEMENTED"},
        {"Id": "Housing", "DisplayName": "Housing", "Status": "IMPLEMENTED"},
        {"Id": "Services", "DisplayName": "Services", "Status": "PLANNED"},
        {"Id": "Commercial", "DisplayName": "Commercial", "Status": "PLANNED"},
        {"Id": "Agriculture", "DisplayName": "Agriculture", "Status": "PLANNED"},
        {"Id": "Resources", "DisplayName": "Resources", "Status": "PLANNED"},
        {"Id": "Industrial", "DisplayName": "Industrial", "Status": "PLANNED"},
        {"Id": "Other", "DisplayName": "Other", "Status": "PLANNED"},
    ]
}

TECHNOLOGY_CONFIG = {
    "Branches": [
        {
            "Id": "USSR",
            "DisplayName": "USSR / Russia",
            "Description": "Soviet / Russian equipment line. Research tree planned.",
            "Active": True,
        },
        {
            "Id": "USA",
            "DisplayName": "USA",
            "Description": "American equipment line. Research tree planned.",
            "Active": True,
        },
        {
            "Id": "Germany",
            "DisplayName": "Germany",
            "Description": "German equipment line. Research tree planned.",
            "Active": True,
        },
    ],
    "ResearchSystemStatus": "PLANNED",
}

REMOTE_FUNCTIONS = [
    ("GetProfile", "Returns the 3 slot summaries and persistence mode"),
    ("CreateCountry", "(slotIndex, {Name, FlagId, Continent, TechnologyBranch}) -> server validates and creates"),
    ("LoadSlot", "(slotIndex) loads a saved country into the world"),
    ("DeleteSlot", "(slotIndex) deletes a saved country (two-tap confirm on client)"),
    ("LeaveState", "Saves and unloads the active country (back to slot screen)"),
    ("SaveNow", "Forces a save of the active slot"),
    ("PlaceRoad", "({Type, X, Z, Rotation}) server snaps + validates + builds road"),
    ("PlaceBuilding", "({Type, Variant, X, Z, Rotation}) server snaps + validates + starts construction"),
]
REMOTE_EVENTS = [
    ("StateChanged", "Server -> client authoritative country snapshot"),
    ("Notify", "Server -> client toast message"),
]

SERVICES = ["ReplicatedStorage", "ServerScriptService", "StarterPlayer", "StarterGui", "Workspace"]
WORKSPACE_FOLDERS = ["Map", "Buildings", "Roads", "Vehicles", "NPCs"]

REQUIRED_DIRS = [
    "src/ReplicatedStorage/Shared/Config",
    "src/ReplicatedStorage/Shared/Constants",
    "src/ReplicatedStorage/Shared/Types",
    "src/ReplicatedStorage/Shared/Modules",
    "src/ReplicatedStorage/Assets",
    "src/ServerScriptService/Systems/Data",
    "src/ServerScriptService/Systems/Buildings",
    "src/ServerScriptService/Systems/Construction",
    "src/ServerScriptService/Systems/Population",
    "src/ServerScriptService/Systems/Roads",
    "src/ServerScriptService/Systems/Resources",
    "src/ServerScriptService/Systems/Research",
    "src/ServerScriptService/Systems/Production",
    "src/ServerScriptService/Systems/Economy",
    "src/ServerScriptService/Systems/Military",
    "src/ServerScriptService/Systems/Military/Future",
    "src/ServerScriptService/Systems/Country",
    "src/ServerScriptService/Systems/World",
    "src/ServerScriptService/Tests",
    "src/StarterPlayer/StarterPlayerScripts/Controllers",
    "src/StarterGui/MainUI/Components",
    "src/StarterGui/MainUI/Screens",
    "src/Workspace/Map",
    "src/Workspace/Buildings",
    "src/Workspace/Roads",
    "src/Workspace/Vehicles",
    "src/Workspace/NPCs",
    "plugin",
    "tests",
]

# ---------------------------------------------------------------------------
# LUAU STATIC CHECKER (heuristic). Single source: used by the build AND written to tests/luau_static.py
# It strips comments/strings, checks bracket balance, block balance (function/if/do/repeat vs end/until),
# ModuleScript trailing return, and obvious non-Luau tokens. It is NOT a full Luau parser.
# ---------------------------------------------------------------------------
LUAU_CHECKER_SOURCE = r'''
import re

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def strip_luau(src):
    """Remove comments and string contents. Keeps newlines so line numbers stay valid."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if src.startswith("--", i):
            m = re.match(r"--\[(=*)\[", src[i:])
            if m:
                close = "]" + m.group(1) + "]"
                end = src.find(close, i + len(m.group(0)))
                if end == -1:
                    raise ValueError("unterminated block comment")
                out.append("\n" * src.count("\n", i, end))
                i = end + len(close)
                continue
            end = src.find("\n", i)
            if end == -1:
                break
            i = end
            continue
        m = re.match(r"\[(=*)\[", src[i:]) if ch == "[" else None
        if m:
            close = "]" + m.group(1) + "]"
            end = src.find(close, i + len(m.group(0)))
            if end == -1:
                raise ValueError("unterminated long string")
            out.append('""' + "\n" * src.count("\n", i, end))
            i = end + len(close)
            continue
        if ch in "\"'`":
            quote = ch
            j = i + 1
            while j < n and src[j] != quote:
                if src[j] == "\\":
                    j += 1
                elif src[j] == "\n":
                    raise ValueError("unterminated string on line %d" % (src.count("\n", 0, i) + 1))
                j += 1
            if j >= n:
                raise ValueError("unterminated string")
            out.append('""')
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def check_luau(src, is_module):
    """Returns a list of error strings (empty = OK)."""
    errors = []
    try:
        code = strip_luau(src)
    except ValueError as exc:
        return [str(exc)]
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for lineno, line in enumerate(code.split("\n"), 1):
        for ch in line:
            if ch in "([{":
                stack.append((ch, lineno))
            elif ch in ")]}":
                if not stack or stack[-1][0] != pairs[ch]:
                    errors.append("unbalanced '%s' on line %d" % (ch, lineno))
                    return errors
                stack.pop()
    if stack:
        errors.append("unclosed '%s' from line %d" % stack[-1])
        return errors

    tokens = []
    for lineno, line in enumerate(code.split("\n"), 1):
        for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*|\"\"|\d[\w.]*|\.\.\.|==|~=|<=|>=|!=|//=|\.\.=|[-+*/%^]=|[=(){}\[\],]", line):
            tokens.append((m.group(0), lineno, m.start(), line))
    blocks = []
    prev = None
    for tok, lineno, col, line in tokens:
        before = line[:col].rstrip()
        if before.endswith(".") or before.endswith(":"):
            prev = tok
            continue  # field access like t.end is not a keyword
        if tok == "!=":
            errors.append("'!=' is not Luau (use '~=') on line %d" % lineno)
        elif tok in ("function", "do", "repeat"):
            blocks.append((tok, lineno))
        elif tok == "if":
            if prev in ("=", "(", ",", "{", "[", "return", "and", "or"):
                pass  # if-expression, no 'end'
            else:
                blocks.append((tok, lineno))
        elif tok == "end":
            if not blocks or blocks[-1][0] == "repeat":
                errors.append("unexpected 'end' on line %d" % lineno)
                return errors
            blocks.pop()
        elif tok == "until":
            if not blocks or blocks[-1][0] != "repeat":
                errors.append("unexpected 'until' on line %d" % lineno)
                return errors
            blocks.pop()
        prev = tok
    if blocks:
        errors.append("'%s' on line %d is never closed" % blocks[-1])
    if is_module:
        if not any(l.startswith("return") for l in code.split("\n")):
            errors.append("ModuleScript must have a top-level (unindented) 'return'")
    return errors
'''

_checker_ns: dict = {}
exec(LUAU_CHECKER_SOURCE, _checker_ns)
check_luau = _checker_ns["check_luau"]

# ---------------------------------------------------------------------------
# EMBEDDED SOURCE FILES (complete Luau sources written verbatim to disk)
# ---------------------------------------------------------------------------
EMBEDDED_FILES = {}

EMBEDDED_FILES['plugin/WarStateBridge.server.luau'] = r'''-- WarStateBridge (Studio plugin, OPTIONAL)
-- Talks ONLY to the local Python bridge at http://127.0.0.1:<port>. It accepts a fixed whitelist of
-- READ-ONLY structured commands ("ping", "verify_structure"). It never edits your place and never
-- executes arbitrary code. Its only job is to let build_war_state.py verify that Studio actually
-- received the Rojo-synced project.

local HttpService = game:GetService("HttpService")
local RunService = game:GetService("RunService")

if RunService:IsRunning() then
	return -- edit mode only, never during Play
end

local PORT = 34873
local BASE = "http://127.0.0.1:" .. PORT
local POLL_SECONDS = 2
local ALLOWED = { ping = true, verify_structure = true }

local toolbar = plugin:CreateToolbar("War State")
local toggle = toolbar:CreateButton("Bridge", "Toggle the War State local verification bridge", "")
toggle.ClickableWhenViewportHidden = true

local enabled = plugin:GetSetting("WarStateBridgeEnabled")
if enabled == nil then
	enabled = true
end
toggle:SetActive(enabled)

toggle.Click:Connect(function()
	enabled = not enabled
	plugin:SetSetting("WarStateBridgeEnabled", enabled)
	toggle:SetActive(enabled)
	print("[WarStateBridge] " .. (enabled and "enabled" or "disabled"))
end)

local function request(method: string, path: string, body)
	local ok, response = pcall(function()
		return HttpService:RequestAsync({
			Url = BASE .. path,
			Method = method,
			Headers = { ["Content-Type"] = "application/json" },
			Body = body and HttpService:JSONEncode(body) or nil,
		})
	end)
	if not ok or not response.Success then
		return nil
	end
	local decoded
	local decodeOk = pcall(function()
		decoded = HttpService:JSONDecode(response.Body)
	end)
	return decodeOk and decoded or nil
end

-- path like "ReplicatedStorage/Shared/Config/GameConfig"
local function resolve(path: string)
	local current: Instance? = nil
	for segment in string.gmatch(path, "[^/]+") do
		if current == nil then
			local okService, service = pcall(function()
				return game:GetService(segment)
			end)
			current = okService and service or game:FindFirstChild(segment)
		else
			current = current:FindFirstChild(segment)
		end
		if current == nil then
			return nil
		end
	end
	return current
end

local function handle(command)
	if type(command) ~= "table" or not ALLOWED[command.type] then
		return nil
	end
	if command.type == "ping" then
		return { id = command.id, type = "ping", ok = true }
	end
	local missing, found = {}, 0
	local paths = type(command.paths) == "table" and command.paths or {}
	for i, path in ipairs(paths) do
		if i > 2000 then
			break
		end
		if type(path) == "string" then
			if resolve(path) then
				found += 1
			else
				table.insert(missing, path)
			end
		end
	end
	return {
		id = command.id,
		type = "verify_structure",
		ok = #missing == 0,
		found = found,
		missing = missing,
	}
end

task.spawn(function()
	local announced = false
	while true do
		task.wait(POLL_SECONDS)
		if enabled then
			local hello = request("POST", "/v1/hello", {
				placeName = game.Name,
				placeId = game.PlaceId,
			})
			if hello and hello.ok then
				if not announced then
					announced = true
					print("[WarStateBridge] Connected to local build script")
				end
				local command = request("GET", "/v1/command", nil)
				if command and command.type and command.type ~= "none" then
					local result = handle(command)
					if result then
						request("POST", "/v1/result", result)
					end
				end
			else
				announced = false
			end
		end
	end
end)
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Config/ThemeConfig.luau'] = r'''-- ThemeConfig: White + Light Blue UI theme. Tweak visuals here only.

local Theme = {}

Theme.Colors = {
	Background = Color3.fromRGB(255, 255, 255),
	Surface = Color3.fromRGB(246, 250, 255),
	SurfaceAlt = Color3.fromRGB(234, 243, 253),
	Accent = Color3.fromRGB(84, 156, 230),
	AccentSoft = Color3.fromRGB(214, 233, 252),
	AccentDark = Color3.fromRGB(52, 116, 190),
	Text = Color3.fromRGB(28, 40, 56),
	TextMuted = Color3.fromRGB(108, 124, 146),
	TextOnAccent = Color3.fromRGB(255, 255, 255),
	Stroke = Color3.fromRGB(206, 223, 242),
	Danger = Color3.fromRGB(214, 88, 88),
	DangerSoft = Color3.fromRGB(252, 232, 232),
	Disabled = Color3.fromRGB(226, 231, 238),
	Success = Color3.fromRGB(76, 170, 120),
}

Theme.Fonts = {
	Regular = Enum.Font.Gotham,
	Medium = Enum.Font.GothamMedium,
	Bold = Enum.Font.GothamBold,
}

Theme.TextSize = {
	Small = 12,
	Body = 14,
	Title = 18,
	Header = 22,
}

Theme.Radius = {
	Small = 8,
	Medium = 12,
	Pill = 999,
}

Theme.Motion = {
	Fast = 0.12,
	Normal = 0.2,
	Slow = 0.28,
	Style = Enum.EasingStyle.Quad,
	Direction = Enum.EasingDirection.Out,
}

return Theme
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/BuildingModels.luau'] = r'''-- BuildingModels: procedural low-poly building visuals (no external assets needed).
-- Every model is built around a ground-level invisible Root part (PrimaryPart) and faces +Z at rotation 0.
-- Visual parts do NOT collide (CanCollide=false). Placement validation is a separate system.

local BuildingModels = {}

local RAD45 = math.rad(45)
local RAD90 = math.rad(90)

local C = {
	Cream = Color3.fromRGB(241, 231, 210),
	Beige = Color3.fromRGB(226, 208, 180),
	White = Color3.fromRGB(244, 244, 240),
	Sky = Color3.fromRGB(196, 218, 238),
	Sage = Color3.fromRGB(178, 199, 166),
	Sand = Color3.fromRGB(222, 196, 158),
	Brick = Color3.fromRGB(176, 98, 78),
	Terracotta = Color3.fromRGB(193, 108, 82),
	Slate = Color3.fromRGB(86, 98, 114),
	Charcoal = Color3.fromRGB(70, 74, 82),
	RoofBrown = Color3.fromRGB(122, 86, 64),
	Wood = Color3.fromRGB(158, 114, 78),
	Door = Color3.fromRGB(104, 76, 58),
	Glass = Color3.fromRGB(164, 202, 230),
	Foundation = Color3.fromRGB(182, 182, 176),
	Trim = Color3.fromRGB(250, 250, 248),
	Green = Color3.fromRGB(110, 150, 96),
}
BuildingModels.Palette = C

local function part(model, name, size, cframe, color, material, transparency)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = cframe
	p.Color = color
	p.Material = material or Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = true
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Transparency = transparency or 0
	p:SetAttribute("BaseTransparency", p.Transparency)
	p.Parent = model
	return p
end

local function box(model, name, sx, sy, sz, x, y, z, color, material)
	return part(model, name, Vector3.new(sx, sy, sz), CFrame.new(x, y, z), color, material)
end

-- Gable roof. Ridge runs along world X when ridgeAlongX is true, else along world Z.
-- (bx, bz) = body center, w/d = body size in world X/Z, h = wall height.
local function gableRoof(model, bx, bz, w, d, h, ridgeAlongX, wallColor, roofColor)
	local frame = CFrame.new(bx, 0, bz)
	local length, span = w, d
	if not ridgeAlongX then
		frame = frame * CFrame.Angles(0, RAD90, 0)
		length, span = d, w
	end
	local s = span / 2
	local side = span / math.sqrt(2)
	local overhang = 0.5
	local t = 0.3
	-- Triangular gable: a 45-degree rotated square prism; its lower half is hidden inside the body/ground.
	part(model, "Gable", Vector3.new(length, side, side), frame * CFrame.new(0, h, 0) * CFrame.Angles(RAD45, 0, 0), wallColor)
	local slabLength = s * math.sqrt(2) + overhang
	local slabSize = Vector3.new(length + 0.5, t, slabLength)
	part(
		model,
		"RoofA",
		slabSize,
		frame * CFrame.new(0, h + s / 2, s / 2) * CFrame.Angles(RAD45, 0, 0) * CFrame.new(0, t / 2, overhang / 2),
		roofColor
	)
	part(
		model,
		"RoofB",
		slabSize,
		frame * CFrame.new(0, h + s / 2, -s / 2) * CFrame.Angles(-RAD45, 0, 0) * CFrame.new(0, t / 2, -overhang / 2),
		roofColor
	)
	part(model, "Ridge", Vector3.new(length + 0.6, 0.3, 0.45), frame * CFrame.new(0, h + s + 0.12, 0), roofColor:Lerp(Color3.new(0, 0, 0), 0.15))
	return h + s
end

local function flatRoof(model, bx, bz, w, d, h, roofColor, trimColor)
	box(model, "RoofSlab", w + 0.4, 0.35, d + 0.4, bx, h + 0.175, bz, roofColor)
	box(model, "Parapet", w + 0.5, 0.2, d + 0.5, bx, h + 0.45, bz, trimColor)
	return h + 0.55
end

local function frontWindows(model, bx, bz, w, d, floors, count, skipCenter, glass)
	local faceZ = bz + d / 2 + 0.06
	for floor = 1, floors do
		local y = 2.0 + (floor - 1) * 3.2
		for i = 1, count do
			local fx = bx - w / 2 + (i - 0.5) * (w / count)
			local isCenter = math.abs(fx - bx) < w / count / 2
			if not (floor == 1 and skipCenter and isCenter) then
				box(model, "Window", 1.2, 1.2, 0.12, fx, y, faceZ, glass)
			end
		end
	end
end

local function sideWindows(model, bx, bz, w, d, floors, glass)
	for floor = 1, floors do
		local y = 2.0 + (floor - 1) * 3.2
		box(model, "WindowL", 0.12, 1.2, 1.2, bx - w / 2 - 0.06, y, bz, glass)
		box(model, "WindowR", 0.12, 1.2, 1.2, bx + w / 2 + 0.06, y, bz, glass)
	end
end

local function door(model, x, bz, d, color)
	box(model, "Door", 1.4, 2.5, 0.14, x, 0.3 + 1.25, bz + d / 2 + 0.07, color)
	box(model, "Step", 2.0, 0.2, 0.7, x, 0.1, bz + d / 2 + 0.35, C.Foundation)
end

local function foundation(model, bx, bz, w, d)
	box(model, "Foundation", w + 0.4, 0.3, d + 0.4, bx, 0.15, bz, C.Foundation)
end

local function body(model, name, bx, bz, w, d, h, color)
	return box(model, name, w, h - 0.3, d, bx, 0.3 + (h - 0.3) / 2, bz, color)
end

-- roofY = roof surface height at (x, z); the chimney base is sunk into the roof.
local function chimney(model, x, z, roofY, color)
	box(model, "Chimney", 0.8, 2.4, 0.8, x, roofY + 0.7, z, color)
end

local function floorBand(model, bx, bz, w, d, y, color)
	box(model, "Band", w + 0.1, 0.25, d + 0.1, bx, y, bz, color)
end

local function garage(model, bx, bz, w, d, h, wallColor, roofColor)
	body(model, "Garage", bx, bz, w, d, h, wallColor)
	box(model, "GarageDoor", w - 1.0, h - 1.2, 0.12, bx, 0.3 + (h - 1.2) / 2, bz + d / 2 + 0.06, C.Trim)
	box(model, "GarageRoof", w + 0.3, 0.3, d + 0.3, bx, h + 0.15, bz, roofColor)
end

local function porch(model, x, frontZ, width, depth, h, roofColor)
	box(model, "PorchDeck", width, 0.25, depth, x, 0.125, frontZ + depth / 2, C.Wood)
	box(model, "PorchPostL", 0.25, h, 0.25, x - width / 2 + 0.2, h / 2, frontZ + depth - 0.2, C.Trim)
	box(model, "PorchPostR", 0.25, h, 0.25, x + width / 2 - 0.2, h / 2, frontZ + depth - 0.2, C.Trim)
	box(model, "PorchRoof", width + 0.3, 0.25, depth + 0.2, x, h + 0.12, frontZ + depth / 2, roofColor)
end

local function shrub(model, x, z, size)
	box(model, "Shrub", size, size * 0.8, size, x, size * 0.4, z, C.Green)
end

-- Variant builders. Each receives the model and footprint (w, d) and must stay inside it.
local Variants = {}

-- SMALL HOUSES (8 x 8)
Variants.SmallHouse_A = function(m)
	foundation(m, 0, -0.4, 6.6, 5.8)
	body(m, "Body", 0, -0.4, 6.6, 5.8, 4.2, C.Cream)
	gableRoof(m, 0, -0.4, 6.6, 5.8, 4.2, true, C.Cream, C.Terracotta)
	chimney(m, 1.8, -1.6, 5.9, C.Brick)
	door(m, 0, -0.4, 5.8, C.Door)
	frontWindows(m, 0, -0.4, 6.6, 5.8, 1, 3, true, C.Glass)
	sideWindows(m, 0, -0.4, 6.6, 5.8, 1, C.Glass)
	shrub(m, -2.8, 3.2, 0.9)
end

Variants.SmallHouse_B = function(m)
	foundation(m, 0, -0.9, 6.0, 5.4)
	body(m, "Body", 0, -0.9, 6.0, 5.4, 4.0, C.Sky)
	gableRoof(m, 0, -0.9, 6.0, 5.4, 4.0, false, C.Sky, C.Slate)
	door(m, 0, -0.9, 5.4, C.Trim)
	frontWindows(m, 0, -0.9, 6.0, 5.4, 1, 2, false, C.Glass)
	porch(m, 0, -0.9 + 2.7, 3.2, 1.4, 2.8, C.Slate)
end

Variants.SmallHouse_C = function(m)
	foundation(m, 0, -0.3, 6.8, 6.0)
	body(m, "Body", 0, -0.3, 6.8, 6.0, 3.8, C.White)
	box(m, "Cladding", 2.2, 3.4, 0.1, -2.2, 0.3 + 1.7, -0.3 + 3.0 + 0.05, C.Wood)
	flatRoof(m, 0, -0.3, 6.8, 6.0, 3.8, C.Charcoal, C.White)
	box(m, "WideWindow", 3.2, 1.4, 0.12, 1.2, 2.2, -0.3 + 3.0 + 0.06, C.Glass)
	door(m, -2.2, -0.3, 6.0, C.Charcoal)
	sideWindows(m, 0, -0.3, 6.8, 6.0, 1, C.Glass)
end

Variants.SmallHouse_D = function(m)
	foundation(m, -0.7, -0.4, 5.4, 5.8)
	body(m, "Body", -0.7, -0.4, 5.4, 5.8, 4.4, C.Sage)
	gableRoof(m, -0.7, -0.4, 5.4, 5.8, 4.4, true, C.Sage, C.RoofBrown)
	door(m, -0.7, -0.4, 5.8, C.Door)
	frontWindows(m, -0.7, -0.4, 5.4, 5.8, 1, 3, true, C.Glass)
	box(m, "Shed", 1.8, 2.4, 3.0, 2.9, 1.2, -1.2, C.Wood)
	box(m, "ShedRoof", 2.1, 0.25, 3.3, 2.9, 2.5, -1.2, C.RoofBrown)
end

-- MEDIUM HOUSES (12 x 8)
Variants.MediumHouse_A = function(m)
	foundation(m, 0, -0.5, 10.4, 6.0)
	body(m, "Body", 0, -0.5, 10.4, 6.0, 7.0, C.Beige)
	floorBand(m, 0, -0.5, 10.4, 6.0, 3.6, C.Trim)
	gableRoof(m, 0, -0.5, 10.4, 6.0, 7.0, true, C.Beige, C.Slate)
	chimney(m, -3.4, -1.6, 8.9, C.Brick)
	door(m, 0, -0.5, 6.0, C.Door)
	frontWindows(m, 0, -0.5, 10.4, 6.0, 2, 4, true, C.Glass)
	sideWindows(m, 0, -0.5, 10.4, 6.0, 2, C.Glass)
end

Variants.MediumHouse_B = function(m)
	-- L-shape: main block + perpendicular wing
	foundation(m, -1.6, -1.0, 7.2, 5.4)
	body(m, "Body", -1.6, -1.0, 7.2, 5.4, 4.4, C.Cream)
	gableRoof(m, -1.6, -1.0, 7.2, 5.4, 4.4, true, C.Cream, C.Terracotta)
	foundation(m, 3.4, 0.0, 4.2, 7.4)
	body(m, "Wing", 3.4, 0.0, 4.2, 7.4, 4.4, C.Cream)
	gableRoof(m, 3.4, 0.0, 4.2, 7.4, 4.4, false, C.Cream, C.Terracotta)
	door(m, -1.6, -1.0, 5.4, C.Door)
	frontWindows(m, -1.6, -1.0, 7.2, 5.4, 1, 3, true, C.Glass)
	box(m, "WingWindow", 1.6, 1.3, 0.12, 3.4, 2.1, 3.76, C.Glass)
end

Variants.MediumHouse_C = function(m)
	-- Modern stacked boxes
	foundation(m, 0, -0.4, 10.6, 6.2)
	body(m, "Lower", 0, -0.4, 10.6, 6.2, 3.6, C.White)
	flatRoof(m, 0, -0.4, 10.6, 6.2, 3.6, C.Charcoal, C.White)
	box(m, "Upper", 6.0, 2.8, 5.0, -1.8, 3.95 + 1.4, -0.9, C.Sky)
	box(m, "UpperRoof", 6.4, 0.3, 5.4, -1.8, 3.95 + 2.95, -0.9, C.Charcoal)
	box(m, "UpperWindow", 3.6, 1.3, 0.12, -1.8, 5.4, -0.9 + 2.56, C.Glass)
	box(m, "Glazing", 4.0, 1.6, 0.12, 2.6, 2.1, -0.4 + 3.16, C.Glass)
	door(m, -2.0, -0.4, 6.2, C.Charcoal)
	sideWindows(m, 0, -0.4, 10.6, 6.2, 1, C.Glass)
end

Variants.MediumHouse_D = function(m)
	foundation(m, -1.5, -0.6, 7.6, 6.0)
	body(m, "Body", -1.5, -0.6, 7.6, 6.0, 4.4, C.Sand)
	gableRoof(m, -1.5, -0.6, 7.6, 6.0, 4.4, true, C.Sand, C.RoofBrown)
	door(m, -1.5, -0.6, 6.0, C.Door)
	frontWindows(m, -1.5, -0.6, 7.6, 6.0, 1, 3, true, C.Glass)
	garage(m, 4.1, -0.4, 3.4, 6.4, 3.4, C.Sand, C.RoofBrown)
end

-- LARGE HOUSES (16 x 12)
Variants.LargeHouse_A = function(m)
	foundation(m, -1.6, -0.8, 11.6, 8.4)
	body(m, "Body", -1.6, -0.8, 11.6, 8.4, 7.2, C.Cream)
	floorBand(m, -1.6, -0.8, 11.6, 8.4, 3.7, C.Trim)
	gableRoof(m, -1.6, -0.8, 11.6, 8.4, 7.2, true, C.Cream, C.Slate)
	chimney(m, 2.2, -2.8, 8.6, C.Brick)
	door(m, -1.6, -0.8, 8.4, C.Door)
	frontWindows(m, -1.6, -0.8, 11.6, 8.4, 2, 5, true, C.Glass)
	sideWindows(m, -1.6, -0.8, 11.6, 8.4, 2, C.Glass)
	garage(m, 5.9, -0.4, 3.6, 7.6, 3.6, C.Cream, C.Slate)
	shrub(m, -6.8, 4.6, 1.1)
end

Variants.LargeHouse_B = function(m)
	foundation(m, 0, -0.6, 14.4, 9.0)
	body(m, "Lower", 0, -0.6, 14.4, 9.0, 3.8, C.White)
	flatRoof(m, 0, -0.6, 14.4, 9.0, 3.8, C.Charcoal, C.White)
	box(m, "Upper", 8.6, 3.0, 7.0, 2.4, 4.15 + 1.5, -1.6, C.White)
	box(m, "UpperRoof", 9.0, 0.3, 7.4, 2.4, 4.15 + 3.15, -1.6, C.Charcoal)
	box(m, "UpperGlazing", 6.0, 1.6, 0.12, 2.4, 5.7, -1.6 + 3.56, C.Glass)
	box(m, "TerraceRail", 5.2, 0.6, 0.15, -4.4, 4.45, 3.7, C.Trim)
	box(m, "Glazing", 6.4, 1.8, 0.12, 3.2, 2.2, -0.6 + 4.56, C.Glass)
	box(m, "WoodPanel", 3.0, 3.2, 0.14, -4.8, 2.0, -0.6 + 4.57, C.Wood)
	door(m, -1.6, -0.6, 9.0, C.Charcoal)
	sideWindows(m, 0, -0.6, 14.4, 9.0, 1, C.Glass)
end

Variants.LargeHouse_C = function(m)
	-- Two-storey L-shape
	foundation(m, -2.0, -1.6, 10.8, 7.2)
	body(m, "Body", -2.0, -1.6, 10.8, 7.2, 7.0, C.Beige)
	floorBand(m, -2.0, -1.6, 10.8, 7.2, 3.6, C.Trim)
	gableRoof(m, -2.0, -1.6, 10.8, 7.2, 7.0, true, C.Beige, C.Terracotta)
	foundation(m, 4.6, 0.2, 5.4, 10.6)
	body(m, "Wing", 4.6, 0.2, 5.4, 10.6, 7.0, C.Beige)
	floorBand(m, 4.6, 0.2, 5.4, 10.6, 3.6, C.Trim)
	gableRoof(m, 4.6, 0.2, 5.4, 10.6, 7.0, false, C.Beige, C.Terracotta)
	door(m, -2.0, -1.6, 7.2, C.Door)
	frontWindows(m, -2.0, -1.6, 10.8, 7.2, 2, 4, true, C.Glass)
	frontWindows(m, 4.6, 0.2, 5.4, 10.6, 2, 2, false, C.Glass)
end

Variants.LargeHouse_D = function(m)
	foundation(m, 0, -1.2, 10.0, 8.6)
	body(m, "Body", 0, -1.2, 10.0, 8.6, 7.4, C.Sky)
	floorBand(m, 0, -1.2, 10.0, 8.6, 3.7, C.Trim)
	gableRoof(m, 0, -1.2, 10.0, 8.6, 7.4, false, C.Sky, C.Charcoal)
	chimney(m, -3.2, -3.0, 9.2, C.Brick)
	door(m, 0, -1.2, 8.6, C.Trim)
	frontWindows(m, 0, -1.2, 10.0, 8.6, 2, 4, true, C.Glass)
	sideWindows(m, 0, -1.2, 10.0, 8.6, 2, C.Glass)
	porch(m, 0, -1.2 + 4.3, 5.0, 1.6, 3.0, C.Charcoal)
	shrub(m, -5.8, 4.8, 1.0)
	shrub(m, 5.8, 4.8, 1.0)
end

BuildingModels.Variants = Variants

function BuildingModels.hasVariant(variantId: string): boolean
	return Variants[variantId] ~= nil
end

-- Builds the model at the origin. Caller positions it with model:PivotTo(cframe).
function BuildingModels.build(def, variantId: string)
	local builder = Variants[variantId]
	assert(builder, "Unknown building variant " .. tostring(variantId))
	local model = Instance.new("Model")
	model.Name = variantId
	local root = part(
		model,
		"Root",
		Vector3.new(def.Footprint[1], 0.2, def.Footprint[2]),
		CFrame.new(0, 0, 0),
		Color3.new(1, 1, 1),
		Enum.Material.SmoothPlastic,
		1
	)
	model.PrimaryPart = root
	builder(model)
	local _, size = model:GetBoundingBox()
	model:SetAttribute("VisualHeight", size.Y)
	return model
end

return BuildingModels
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/Countries.luau'] = r'''-- Countries: lookup helpers over the generated CountryRegistry (195 sovereign states).
-- Flags: FlagAsset is empty unless a real, verified Roblox asset id is provided.
-- When FlagAsset is empty the UI shows EmojiFallback.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local Registry = require(Config:WaitForChild("CountryRegistry"))

local Countries = {}

Countries.Continents = Registry.Continents
Countries.List = Registry.Countries

local byId = {}
local byContinent = {}
for _, continent in ipairs(Registry.Continents) do
	byContinent[continent] = {}
end
for _, entry in ipairs(Registry.Countries) do
	byId[entry.Id] = entry
	local bucket = byContinent[entry.Continent]
	if bucket then
		table.insert(bucket, entry)
	end
end
for _, bucket in pairs(byContinent) do
	table.sort(bucket, function(a, b)
		return a.DisplayNameEN < b.DisplayNameEN
	end)
end

function Countries.get(id: string)
	return byId[id]
end

function Countries.forContinent(continent: string)
	return byContinent[continent] or {}
end

function Countries.count(): number
	return #Registry.Countries
end

function Countries.hasRealFlag(entry): boolean
	return entry ~= nil and type(entry.FlagAsset) == "string" and entry.FlagAsset ~= ""
end

-- Case-insensitive plain-text search over English names (secondary navigation).
function Countries.search(query: string, continent: string?)
	local q = string.lower(query or "")
	local results = {}
	local source = continent and Countries.forContinent(continent) or Registry.Countries
	for _, entry in ipairs(source) do
		if q == "" or string.find(string.lower(entry.DisplayNameEN), q, 1, true) then
			table.insert(results, entry)
		end
	end
	return results
end

return Countries
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/DefaultCountry.luau'] = r'''-- DefaultCountry: creates an EMPTY country from GameConfig.EmptyCountry.
-- No starting resources, citizens, houses, roads or economy.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))

local DefaultCountry = {}

local function deepCopy(value)
	if type(value) ~= "table" then
		return value
	end
	local copy = {}
	for k, v in pairs(value) do
		copy[k] = deepCopy(v)
	end
	return copy
end

DefaultCountry.deepCopy = deepCopy

function DefaultCountry.new(slotIndex: number, name: string, flagId: string, continent: string, technologyBranch: string)
	local country = deepCopy(GameConfig.EmptyCountry)
	country.SchemaVersion = GameConfig.SchemaVersion
	country.SlotIndex = slotIndex
	country.Name = name
	country.FlagId = flagId
	country.Continent = continent
	country.TechnologyBranch = technologyBranch
	country.CreatedAt = os.time()
	country.NextBuildingId = 1
	country.NextRoadId = 1
	return country
end

-- Fill missing fields for older saves without granting anything.
function DefaultCountry.migrate(country)
	for key, value in pairs(GameConfig.EmptyCountry) do
		if country[key] == nil then
			country[key] = deepCopy(value)
		end
	end
	country.NextBuildingId = country.NextBuildingId or 1
	country.NextRoadId = country.NextRoadId or 1
	country.SchemaVersion = GameConfig.SchemaVersion
	return country
end

return DefaultCountry
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/GridMath.luau'] = r'''--!strict
-- GridMath: pure geometry helpers shared by client preview and server validation.
-- Coordinates are world X/Z on the flat territory plane.

local GridMath = {}

GridMath.DirectionOrder = { "N", "E", "S", "W" }

-- Grid direction offsets. N points to -Z (Roblox forward), E to +X.
GridMath.DirectionOffset = {
	N = { 0, -1 },
	E = { 1, 0 },
	S = { 0, 1 },
	W = { -1, 0 },
}

GridMath.Opposite = { N = "S", S = "N", E = "W", W = "E" }

function GridMath.normalizeRotation(step: number): number
	return ((math.floor(step) % 4) + 4) % 4
end

-- Rotate a direction clockwise (seen from above) by `step` quarter turns.
function GridMath.rotateDirection(dir: string, step: number): string
	local index = table.find(GridMath.DirectionOrder, dir)
	assert(index, "Unknown direction " .. tostring(dir))
	local rotated = ((index - 1 + GridMath.normalizeRotation(step)) % 4) + 1
	return GridMath.DirectionOrder[rotated]
end

-- Yaw (radians) used for models so that visuals match rotateDirection.
function GridMath.yawForRotation(step: number): number
	return -math.rad(GridMath.normalizeRotation(step) * 90)
end

function GridMath.rotatedSize(width: number, depth: number, step: number): (number, number)
	if GridMath.normalizeRotation(step) % 2 == 1 then
		return depth, width
	end
	return width, depth
end

export type Rect = { minX: number, maxX: number, minZ: number, maxZ: number }

function GridMath.rect(centerX: number, centerZ: number, width: number, depth: number): Rect
	return {
		minX = centerX - width / 2,
		maxX = centerX + width / 2,
		minZ = centerZ - depth / 2,
		maxZ = centerZ + depth / 2,
	}
end

function GridMath.rectsOverlap(a: Rect, b: Rect, tolerance: number?): boolean
	local tol = tolerance or 0
	return a.minX < b.maxX - tol and a.maxX > b.minX + tol and a.minZ < b.maxZ - tol and a.maxZ > b.minZ + tol
end

function GridMath.rectInside(inner: Rect, outer: Rect, tolerance: number?): boolean
	local tol = tolerance or 0
	return inner.minX >= outer.minX - tol
		and inner.maxX <= outer.maxX + tol
		and inner.minZ >= outer.minZ - tol
		and inner.maxZ <= outer.maxZ + tol
end

function GridMath.pointRectDistance(x: number, z: number, r: Rect): number
	local dx = math.max(r.minX - x, 0, x - r.maxX)
	local dz = math.max(r.minZ - z, 0, z - r.maxZ)
	return math.sqrt(dx * dx + dz * dz)
end

-- Snap a footprint so that its edges line up with the grid measured from (originX, originZ).
function GridMath.snapFootprint(
	x: number,
	z: number,
	width: number,
	depth: number,
	grid: number,
	originX: number,
	originZ: number
): (number, number)
	local minX = originX + math.floor((x - width / 2 - originX) / grid + 0.5) * grid
	local minZ = originZ + math.floor((z - depth / 2 - originZ) / grid + 0.5) * grid
	return minX + width / 2, minZ + depth / 2
end

-- Integer cell index containing a coordinate.
function GridMath.cellIndex(value: number, cellSize: number, origin: number): number
	return math.floor((value - origin) / cellSize)
end

function GridMath.cellCenter(index: number, cellSize: number, origin: number): number
	return origin + (index + 0.5) * cellSize
end

function GridMath.cellKey(ix: number, iz: number): string
	return tostring(ix) .. ":" .. tostring(iz)
end

return GridMath
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/PlacementRules.luau'] = r'''-- PlacementRules: shared placement validation.
-- The client uses it for the live preview, the SERVER uses the same rules as the authority.
--
-- ctx = {
--   plot = Plots bounds,
--   buildingRects = { Rect, ... },        -- world-space footprints of existing buildings
--   roadCells = { ["ix:iz"] = Rect, ... } -- world-space rects of existing road tiles
-- }

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local GridMath = require(Shared:WaitForChild("Modules"):WaitForChild("GridMath"))

local PlacementRules = {}

PlacementRules.Reasons = {
	Ok = "OK",
	OutsideTerritory = "Outside territory",
	OverlapBuilding = "Overlaps a building",
	OverlapRoad = "Overlaps a road",
	RoadOccupied = "Road already here",
	TooFarFromRoad = "Too far from road",
	NoRoads = "Build a road first",
	UnknownType = "Unknown type",
}

function PlacementRules.plotRect(plot)
	return { minX = plot.minX, maxX = plot.maxX, minZ = plot.minZ, maxZ = plot.maxZ }
end

-- Snap a world point to a building footprint. Returns centerX, centerZ, rect, width, depth.
function PlacementRules.snapBuilding(def, worldX: number, worldZ: number, rotation: number, plot)
	local width, depth = GridMath.rotatedSize(def.Footprint[1], def.Footprint[2], rotation)
	local cx, cz =
		GridMath.snapFootprint(worldX, worldZ, width, depth, PlacementConfig.GridSize, plot.minX, plot.minZ)
	return cx, cz, GridMath.rect(cx, cz, width, depth), width, depth
end

-- Snap a world point to a road tile. Returns ix, iz, centerX, centerZ, rect.
function PlacementRules.snapRoad(worldX: number, worldZ: number, plot)
	local size = PlacementConfig.RoadTileSize
	local ix = GridMath.cellIndex(worldX, size, plot.minX)
	local iz = GridMath.cellIndex(worldZ, size, plot.minZ)
	return ix, iz, PlacementRules.roadCellCenter(ix, iz, plot)
end

function PlacementRules.roadCellCenter(ix: number, iz: number, plot)
	local size = PlacementConfig.RoadTileSize
	local cx = GridMath.cellCenter(ix, size, plot.minX)
	local cz = GridMath.cellCenter(iz, size, plot.minZ)
	return cx, cz, GridMath.rect(cx, cz, size, size)
end

-- Distance from a point to the nearest road tile. Returns math.huge when no roads exist.
function PlacementRules.nearestRoadDistance(x: number, z: number, roadCells): number
	local best = math.huge
	for _, rect in pairs(roadCells) do
		local d = GridMath.pointRectDistance(x, z, rect)
		if d < best then
			best = d
		end
	end
	return best
end

-- Returns ok, reason, info
function PlacementRules.validateBuilding(def, worldX: number, worldZ: number, rotation: number, ctx)
	if not def then
		return false, PlacementRules.Reasons.UnknownType, nil
	end
	local tol = PlacementConfig.OverlapTolerance
	local cx, cz, rect = PlacementRules.snapBuilding(def, worldX, worldZ, rotation, ctx.plot)
	local info = { centerX = cx, centerZ = cz, rect = rect, roadDistance = math.huge }

	if not GridMath.rectInside(rect, PlacementRules.plotRect(ctx.plot), tol) then
		return false, PlacementRules.Reasons.OutsideTerritory, info
	end
	for _, other in ipairs(ctx.buildingRects) do
		if GridMath.rectsOverlap(rect, other, tol) then
			return false, PlacementRules.Reasons.OverlapBuilding, info
		end
	end
	for _, roadRect in pairs(ctx.roadCells) do
		if GridMath.rectsOverlap(rect, roadRect, tol) then
			return false, PlacementRules.Reasons.OverlapRoad, info
		end
	end
	if PlacementConfig.RequireRoadAccess then
		if next(ctx.roadCells) == nil then
			return false, PlacementRules.Reasons.NoRoads, info
		end
		local distance = PlacementRules.nearestRoadDistance(cx, cz, ctx.roadCells)
		info.roadDistance = distance
		if distance > PlacementConfig.MaxRoadDistance then
			return false, PlacementRules.Reasons.TooFarFromRoad, info
		end
	end
	return true, PlacementRules.Reasons.Ok, info
end

function PlacementRules.validateRoad(worldX: number, worldZ: number, ctx)
	local tol = PlacementConfig.OverlapTolerance
	local ix, iz, cx, cz, rect = PlacementRules.snapRoad(worldX, worldZ, ctx.plot)
	local info = { ix = ix, iz = iz, centerX = cx, centerZ = cz, rect = rect }
	if not GridMath.rectInside(rect, PlacementRules.plotRect(ctx.plot), tol) then
		return false, PlacementRules.Reasons.OutsideTerritory, info
	end
	if ctx.roadCells[GridMath.cellKey(ix, iz)] then
		return false, PlacementRules.Reasons.RoadOccupied, info
	end
	for _, other in ipairs(ctx.buildingRects) do
		if GridMath.rectsOverlap(rect, other, tol) then
			return false, PlacementRules.Reasons.OverlapBuilding, info
		end
	end
	return true, PlacementRules.Reasons.Ok, info
end

return PlacementRules
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/Plots.luau'] = r'''-- Plots: territory geometry. Each active country gets one flat plot (territory).
-- Building and road positions are saved in plot-LOCAL coordinates so a country can
-- be loaded onto any free plot in a later session.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))

local Plots = {}

function Plots.getBounds(index: number)
	local t = GameConfig.Territory
	local centerX = t.OriginX + (index - 1) * t.Spacing
	local centerZ = t.OriginZ
	local half = t.Size / 2
	return {
		index = index,
		centerX = centerX,
		centerZ = centerZ,
		minX = centerX - half,
		maxX = centerX + half,
		minZ = centerZ - half,
		maxZ = centerZ + half,
		size = t.Size,
		surfaceY = t.SurfaceY,
	}
end

function Plots.toWorld(bounds, localX: number, localZ: number): (number, number)
	return bounds.minX + localX, bounds.minZ + localZ
end

function Plots.toLocal(bounds, worldX: number, worldZ: number): (number, number)
	return worldX - bounds.minX, worldZ - bounds.minZ
end

function Plots.maxPlots(): number
	return GameConfig.Territory.MaxPlots
end

return Plots
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/RoadGraph.luau'] = r'''-- RoadGraph: pure road-network logic (no Instances).
-- Segment record fields (saved): RoadId, Type, Rotation, Ix, Iz, Position {X, Z} (plot-local)
-- Derived fields (recomputed): Neighbours (connected RoadIds), Adjacent (touching RoadIds), Connected
-- The graph is ready for future pathfinding: Neighbours are true bidirectional edges.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local RoadConfig = require(Shared:WaitForChild("Config"):WaitForChild("RoadConfig"))
local GridMath = require(Shared:WaitForChild("Modules"):WaitForChild("GridMath"))

local RoadGraph = {}

local typeById = {}
for _, roadType in ipairs(RoadConfig.Types) do
	typeById[roadType.Id] = roadType
end

function RoadGraph.getType(typeId: string)
	return typeById[typeId]
end

-- Returns a set {N=true, ...} of open sides after rotation.
function RoadGraph.openings(typeId: string, rotation: number)
	local roadType = typeById[typeId]
	local result = {}
	if not roadType then
		return result
	end
	for _, dir in ipairs(roadType.Openings) do
		result[GridMath.rotateDirection(dir, rotation)] = true
	end
	return result
end

-- segmentsByCell: map "ix:iz" -> segment
local function refreshSegment(segmentsByCell, segment)
	local open = RoadGraph.openings(segment.Type, segment.Rotation)
	local neighbours = {}
	local adjacent = {}
	for _, dir in ipairs(GridMath.DirectionOrder) do
		local offset = GridMath.DirectionOffset[dir]
		local other = segmentsByCell[GridMath.cellKey(segment.Ix + offset[1], segment.Iz + offset[2])]
		if other then
			table.insert(adjacent, other.RoadId)
			local otherOpen = RoadGraph.openings(other.Type, other.Rotation)
			if open[dir] and otherOpen[GridMath.Opposite[dir]] then
				table.insert(neighbours, other.RoadId)
			end
		end
	end
	segment.Neighbours = neighbours
	segment.Adjacent = adjacent
	segment.Connected = #neighbours > 0
end

-- Recompute a segment and its four adjacent cells after a change.
function RoadGraph.updateAround(segmentsByCell, ix: number, iz: number)
	local center = segmentsByCell[GridMath.cellKey(ix, iz)]
	if center then
		refreshSegment(segmentsByCell, center)
	end
	for _, dir in ipairs(GridMath.DirectionOrder) do
		local offset = GridMath.DirectionOffset[dir]
		local other = segmentsByCell[GridMath.cellKey(ix + offset[1], iz + offset[2])]
		if other then
			refreshSegment(segmentsByCell, other)
		end
	end
end

function RoadGraph.recomputeAll(segmentsByCell)
	for _, segment in pairs(segmentsByCell) do
		refreshSegment(segmentsByCell, segment)
	end
end

-- Breadth-first count of the network reachable from a RoadId (future logistics/pathfinding hook).
function RoadGraph.networkSize(segmentsById, startId: string): number
	local visited = { [startId] = true }
	local queue = { startId }
	local count = 0
	while #queue > 0 do
		local id = table.remove(queue, 1)
		local segment = segmentsById[id]
		if segment then
			count += 1
			for _, n in ipairs(segment.Neighbours or {}) do
				if not visited[n] then
					visited[n] = true
					table.insert(queue, n)
				end
			end
		end
	end
	return count
end

return RoadGraph
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Modules/RoadModels.luau'] = r'''-- RoadModels: procedural road tiles (Straight, Corner, TJunction, Crossroad).
-- Tiles are built unrotated (openings from RoadConfig) and rotated by the caller with GridMath.yawForRotation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local RoadConfig = require(Shared:WaitForChild("Config"):WaitForChild("RoadConfig"))

local RoadModels = {}

local function rgb(t)
	return Color3.fromRGB(t[1], t[2], t[3])
end

local SIDEWALK = rgb(RoadConfig.Colors.Sidewalk)
local ASPHALT = rgb(RoadConfig.Colors.Asphalt)
local MARKING = rgb(RoadConfig.Colors.Marking)

local function part(model, name, size, position, color)
	local p = Instance.new("Part")
	p.Name = name
	p.Size = size
	p.CFrame = CFrame.new(position)
	p.Color = color
	p.Material = Enum.Material.SmoothPlastic
	p.Anchored = true
	p.CanCollide = false
	p.CanTouch = false
	p.CanQuery = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p:SetAttribute("BaseTransparency", 0)
	p.Parent = model
	return p
end

local ARM = {
	N = { 0, -1 },
	E = { 1, 0 },
	S = { 0, 1 },
	W = { -1, 0 },
}

function RoadModels.build(typeId: string)
	local roadType
	for _, t in ipairs(RoadConfig.Types) do
		if t.Id == typeId then
			roadType = t
		end
	end
	assert(roadType, "Unknown road type " .. tostring(typeId))

	local size = RoadConfig.TileSize
	local half = size / 2
	local lane = RoadConfig.RoadWidth
	local model = Instance.new("Model")
	model.Name = "Road_" .. typeId

	local root = part(model, "Root", Vector3.new(size, 0.2, size), Vector3.new(0, 0, 0), SIDEWALK)
	root.Transparency = 1
	root:SetAttribute("BaseTransparency", 1)
	model.PrimaryPart = root

	part(model, "Sidewalk", Vector3.new(size, 0.2, size), Vector3.new(0, 0.1, 0), SIDEWALK)
	part(model, "Asphalt", Vector3.new(lane, 0.24, lane), Vector3.new(0, 0.12, 0), ASPHALT)

	local edge = (size - lane) / 2
	for _, dir in ipairs(roadType.Openings) do
		local o = ARM[dir]
		local armCenter = half - edge / 2
		local armSize
		if o[1] == 0 then
			armSize = Vector3.new(lane, 0.24, edge)
		else
			armSize = Vector3.new(edge, 0.24, lane)
		end
		part(model, "Arm" .. dir, armSize, Vector3.new(o[1] * armCenter, 0.12, o[2] * armCenter), ASPHALT)
		-- Lane dash on each open arm (subtle, flat)
		local dashCenter = half * 0.55
		local dashSize
		if o[1] == 0 then
			dashSize = Vector3.new(0.25, 0.04, 1.3)
		else
			dashSize = Vector3.new(1.3, 0.04, 0.25)
		end
		part(model, "Dash" .. dir, dashSize, Vector3.new(o[1] * dashCenter, 0.25, o[2] * dashCenter), MARKING)
	end
	return model
end

return RoadModels
'''

EMBEDDED_FILES['src/ReplicatedStorage/Shared/Types/Types.luau'] = r'''-- Types: shared Luau type definitions (documentation + type checking only, no runtime logic).

export type BuildState = "PLANNED" | "UNDER_CONSTRUCTION" | "COMPLETED"

export type BuildingRecord = {
	Id: string,
	Type: string,
	Variant: string,
	X: number, -- plot-local center X
	Z: number, -- plot-local center Z
	Rotation: number, -- 0..3 quarter turns clockwise
	State: BuildState,
	PlannedElapsed: number,
	Progress: number, -- seconds of construction completed
	CreatedAt: number,
}

export type RoadSegment = {
	RoadId: string,
	Type: string, -- Straight | Corner | TJunction | Crossroad
	Rotation: number,
	Ix: number,
	Iz: number,
	Position: { X: number, Z: number }, -- plot-local tile center
	Neighbours: { string }, -- mutually connected RoadIds (graph edges)
	Adjacent: { string }, -- touching RoadIds (connected or not)
	Connected: boolean,
}

export type Country = {
	SchemaVersion: number,
	SlotIndex: number,
	Name: string,
	FlagId: string,
	Continent: string,
	TechnologyBranch: string,
	CreatedAt: number,
	Money: number,
	Oil: number,
	Fuel: number,
	Steel: number,
	Supplies: number,
	Population: number,
	Workers: number,
	HousingCapacity: number,
	Buildings: { [string]: BuildingRecord },
	Roads: { [string]: RoadSegment },
	Military: { [string]: any },
	NextBuildingId: number,
	NextRoadId: number,
}

export type SlotSummary = {
	Index: number,
	Locked: boolean,
	Empty: boolean,
	Name: string?,
	FlagId: string?,
	TechnologyBranch: string?,
	Population: number?,
}

return {}
'''

EMBEDDED_FILES['src/ServerScriptService/ServerMain.server.luau'] = r'''-- ServerMain: single server entry point. Requires every system, calls init() then start().
-- Systems never run from their own Script; order is explicit here.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))

local Systems = script.Parent:WaitForChild("Systems")

-- Remotes are defined in default.project.json (Rojo). If they are missing (e.g. playing without
-- Rojo), create them once. FindFirstChild guards prevent duplicates.
local function ensureRemotes()
	local folder = ReplicatedStorage:FindFirstChild("Remotes")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "Remotes"
		folder.Parent = ReplicatedStorage
	end
	local remotes = {}
	for _, name in ipairs(Constants.RemoteFunctions) do
		local r = folder:FindFirstChild(name)
		if not r then
			r = Instance.new("RemoteFunction")
			r.Name = name
			r.Parent = folder
			warn("[ServerMain] Created missing RemoteFunction " .. name)
		end
		remotes[name] = r
	end
	for _, name in ipairs(Constants.RemoteEvents) do
		local r = folder:FindFirstChild(name)
		if not r then
			r = Instance.new("RemoteEvent")
			r.Name = name
			r.Parent = folder
			warn("[ServerMain] Created missing RemoteEvent " .. name)
		end
		remotes[name] = r
	end
	return remotes
end

local ORDER = {
	{ "Data", "DataService" },
	{ "World", "WorldService" },
	{ "Resources", "ResourceService" },
	{ "Roads", "RoadService" },
	{ "Buildings", "BuildingService" },
	{ "Construction", "ConstructionService" },
	{ "Population", "PopulationService" },
	{ "Country", "CountryService" },
	{ "Research", "ResearchService" },
	{ "Production", "ProductionService" },
	{ "Economy", "EconomyService" },
	{ "Military", "MilitaryService" },
}

local services = { Remotes = ensureRemotes() }
local loaded = {}

for _, entry in ipairs(ORDER) do
	local folderName, moduleName = entry[1], entry[2]
	local moduleScript = Systems:WaitForChild(folderName):WaitForChild(moduleName)
	local ok, result = pcall(require, moduleScript)
	if not ok then
		error(string.format("[ServerMain] Failed to load %s: %s", moduleName, tostring(result)))
	end
	services[moduleName] = result
	table.insert(loaded, result)
end

for _, service in ipairs(loaded) do
	service.init(services)
end
for _, service in ipairs(loaded) do
	service.start()
end

ReplicatedStorage:SetAttribute("WarStateServerReady", true)
print(string.format("[WarState] Server ready (%d systems)", #loaded))
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Buildings/BuildingService.luau'] = r'''-- BuildingService: server-authoritative building placement.
-- Client sends {Type, Variant, X, Z, Rotation}; the server snaps, validates (territory, overlap,
-- road access within PlacementConfig.MaxRoadDistance) and creates a PLANNED building that the
-- ConstructionService then builds over time.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local BuildingModels = require(Modules:WaitForChild("BuildingModels"))

local BuildingService = {}
BuildingService.Name = "BuildingService"

local services
local remotes
local runtime = {} -- [Player] = { models = {Id -> Model}, rects = {Id -> Rect} }
local lastRequest = {}

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

function BuildingService.getDef(typeId: string)
	return defsById[typeId]
end

local function getRuntime(player)
	local r = runtime[player]
	if not r then
		r = { models = {}, rects = {} }
		runtime[player] = r
	end
	return r
end

local function worldRect(record, bounds)
	local def = defsById[record.Type]
	local width, depth = GridMath.rotatedSize(def.Footprint[1], def.Footprint[2], record.Rotation)
	return GridMath.rect(bounds.minX + record.X, bounds.minZ + record.Z, width, depth)
end

local function spawnModel(player, record)
	local folder = services.WorldService.getPlotFolder(player, "Buildings")
	local bounds = services.WorldService.getBounds(player)
	local def = defsById[record.Type]
	if not folder or not bounds or not def then
		return nil
	end
	local r = getRuntime(player)
	local old = r.models[record.Id]
	if old then
		old:Destroy()
	end
	local model = BuildingModels.build(def, record.Variant)
	model.Name = record.Id
	local wx, wz = bounds.minX + record.X, bounds.minZ + record.Z
	model:PivotTo(CFrame.new(wx, bounds.surfaceY, wz) * CFrame.Angles(0, GridMath.yawForRotation(record.Rotation), 0))
	local rect = worldRect(record, bounds)
	model:SetAttribute(Constants.Attributes.Kind, "Building")
	model:SetAttribute(Constants.Attributes.TypeId, record.Type)
	model:SetAttribute("Variant", record.Variant)
	model:SetAttribute("RectMinX", rect.minX)
	model:SetAttribute("RectMaxX", rect.maxX)
	model:SetAttribute("RectMinZ", rect.minZ)
	model:SetAttribute("RectMaxZ", rect.maxZ)
	model:SetAttribute("State", record.State)
	model.Parent = folder
	r.models[record.Id] = model
	r.rects[record.Id] = rect
	return model
end

function BuildingService.getModel(player: Player, id: string)
	local r = runtime[player]
	return r and r.models[id] or nil
end

function BuildingService.getBuildingRects(player: Player)
	local result = {}
	local r = runtime[player]
	if r then
		for _, rect in pairs(r.rects) do
			table.insert(result, rect)
		end
	end
	return result
end

function BuildingService.loadCountry(player: Player, country)
	BuildingService.clearPlayer(player)
	for _, record in pairs(country.Buildings) do
		if defsById[record.Type] and BuildingModels.hasVariant(record.Variant) then
			local model = spawnModel(player, record)
			if model then
				services.ConstructionService.track(player, record, model)
			end
		else
			warn("[BuildingService] Skipping unknown saved building " .. tostring(record.Type))
		end
	end
end

function BuildingService.clearPlayer(player: Player)
	local r = runtime[player]
	if r then
		for _, model in pairs(r.models) do
			model:Destroy()
		end
	end
	runtime[player] = nil
end

local function handlePlace(player, request)
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < PlacementConfig.RequestCooldown then
		return { ok = false, error = "Too fast" }
	end
	lastRequest[player] = now

	local country = services.DataService.getCountry(player)
	local bounds = services.WorldService.getBounds(player)
	if not country or not bounds then
		return { ok = false, error = "No active state" }
	end
	if type(request) ~= "table" or type(request.X) ~= "number" or type(request.Z) ~= "number" then
		return { ok = false, error = "Invalid request" }
	end
	if request.X ~= request.X or request.Z ~= request.Z then
		return { ok = false, error = "Invalid request" }
	end
	local def = type(request.Type) == "string" and defsById[request.Type] or nil
	if not def or def.Active ~= true then
		return { ok = false, error = "Unknown building" }
	end
	local variant = request.Variant
	if type(variant) ~= "string" or not table.find(def.Variants, variant) then
		variant = def.Variants[1]
	end
	local rotation = GridMath.normalizeRotation(type(request.Rotation) == "number" and request.Rotation or 0)

	local ctx = {
		plot = bounds,
		buildingRects = BuildingService.getBuildingRects(player),
		roadCells = services.RoadService.getRoadCells(player),
	}
	local ok, reason, info = PlacementRules.validateBuilding(def, request.X, request.Z, rotation, ctx)
	if not ok then
		return { ok = false, error = reason }
	end

	local id = "B" .. tostring(country.NextBuildingId)
	country.NextBuildingId += 1
	local record = {
		Id = id,
		Type = def.Id,
		Variant = variant,
		X = info.centerX - bounds.minX,
		Z = info.centerZ - bounds.minZ,
		Rotation = rotation,
		State = Constants.BuildState.Planned,
		PlannedElapsed = 0,
		Progress = 0,
		CreatedAt = os.time(),
	}
	country.Buildings[id] = record
	local model = spawnModel(player, record)
	if model then
		services.ConstructionService.track(player, record, model)
	end
	services.DataService.markDirty(player)
	services.CountryService.push(player)
	return { ok = true, buildingId = id }
end

function BuildingService.init(allServices)
	services = allServices
	remotes = allServices.Remotes
end

function BuildingService.start()
	remotes[Constants.Remotes.PlaceBuilding].OnServerInvoke = handlePlace
	Players.PlayerRemoving:Connect(function(player)
		BuildingService.clearPlayer(player)
		lastRequest[player] = nil
	end)
end

return BuildingService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Construction/ConstructionService.luau'] = r'''-- ConstructionService: PLANNED -> UNDER_CONSTRUCTION -> COMPLETED over time.
-- Visuals: planned = faint ghost; under construction = parts become solid from the ground up
-- plus a small progress bar that is REMOVED on completion (no permanent floating labels).
-- Construction advances only while the owner is in the session (progress is saved).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))

local ConstructionService = {}
ConstructionService.Name = "ConstructionService"

local services
local tracked = {} -- [Player] = { [Id] = { record, model, parts } }

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

local GHOST = GameConfig.Construction.GhostTransparency
local ACCENT = Color3.fromRGB(84, 156, 230)

local function collectParts(model)
	local parts = {}
	local pivotY = model:GetPivot().Position.Y
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") and d.Name ~= "Root" then
			local base = d:GetAttribute("BaseTransparency") or 0
			local bottom = d.Position.Y - d.Size.Y / 2 - pivotY
			table.insert(parts, { part = d, base = base, bottom = bottom })
		end
	end
	return parts
end

local function ensureProgressBar(entry)
	local model = entry.model
	local existing = model:FindFirstChild("ConstructionProgress")
	if existing then
		return existing
	end
	local height = model:GetAttribute("VisualHeight") or 6
	local gui = Instance.new("BillboardGui")
	gui.Name = "ConstructionProgress"
	gui.Size = UDim2.fromOffset(64, 8)
	gui.StudsOffsetWorldSpace = Vector3.new(0, height + 1.5, 0)
	gui.MaxDistance = GameConfig.Construction.ProgressBarMaxDistance
	gui.AlwaysOnTop = false
	gui.LightInfluence = 0
	gui.Adornee = model.PrimaryPart

	local back = Instance.new("Frame")
	back.Name = "Back"
	back.Size = UDim2.fromScale(1, 1)
	back.BackgroundColor3 = Color3.fromRGB(255, 255, 255)
	back.BorderSizePixel = 0
	back.Parent = gui
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(1, 0)
	corner.Parent = back

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = ACCENT
	fill.BorderSizePixel = 0
	fill.Parent = back
	local fillCorner = Instance.new("UICorner")
	fillCorner.CornerRadius = UDim.new(1, 0)
	fillCorner.Parent = fill

	gui.Parent = model
	return gui
end

local function applyVisual(entry)
	local record = entry.record
	local model = entry.model
	local def = defsById[record.Type]
	model:SetAttribute("State", record.State)
	if record.State == Constants.BuildState.Completed then
		for _, info in ipairs(entry.parts) do
			info.part.Transparency = info.base
		end
		local bar = model:FindFirstChild("ConstructionProgress")
		if bar then
			bar:Destroy()
		end
		model:SetAttribute("Progress", 1)
		return
	end

	local fraction = 0
	if record.State == Constants.BuildState.UnderConstruction then
		fraction = math.clamp(record.Progress / def.BuildTimeSeconds, 0, 1)
	end
	model:SetAttribute("Progress", fraction)
	local height = model:GetAttribute("VisualHeight") or 6
	local revealHeight = fraction * height
	for _, info in ipairs(entry.parts) do
		if record.State == Constants.BuildState.UnderConstruction and info.bottom <= revealHeight then
			info.part.Transparency = info.base
		else
			info.part.Transparency = math.max(info.base, GHOST)
		end
	end
	local bar = ensureProgressBar(entry)
	local fill = bar:FindFirstChild("Back") and bar.Back:FindFirstChild("Fill")
	if fill then
		fill.Size = UDim2.fromScale(math.max(fraction, 0.04), 1)
	end
end

function ConstructionService.track(player: Player, record, model)
	tracked[player] = tracked[player] or {}
	local entry = { record = record, model = model, parts = collectParts(model) }
	tracked[player][record.Id] = entry
	applyVisual(entry)
end

function ConstructionService.clearPlayer(player: Player)
	tracked[player] = nil
end

local function step(dt: number)
	for player, entries in pairs(tracked) do
		local changedCapacity = false
		local anyActive = false
		for id, entry in pairs(entries) do
			local record = entry.record
			local def = defsById[record.Type]
			if record.State == Constants.BuildState.Planned then
				anyActive = true
				record.PlannedElapsed += dt
				if record.PlannedElapsed >= GameConfig.Construction.PlannedSeconds then
					record.State = Constants.BuildState.UnderConstruction
				end
				applyVisual(entry)
			elseif record.State == Constants.BuildState.UnderConstruction then
				anyActive = true
				record.Progress = math.min(record.Progress + dt, def.BuildTimeSeconds)
				if record.Progress >= def.BuildTimeSeconds then
					record.State = Constants.BuildState.Completed
					changedCapacity = true
					services.CountryService.notify(player, def.DisplayName .. " completed", "success")
				end
				applyVisual(entry)
			end
			if record.State == Constants.BuildState.Completed then
				entries[id] = nil
			end
		end
		if anyActive then
			services.DataService.markDirty(player)
		end
		if changedCapacity then
			local country = services.DataService.getCountry(player)
			if country then
				services.PopulationService.recalculate(country)
			end
		end
		if anyActive or changedCapacity then
			services.CountryService.push(player)
		end
	end
end

function ConstructionService.init(allServices)
	services = allServices
end

function ConstructionService.start()
	task.spawn(function()
		local interval = GameConfig.Construction.TickSeconds
		local last = os.clock()
		while true do
			task.wait(interval)
			local now = os.clock()
			local dt = now - last
			last = now
			local ok, err = pcall(step, dt)
			if not ok then
				warn("[ConstructionService] " .. tostring(err))
			end
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		tracked[player] = nil
	end)
end

return ConstructionService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Country/CountryService.luau'] = r'''-- CountryService: slot selection, country creation (server-validated) and state replication.
-- The client only sends a creation REQUEST; the server validates every field and builds the country.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextService = game:GetService("TextService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local TechnologyConfig = require(Config:WaitForChild("TechnologyConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local Countries = require(Shared:WaitForChild("Modules"):WaitForChild("Countries"))
local DefaultCountry = require(Shared:WaitForChild("Modules"):WaitForChild("DefaultCountry"))

local CountryService = {}
CountryService.Name = "CountryService"

local services
local remotes
local pushQueued = {}
local busy = {}

local techById = {}
for _, branch in ipairs(TechnologyConfig.Branches) do
	techById[branch.Id] = branch
end

local function cleanName(raw)
	if type(raw) ~= "string" then
		return nil, "Enter a country name"
	end
	local name = string.gsub(raw, "%s+", " ")
	name = string.match(name, "^%s*(.-)%s*$") or ""
	local length = utf8.len(name) or #name
	if length < GameConfig.CountryName.MinLength then
		return nil, "Name is too short"
	end
	if length > GameConfig.CountryName.MaxLength then
		return nil, "Name is too long"
	end
	if not string.match(name, "^[%w %-'%.]+$") then
		return nil, "Use letters, numbers, spaces, - ' ."
	end
	return name, nil
end

local function filterName(player, name)
	local ok, result = pcall(function()
		local filtered = TextService:FilterStringAsync(name, player.UserId, Enum.TextFilterContext.PublicChat)
		return filtered:GetNonChatStringForBroadcastAsync()
	end)
	if ok then
		if result ~= name then
			return nil, "That name is not allowed"
		end
		return name, nil
	end
	if RunService:IsStudio() then
		-- Text filtering is not always available in Studio; allow the already-sanitized name.
		return name, nil
	end
	return nil, "Name check failed. Try again."
end

local function snapshot(player)
	local session = services.DataService.getSession(player)
	local country = session and session.country
	if not country then
		return { Active = false, Persistent = session and session.persistent or false }
	end
	local buildingCount, underConstruction = 0, 0
	for _, record in pairs(country.Buildings) do
		buildingCount += 1
		if record.State ~= Constants.BuildState.Completed then
			underConstruction += 1
		end
	end
	local roadCount = 0
	for _ in pairs(country.Roads) do
		roadCount += 1
	end
	return {
		Active = true,
		Persistent = session.persistent,
		SlotIndex = session.activeSlot,
		Name = country.Name,
		FlagId = country.FlagId,
		Continent = country.Continent,
		TechnologyBranch = country.TechnologyBranch,
		Money = country.Money,
		Oil = country.Oil,
		Fuel = country.Fuel,
		Steel = country.Steel,
		Supplies = country.Supplies,
		Population = country.Population,
		Workers = country.Workers,
		HousingCapacity = country.HousingCapacity,
		BuildingCount = buildingCount,
		UnderConstruction = underConstruction,
		RoadCount = roadCount,
		PlotIndex = player:GetAttribute(Constants.Attributes.PlotIndex),
	}
end

-- Replicate the authoritative state (throttled to one push per frame).
function CountryService.push(player: Player)
	if pushQueued[player] then
		return
	end
	pushQueued[player] = true
	task.defer(function()
		pushQueued[player] = nil
		if player.Parent then
			remotes[Constants.Remotes.StateChanged]:FireClient(player, snapshot(player))
		end
	end)
end

function CountryService.notify(player: Player, message: string, kind: string?)
	remotes[Constants.Remotes.Notify]:FireClient(player, { Text = message, Kind = kind or "info" })
end

local function guard(player, fn)
	if busy[player] then
		return { ok = false, error = "Please wait" }
	end
	busy[player] = true
	local ok, result = pcall(fn)
	busy[player] = nil
	if not ok then
		warn("[CountryService] " .. tostring(result))
		return { ok = false, error = "Server error" }
	end
	return result
end

local function enterCountry(player, index, country)
	services.DataService.setActive(player, index, country)
	services.PopulationService.recalculate(country)
	local ok, err = services.WorldService.enter(player)
	if not ok then
		services.DataService.clearActive(player)
		return { ok = false, error = err }
	end
	services.RoadService.loadCountry(player, country)
	services.BuildingService.loadCountry(player, country)
	services.DataService.saveActive(player)
	CountryService.push(player)
	return { ok = true, state = snapshot(player) }
end

local function handleGetProfile(player)
	local session = services.DataService.loadSession(player)
	return {
		ok = true,
		slots = services.DataService.getSlotSummaries(player),
		persistent = session.persistent,
		activeSlot = session.activeSlot,
	}
end

local function validSlotIndex(index)
	return type(index) == "number" and index == math.floor(index) and index >= 1 and index <= GameConfig.SlotCount
end

local function handleCreate(player, index, payload)
	return guard(player, function()
		if not validSlotIndex(index) then
			return { ok = false, error = "Invalid slot" }
		end
		if not services.DataService.isSlotUnlocked(index) then
			return { ok = false, error = "This slot is locked" }
		end
		local session = services.DataService.loadSession(player)
		if session.activeSlot then
			return { ok = false, error = "Leave your current state first" }
		end
		if session.profile.Summaries["Slot" .. index] ~= nil then
			return { ok = false, error = "Slot already has a state" }
		end
		if type(payload) ~= "table" then
			return { ok = false, error = "Invalid request" }
		end
		local name, nameError = cleanName(payload.Name)
		if not name then
			return { ok = false, error = nameError }
		end
		name, nameError = filterName(player, name)
		if not name then
			return { ok = false, error = nameError }
		end
		local flag = type(payload.FlagId) == "string" and Countries.get(payload.FlagId) or nil
		if not flag then
			return { ok = false, error = "Select a flag" }
		end
		if payload.Continent ~= flag.Continent then
			return { ok = false, error = "Flag does not match continent" }
		end
		local branch = type(payload.TechnologyBranch) == "string" and techById[payload.TechnologyBranch] or nil
		if not branch or branch.Active ~= true then
			return { ok = false, error = "Select a technology branch" }
		end
		local country = DefaultCountry.new(index, name, flag.Id, flag.Continent, branch.Id)
		return enterCountry(player, index, country)
	end)
end

local function handleLoad(player, index)
	return guard(player, function()
		if not validSlotIndex(index) or not services.DataService.isSlotUnlocked(index) then
			return { ok = false, error = "Invalid slot" }
		end
		local session = services.DataService.loadSession(player)
		if session.activeSlot then
			return { ok = false, error = "Leave your current state first" }
		end
		local country, err = services.DataService.loadSlot(player, index)
		if not country then
			return { ok = false, error = err }
		end
		return enterCountry(player, index, country)
	end)
end

local function handleLeave(player)
	return guard(player, function()
		local session = services.DataService.getSession(player)
		if not session or not session.activeSlot then
			return { ok = true }
		end
		services.DataService.saveActive(player)
		services.ConstructionService.clearPlayer(player)
		services.RoadService.clearPlayer(player)
		services.BuildingService.clearPlayer(player)
		services.WorldService.leave(player)
		services.DataService.clearActive(player)
		CountryService.push(player)
		return { ok = true }
	end)
end

local function handleDelete(player, index)
	return guard(player, function()
		if not validSlotIndex(index) then
			return { ok = false, error = "Invalid slot" }
		end
		local ok, err = services.DataService.deleteSlot(player, index)
		return { ok = ok, error = err }
	end)
end

local function handleSave(player)
	return guard(player, function()
		local session = services.DataService.getSession(player)
		if not session or not session.activeSlot then
			return { ok = false, error = "No active state" }
		end
		session.dirty = true
		local ok = services.DataService.saveActive(player)
		if not session.persistent then
			return { ok = ok, persistent = false }
		end
		return { ok = ok, persistent = true, error = (not ok) and "Save failed" or nil }
	end)
end

function CountryService.init(allServices)
	services = allServices
	remotes = allServices.Remotes
end

function CountryService.start()
	remotes[Constants.Remotes.GetProfile].OnServerInvoke = handleGetProfile
	remotes[Constants.Remotes.CreateCountry].OnServerInvoke = handleCreate
	remotes[Constants.Remotes.LoadSlot].OnServerInvoke = handleLoad
	remotes[Constants.Remotes.LeaveState].OnServerInvoke = handleLeave
	remotes[Constants.Remotes.DeleteSlot].OnServerInvoke = handleDelete
	remotes[Constants.Remotes.SaveNow].OnServerInvoke = handleSave

	Players.PlayerRemoving:Connect(function(player)
		pushQueued[player] = nil
		busy[player] = nil
	end)
end

return CountryService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Data/DataService.luau'] = r'''-- DataService: server-authoritative save/load.
-- Profile key  : "profile_<userId>"          -> slot summaries (for the slot screen)
-- Slot keys    : "slot_<userId>_<index>"      -> full country data, one key per slot (independent)
-- If DataStores are unavailable (e.g. Studio without API access) the session runs in MEMORY mode
-- and never writes, so a failed load can never overwrite real data.

local DataStoreService = game:GetService("DataStoreService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local DefaultCountry = require(Shared:WaitForChild("Modules"):WaitForChild("DefaultCountry"))

local DataService = {}
DataService.Name = "DataService"

local store = nil
local storeError = nil
local sessions = {} -- [Player] = session
local memoryStore = {} -- used only in memory mode, lost on server shutdown

local function profileKey(userId: number): string
	return "profile_" .. tostring(userId)
end

local function slotKey(userId: number, index: number): string
	return "slot_" .. tostring(userId) .. "_" .. tostring(index)
end

local function withRetries(label: string, fn)
	local lastError = nil
	for attempt = 1, GameConfig.DataStoreRetries do
		local ok, result = pcall(fn)
		if ok then
			return true, result
		end
		lastError = result
		warn(string.format("[DataService] %s failed (attempt %d): %s", label, attempt, tostring(result)))
		local message = tostring(result)
		if string.find(message, "StudioAccessToApisNotAllowed", 1, true) or string.find(message, "API access", 1, true) then
			break -- Studio without API access: retrying cannot succeed
		end
		task.wait(attempt)
	end
	return false, lastError
end

local function newProfile()
	return { SchemaVersion = GameConfig.SchemaVersion, Summaries = {} }
end

function DataService.init(_services)
	local ok, result = pcall(function()
		return DataStoreService:GetDataStore(GameConfig.DataStoreName)
	end)
	if ok then
		store = result
	else
		storeError = tostring(result)
		warn("[DataService] DataStore unavailable, using MEMORY mode: " .. storeError)
	end
end

function DataService.start()
	task.spawn(function()
		while true do
			task.wait(GameConfig.AutosaveSeconds)
			for player in pairs(sessions) do
				task.spawn(DataService.saveActive, player)
			end
		end
	end)
	game:BindToClose(function()
		local pending = 0
		for player in pairs(sessions) do
			pending += 1
			task.spawn(function()
				DataService.saveActive(player)
				pending -= 1
			end)
		end
		local deadline = os.clock() + 25
		while pending > 0 and os.clock() < deadline do
			task.wait(0.1)
		end
	end)
end

-- Loads (or creates) the player's session. Returns session.
function DataService.loadSession(player: Player)
	if sessions[player] then
		return sessions[player]
	end
	local session = {
		player = player,
		persistent = store ~= nil,
		persistenceReason = storeError,
		profile = newProfile(),
		activeSlot = nil,
		country = nil,
		dirty = false,
	}
	if store then
		local ok, data = withRetries("Load profile", function()
			return store:GetAsync(profileKey(player.UserId))
		end)
		if ok then
			if type(data) == "table" then
				session.profile = data
				session.profile.Summaries = session.profile.Summaries or {}
			end
		else
			session.persistent = false
			session.persistenceReason = "Profile load failed: " .. tostring(data)
		end
	else
		session.profile = memoryStore[profileKey(player.UserId)] or newProfile()
	end
	sessions[player] = session
	return session
end

function DataService.getSession(player: Player)
	return sessions[player]
end

function DataService.isSlotUnlocked(index: number): boolean
	local slot = GameConfig.Slots[index]
	return slot ~= nil and slot.Unlocked == true
end

function DataService.getSlotSummaries(player: Player)
	local session = DataService.loadSession(player)
	local result = {}
	for index = 1, GameConfig.SlotCount do
		local summary = session.profile.Summaries["Slot" .. index]
		table.insert(result, {
			Index = index,
			Locked = not DataService.isSlotUnlocked(index),
			Empty = summary == nil,
			Name = summary and summary.Name or nil,
			FlagId = summary and summary.FlagId or nil,
			TechnologyBranch = summary and summary.TechnologyBranch or nil,
			Population = summary and summary.Population or nil,
		})
	end
	return result
end

local function summarize(country)
	return {
		Name = country.Name,
		FlagId = country.FlagId,
		TechnologyBranch = country.TechnologyBranch,
		Population = country.Population,
		UpdatedAt = os.time(),
	}
end

local function writeProfile(session)
	local key = profileKey(session.player.UserId)
	if not session.persistent then
		memoryStore[key] = session.profile
		return true
	end
	return withRetries("Save profile", function()
		store:UpdateAsync(key, function()
			return session.profile
		end)
	end)
end

-- Loads the full country for a slot. Returns country or nil, error.
function DataService.loadSlot(player: Player, index: number)
	local session = DataService.loadSession(player)
	if session.profile.Summaries["Slot" .. index] == nil then
		return nil, "Slot is empty"
	end
	local key = slotKey(player.UserId, index)
	local data
	if session.persistent then
		local ok, result = withRetries("Load slot", function()
			return store:GetAsync(key)
		end)
		if not ok then
			return nil, "Could not load save data. Try again."
		end
		data = result
	else
		data = memoryStore[key]
	end
	if type(data) ~= "table" then
		return nil, "Save data missing"
	end
	return DefaultCountry.migrate(data), nil
end

function DataService.setActive(player: Player, index: number, country)
	local session = DataService.loadSession(player)
	session.activeSlot = index
	session.country = country
	session.dirty = true
	session.profile.Summaries["Slot" .. index] = summarize(country)
end

function DataService.clearActive(player: Player)
	local session = sessions[player]
	if session then
		session.activeSlot = nil
		session.country = nil
		session.dirty = false
	end
end

function DataService.getCountry(player: Player)
	local session = sessions[player]
	return session and session.country or nil
end

function DataService.markDirty(player: Player)
	local session = sessions[player]
	if session then
		session.dirty = true
	end
end

-- Saves the active slot and the profile summary.
function DataService.saveActive(player: Player): boolean
	local session = sessions[player]
	if not session or not session.country or not session.activeSlot then
		return true
	end
	if not session.dirty then
		return true
	end
	local index = session.activeSlot
	local country = session.country
	session.profile.Summaries["Slot" .. index] = summarize(country)
	local key = slotKey(player.UserId, index)
	if not session.persistent then
		memoryStore[key] = DefaultCountry.deepCopy(country)
		memoryStore[profileKey(player.UserId)] = session.profile
		session.dirty = false
		return true
	end
	local ok = withRetries("Save slot", function()
		store:UpdateAsync(key, function()
			return country
		end)
	end)
	if ok then
		ok = writeProfile(session)
	end
	if ok then
		session.dirty = false
	end
	return ok
end

function DataService.deleteSlot(player: Player, index: number): (boolean, string?)
	local session = DataService.loadSession(player)
	if session.activeSlot == index then
		return false, "Leave the state before deleting it"
	end
	local key = slotKey(player.UserId, index)
	if session.persistent then
		local ok = withRetries("Delete slot", function()
			store:RemoveAsync(key)
		end)
		if not ok then
			return false, "Delete failed. Try again."
		end
	else
		memoryStore[key] = nil
	end
	session.profile.Summaries["Slot" .. index] = nil
	writeProfile(session)
	return true, nil
end

function DataService.releaseSession(player: Player)
	DataService.saveActive(player)
	sessions[player] = nil
end

Players.PlayerRemoving:Connect(function(player)
	-- WorldService/other systems clean up first via their own handlers; saving happens here.
	DataService.releaseSession(player)
end)

return DataService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Economy/EconomyService.luau'] = r'''-- EconomyService: PLANNED placeholder.
-- Money flow, jobs and commerce. Civilian trips House -> Road -> Shop/Service -> House.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local EconomyService = {}
EconomyService.Name = "EconomyService"
EconomyService.Status = "PLANNED"
EconomyService.Active = false
EconomyService.Description = "Money flow, jobs and commerce. Civilian trips House -> Road -> Shop/Service -> House."

function EconomyService.init(_services) end

function EconomyService.start() end

return EconomyService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/Aircraft.luau'] = r'''-- Aircraft: PLANNED interface reservation for the future military layer.
-- Fixed-wing aircraft layer.
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "Aircraft",
	Status = "PLANNED",
	Active = false,
	Description = "Fixed-wing aircraft layer.",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/ElectronicWarfare.luau'] = r'''-- ElectronicWarfare: PLANNED interface reservation for the future military layer.
-- Electronic warfare (jamming / detection).
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "ElectronicWarfare",
	Status = "PLANNED",
	Active = false,
	Description = "Electronic warfare (jamming / detection).",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/Helicopters.luau'] = r'''-- Helicopters: PLANNED interface reservation for the future military layer.
-- Rotary-wing aircraft layer.
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "Helicopters",
	Status = "PLANNED",
	Active = false,
	Description = "Rotary-wing aircraft layer.",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/Reconnaissance.luau'] = r'''-- Reconnaissance: PLANNED interface reservation for the future military layer.
-- Ground reconnaissance and fog-of-war reveal.
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "Reconnaissance",
	Status = "PLANNED",
	Active = false,
	Description = "Ground reconnaissance and fog-of-war reveal.",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/Satellites.luau'] = r'''-- Satellites: PLANNED interface reservation for the future military layer.
-- Satellite coverage and orbital reconnaissance.
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "Satellites",
	Status = "PLANNED",
	Active = false,
	Description = "Satellite coverage and orbital reconnaissance.",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/Future/UAV.luau'] = r'''-- UAV: PLANNED interface reservation for the future military layer.
-- Unmanned aerial vehicles (scouting).
-- No mechanics are implemented. Do not treat this module as working gameplay.

return {
	Name = "UAV",
	Status = "PLANNED",
	Active = false,
	Description = "Unmanned aerial vehicles (scouting).",
}
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Military/MilitaryService.luau'] = r'''-- MilitaryService: PLANNED placeholder.
-- Future military layer (units, military UI/data). No combat or weapons are implemented.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local MilitaryService = {}
MilitaryService.Name = "MilitaryService"
MilitaryService.Status = "PLANNED"
MilitaryService.Active = false
MilitaryService.Description = "Future military layer (units, military UI/data). No combat or weapons are implemented."

function MilitaryService.init(_services) end

function MilitaryService.start() end

return MilitaryService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Population/PopulationService.luau'] = r'''-- PopulationService: logical population (no physical NPCs).
-- Completed housing -> HousingCapacity -> Population grows gradually, never above HousingCapacity.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local GameConfig = require(Config:WaitForChild("GameConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))

local PopulationService = {}
PopulationService.Name = "PopulationService"

local services
local capacityByType = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	capacityByType[def.Id] = def.HousingCapacity or 0
end

function PopulationService.capacityOf(country): number
	local capacity = 0
	for _, record in pairs(country.Buildings) do
		if record.State == Constants.BuildState.Completed then
			capacity += capacityByType[record.Type] or 0
		end
	end
	return capacity
end

-- Recalculate capacity and clamp population (called on load and when housing completes).
function PopulationService.recalculate(country)
	country.HousingCapacity = PopulationService.capacityOf(country)
	if country.Population > country.HousingCapacity then
		country.Population = country.HousingCapacity
	end
	country.Workers = math.floor(country.Population * GameConfig.Population.WorkerRatio)
end

-- One growth step. Returns true if population changed.
function PopulationService.grow(country): boolean
	local capacity = country.HousingCapacity
	local population = country.Population
	if population >= capacity then
		if population > capacity then
			country.Population = capacity
			return true
		end
		return false
	end
	local free = capacity - population
	local growth = math.max(GameConfig.Population.MinGrowth, math.floor(free * GameConfig.Population.GrowthFraction))
	country.Population = math.min(capacity, population + growth)
	country.Workers = math.floor(country.Population * GameConfig.Population.WorkerRatio)
	return true
end

function PopulationService.init(allServices)
	services = allServices
end

function PopulationService.start()
	task.spawn(function()
		while true do
			task.wait(GameConfig.Population.TickSeconds)
			for _, player in ipairs(game:GetService("Players"):GetPlayers()) do
				local country = services.DataService.getCountry(player)
				if country and PopulationService.grow(country) then
					services.DataService.markDirty(player)
					services.CountryService.push(player)
				end
			end
		end
	end)
end

return PopulationService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Production/ProductionService.luau'] = r'''-- ProductionService: PLANNED placeholder.
-- Production chains (Oil Well -> Crude Oil -> Refinery -> Fuel). Requires stable road graph and logistics.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local ProductionService = {}
ProductionService.Name = "ProductionService"
ProductionService.Status = "PLANNED"
ProductionService.Active = false
ProductionService.Description = "Production chains (Oil Well -> Crude Oil -> Refinery -> Fuel). Requires stable road graph and logistics."

function ProductionService.init(_services) end

function ProductionService.start() end

return ProductionService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Research/ResearchService.luau'] = r'''-- ResearchService: PLANNED placeholder.
-- Time-based research (ResearchTime, Requirements, Unlocks). Not active in the initial bootstrap.
-- This module intentionally contains NO gameplay mechanics. It only reserves the interface.

local ResearchService = {}
ResearchService.Name = "ResearchService"
ResearchService.Status = "PLANNED"
ResearchService.Active = false
ResearchService.Description = "Time-based research (ResearchTime, Requirements, Unlocks). Not active in the initial bootstrap."

function ResearchService.init(_services) end

function ResearchService.start() end

return ResearchService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Resources/ResourceService.luau'] = r'''-- ResourceService: PARTIAL.
-- Resources (Money, Oil, Fuel, Steel, Supplies) exist in country data and are replicated,
-- but they stay at ZERO and are INACTIVE in the current build. No starting resources are granted.
-- Future: Oil Well -> Crude Oil -> Refinery -> Fuel, Factory -> Road -> Truck -> Warehouse.

local ResourceService = {}
ResourceService.Name = "ResourceService"
ResourceService.Status = "PARTIAL"
ResourceService.ResourceKeys = { "Money", "Oil", "Fuel", "Steel", "Supplies" }
ResourceService.Active = false

local services

function ResourceService.get(player: Player)
	local country = services.DataService.getCountry(player)
	if not country then
		return nil
	end
	local result = {}
	for _, key in ipairs(ResourceService.ResourceKeys) do
		result[key] = country[key] or 0
	end
	return result
end

function ResourceService.init(allServices)
	services = allServices
end

function ResourceService.start() end

return ResourceService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/Roads/RoadService.luau'] = r'''-- RoadService: server-authoritative road placement and the road graph.
-- Roads snap to the RoadTileSize grid, connect to adjacent segments and form a network
-- (RoadGraph) that future traffic/logistics/pathfinding will use.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local RoadConfig = require(Config:WaitForChild("RoadConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local RoadGraph = require(Modules:WaitForChild("RoadGraph"))
local RoadModels = require(Modules:WaitForChild("RoadModels"))

local RoadService = {}
RoadService.Name = "RoadService"

local services
local remotes
local runtime = {} -- [Player] = { cells = {key -> segment}, models = {RoadId -> Model} }
local lastRequest = {}

local function getRuntime(player)
	local r = runtime[player]
	if not r then
		r = { cells = {}, models = {} }
		runtime[player] = r
	end
	return r
end

local function spawnModel(player, segment)
	local folder = services.WorldService.getPlotFolder(player, "Roads")
	local bounds = services.WorldService.getBounds(player)
	if not folder or not bounds then
		return
	end
	local r = getRuntime(player)
	local old = r.models[segment.RoadId]
	if old then
		old:Destroy()
	end
	local model = RoadModels.build(segment.Type)
	model.Name = segment.RoadId
	local wx, wz = bounds.minX + segment.Position.X, bounds.minZ + segment.Position.Z
	model:PivotTo(CFrame.new(wx, bounds.surfaceY, wz) * CFrame.Angles(0, GridMath.yawForRotation(segment.Rotation), 0))
	local size = PlacementConfig.RoadTileSize
	model:SetAttribute(Constants.Attributes.Kind, "Road")
	model:SetAttribute(Constants.Attributes.TypeId, segment.Type)
	model:SetAttribute("Ix", segment.Ix)
	model:SetAttribute("Iz", segment.Iz)
	model:SetAttribute("Rotation", segment.Rotation)
	model:SetAttribute("RectMinX", wx - size / 2)
	model:SetAttribute("RectMaxX", wx + size / 2)
	model:SetAttribute("RectMinZ", wz - size / 2)
	model:SetAttribute("RectMaxZ", wz + size / 2)
	model:SetAttribute("Connected", segment.Connected == true)
	model.Parent = folder
	r.models[segment.RoadId] = model
end

local function refreshAttributes(player)
	local r = runtime[player]
	if not r then
		return
	end
	for _, segment in pairs(r.cells) do
		local model = r.models[segment.RoadId]
		if model then
			model:SetAttribute("Connected", segment.Connected == true)
		end
	end
end

-- World-space rects of all road tiles, keyed by cell (used by placement validation).
function RoadService.getRoadCells(player: Player)
	local result = {}
	local r = runtime[player]
	local bounds = services.WorldService.getBounds(player)
	if not r or not bounds then
		return result
	end
	for key, segment in pairs(r.cells) do
		local _, _, rect = PlacementRules.roadCellCenter(segment.Ix, segment.Iz, bounds)
		result[key] = rect
	end
	return result
end

function RoadService.getSegments(player: Player)
	local r = runtime[player]
	return r and r.cells or {}
end

function RoadService.loadCountry(player: Player, country)
	RoadService.clearPlayer(player)
	local r = getRuntime(player)
	for _, segment in pairs(country.Roads) do
		r.cells[GridMath.cellKey(segment.Ix, segment.Iz)] = segment
	end
	RoadGraph.recomputeAll(r.cells)
	for _, segment in pairs(r.cells) do
		spawnModel(player, segment)
	end
end

function RoadService.clearPlayer(player: Player)
	local r = runtime[player]
	if r then
		for _, model in pairs(r.models) do
			model:Destroy()
		end
	end
	runtime[player] = nil
end

local function typeIsActive(typeId)
	for _, t in ipairs(RoadConfig.Types) do
		if t.Id == typeId then
			return t.Active == true
		end
	end
	return false
end

local function handlePlace(player, request)
	local now = os.clock()
	if lastRequest[player] and now - lastRequest[player] < PlacementConfig.RequestCooldown then
		return { ok = false, error = "Too fast" }
	end
	lastRequest[player] = now

	local country = services.DataService.getCountry(player)
	local bounds = services.WorldService.getBounds(player)
	if not country or not bounds then
		return { ok = false, error = "No active state" }
	end
	if type(request) ~= "table" or type(request.X) ~= "number" or type(request.Z) ~= "number" then
		return { ok = false, error = "Invalid request" }
	end
	if request.X ~= request.X or request.Z ~= request.Z then
		return { ok = false, error = "Invalid request" }
	end
	if type(request.Type) ~= "string" or not typeIsActive(request.Type) then
		return { ok = false, error = "Unknown road type" }
	end
	local rotation = GridMath.normalizeRotation(type(request.Rotation) == "number" and request.Rotation or 0)

	local ctx = {
		plot = bounds,
		buildingRects = services.BuildingService.getBuildingRects(player),
		roadCells = RoadService.getRoadCells(player),
	}
	local ok, reason, info = PlacementRules.validateRoad(request.X, request.Z, ctx)
	if not ok then
		return { ok = false, error = reason }
	end

	local r = getRuntime(player)
	local roadId = "R" .. tostring(country.NextRoadId)
	country.NextRoadId += 1
	local segment = {
		RoadId = roadId,
		Type = request.Type,
		Rotation = rotation,
		Ix = info.ix,
		Iz = info.iz,
		Position = { X = info.centerX - bounds.minX, Z = info.centerZ - bounds.minZ },
		Neighbours = {},
		Adjacent = {},
		Connected = false,
	}
	country.Roads[roadId] = segment
	r.cells[GridMath.cellKey(info.ix, info.iz)] = segment
	RoadGraph.updateAround(r.cells, info.ix, info.iz)
	spawnModel(player, segment)
	refreshAttributes(player)
	services.DataService.markDirty(player)
	services.CountryService.push(player)
	return { ok = true, roadId = roadId, connected = segment.Connected }
end

function RoadService.init(allServices)
	services = allServices
	remotes = allServices.Remotes
end

function RoadService.start()
	remotes[Constants.Remotes.PlaceRoad].OnServerInvoke = handlePlace
	Players.PlayerRemoving:Connect(function(player)
		RoadService.clearPlayer(player)
		lastRequest[player] = nil
	end)
end

return RoadService
'''

EMBEDDED_FILES['src/ServerScriptService/Systems/World/WorldService.luau'] = r'''-- WorldService: generates the simple flat green territory (one plot per active country)
-- and the per-plot Buildings/Roads folders. NO buildings, roads, citizens or city are pre-placed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local Plots = require(Shared:WaitForChild("Modules"):WaitForChild("Plots"))

local WorldService = {}
WorldService.Name = "WorldService"

local plotOwners = {} -- [index] = Player
local playerPlots = {} -- [Player] = index

local function ensureFolder(parent: Instance, name: string): Folder
	local existing = parent:FindFirstChild(name)
	if existing and existing:IsA("Folder") then
		return existing
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = parent
	return folder
end

local function rootFolders()
	return {
		Map = ensureFolder(Workspace, "Map"),
		Buildings = ensureFolder(Workspace, "Buildings"),
		Roads = ensureFolder(Workspace, "Roads"),
		Vehicles = ensureFolder(Workspace, "Vehicles"),
		NPCs = ensureFolder(Workspace, "NPCs"),
	}
end

local function color(t)
	return Color3.new(t[1], t[2], t[3])
end

local function createTerritory(index: number, owner: Player)
	local folders = rootFolders()
	local bounds = Plots.getBounds(index)
	local t = GameConfig.Territory
	local name = "Territory_" .. index
	local existing = folders.Map:FindFirstChild(name)
	if existing then
		existing:Destroy()
	end
	local territory = Instance.new("Model")
	territory.Name = name
	territory:SetAttribute(Constants.Attributes.PlotIndex, index)
	territory:SetAttribute(Constants.Attributes.OwnerUserId, owner.UserId)

	local ground = Instance.new("Part")
	ground.Name = "Ground"
	ground.Anchored = true
	ground.CanCollide = true
	ground.Size = Vector3.new(t.Size, t.Thickness, t.Size)
	ground.CFrame = CFrame.new(bounds.centerX, bounds.surfaceY - t.Thickness / 2, bounds.centerZ)
	ground.Color = color(t.Color)
	ground.Material = Enum.Material.Grass
	ground.TopSurface = Enum.SurfaceType.Smooth
	ground.BottomSurface = Enum.SurfaceType.Smooth
	ground:SetAttribute(Constants.Attributes.PlotIndex, index)
	ground.Parent = territory

	-- Thin low border so the territory edge is readable (not a wall, does not collide).
	local border = t.BorderWidth
	local borderColor = color(t.BorderColor)
	local sides = {
		{ Vector3.new(t.Size, 0.1, border), Vector3.new(0, 0, -t.Size / 2 + border / 2) },
		{ Vector3.new(t.Size, 0.1, border), Vector3.new(0, 0, t.Size / 2 - border / 2) },
		{ Vector3.new(border, 0.1, t.Size), Vector3.new(-t.Size / 2 + border / 2, 0, 0) },
		{ Vector3.new(border, 0.1, t.Size), Vector3.new(t.Size / 2 - border / 2, 0, 0) },
	}
	for i, side in ipairs(sides) do
		local p = Instance.new("Part")
		p.Name = "Border" .. i
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.Size = side[1]
		p.CFrame = CFrame.new(bounds.centerX, bounds.surfaceY + 0.05, bounds.centerZ) + side[2]
		p.Color = borderColor
		p.Material = Enum.Material.SmoothPlastic
		p.Parent = territory
	end
	territory.PrimaryPart = ground
	territory.Parent = folders.Map

	for _, key in ipairs({ "Buildings", "Roads" }) do
		local plotFolderName = "Plot_" .. index
		local old = folders[key]:FindFirstChild(plotFolderName)
		if old then
			old:Destroy()
		end
		local folder = Instance.new("Folder")
		folder.Name = plotFolderName
		folder:SetAttribute(Constants.Attributes.PlotIndex, index)
		folder:SetAttribute(Constants.Attributes.OwnerUserId, owner.UserId)
		folder.Parent = folders[key]
	end
end

local function destroyPlot(index: number)
	local folders = rootFolders()
	local names = { { folders.Map, "Territory_" .. index }, { folders.Buildings, "Plot_" .. index }, { folders.Roads, "Plot_" .. index } }
	for _, pair in ipairs(names) do
		local inst = pair[1]:FindFirstChild(pair[2])
		if inst then
			inst:Destroy()
		end
	end
end

function WorldService.getPlotIndex(player: Player): number?
	return playerPlots[player]
end

function WorldService.getBounds(player: Player)
	local index = playerPlots[player]
	if not index then
		return nil
	end
	return Plots.getBounds(index)
end

function WorldService.getPlotFolder(player: Player, kind: string): Folder?
	local index = playerPlots[player]
	if not index then
		return nil
	end
	local root = Workspace:FindFirstChild(kind)
	return root and root:FindFirstChild("Plot_" .. index) or nil
end

local function spawnCFrame(bounds)
	return CFrame.new(bounds.centerX, bounds.surfaceY + 4, bounds.centerZ + 24)
end

function WorldService.teleportToPlot(player: Player)
	local bounds = WorldService.getBounds(player)
	local character = player.Character
	if bounds and character then
		character:PivotTo(spawnCFrame(bounds))
	end
end

function WorldService.enter(player: Player): (boolean, string?)
	if playerPlots[player] then
		return true, nil
	end
	local index = nil
	for i = 1, Plots.maxPlots() do
		if plotOwners[i] == nil then
			index = i
			break
		end
	end
	if not index then
		return false, "Server is full of states. Try another server."
	end
	plotOwners[index] = player
	playerPlots[player] = index
	createTerritory(index, player)
	player:SetAttribute(Constants.Attributes.PlotIndex, index)
	WorldService.teleportToPlot(player)
	return true, nil
end

function WorldService.leave(player: Player)
	local index = playerPlots[player]
	if not index then
		return
	end
	destroyPlot(index)
	plotOwners[index] = nil
	playerPlots[player] = nil
	player:SetAttribute(Constants.Attributes.PlotIndex, nil)
end

function WorldService.init(_services)
	rootFolders()
end

function WorldService.start()
	Players.PlayerAdded:Connect(function(player)
		player.CharacterAdded:Connect(function()
			task.defer(function()
				if playerPlots[player] then
					WorldService.teleportToPlot(player)
				end
			end)
		end)
	end)
	for _, player in ipairs(Players:GetPlayers()) do
		player.CharacterAdded:Connect(function()
			task.defer(function()
				if playerPlots[player] then
					WorldService.teleportToPlot(player)
				end
			end)
		end)
	end
	Players.PlayerRemoving:Connect(function(player)
		WorldService.leave(player)
	end)
end

return WorldService
'''

EMBEDDED_FILES['src/ServerScriptService/Tests/RuntimeSelfTest.server.luau'] = r'''-- RuntimeSelfTest: runs automatically in Studio Play (server side) and prints PASS/FAIL.
-- It exercises the REAL shared modules inside Roblox (registry, defaults, placement, road graph,
-- population). Result is also written to ReplicatedStorage attribute "WarStateSelfTest".

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

if not RunService:IsStudio() then
	return
end

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Modules = Shared:WaitForChild("Modules")
local Config = Shared:WaitForChild("Config")
local Countries = require(Modules:WaitForChild("Countries"))
local DefaultCountry = require(Modules:WaitForChild("DefaultCountry"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local RoadGraph = require(Modules:WaitForChild("RoadGraph"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local Plots = require(Modules:WaitForChild("Plots"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local Registry = require(Config:WaitForChild("CountryRegistry"))

local results = { passed = 0, failed = 0, failures = {} }

local function check(name: string, condition: boolean, detail: string?)
	if condition then
		results.passed += 1
	else
		results.failed += 1
		table.insert(results.failures, name .. (detail and (" (" .. detail .. ")") or ""))
	end
end

-- Registry
check("Registry has 195 countries", Countries.count() == 195, tostring(Countries.count()))
local seen, duplicates = {}, 0
for _, entry in ipairs(Countries.List) do
	if seen[entry.Id] then
		duplicates += 1
	end
	seen[entry.Id] = true
end
check("No duplicate country ids", duplicates == 0, tostring(duplicates))
for continent, expected in pairs(Registry.ExpectedContinentCounts) do
	local actual = #Countries.forContinent(continent)
	check("Continent count " .. continent, actual == expected, tostring(actual))
end
check("Holy See present", Countries.get("VA") ~= nil)
check("Palestine present", Countries.get("PS") ~= nil)

-- Empty country defaults
local country = DefaultCountry.new(1, "Novaria", "DE", "Europe", "USSR")
for _, key in ipairs({ "Money", "Oil", "Fuel", "Steel", "Supplies", "Population", "Workers", "HousingCapacity" }) do
	check("Empty country " .. key .. " = 0", country[key] == 0, tostring(country[key]))
end
check("Empty country has no buildings", next(country.Buildings) == nil)
check("Empty country has no roads", next(country.Roads) == nil)
check("Empty country has no military", next(country.Military) == nil)
for key in pairs(country) do
	check("No doctrine field: " .. key, not string.find(string.lower(key), "doctrine", 1, true))
end

-- Placement rules
local plot = Plots.getBounds(1)
local small
for _, def in ipairs(BuildingConfig.Buildings) do
	if def.Id == "SmallHouse" then
		small = def
	end
end
check("SmallHouse config exists", small ~= nil)
if small then
	local empty = { plot = plot, buildingRects = {}, roadCells = {} }
	local ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, empty)
	check("House without roads is invalid", not ok and reason == PlacementRules.Reasons.NoRoads, reason)

	local roadOk, _, roadInfo = PlacementRules.validateRoad(plot.minX + 84, plot.minZ + 84, empty)
	check("Road inside territory is valid", roadOk)
	local ctx = {
		plot = plot,
		buildingRects = {},
		roadCells = { [GridMath.cellKey(roadInfo.ix, roadInfo.iz)] = roadInfo.rect },
	}
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, ctx)
	check("House next to road is valid", ok, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 160, 0, ctx)
	check("House far from road is invalid", not ok and reason == PlacementRules.Reasons.TooFarFromRoad, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 84, 0, ctx)
	check("House on road is invalid", not ok and reason == PlacementRules.Reasons.OverlapRoad, reason)
	ok, reason = PlacementRules.validateBuilding(small, plot.minX - 50, plot.minZ + 84, 0, ctx)
	check("House outside territory is invalid", not ok and reason == PlacementRules.Reasons.OutsideTerritory, reason)
	local _, _, houseInfo = PlacementRules.validateBuilding(small, plot.minX + 84, plot.minZ + 96, 0, ctx)
	ctx.buildingRects = { houseInfo.rect }
	ok, reason = PlacementRules.validateBuilding(small, plot.minX + 86, plot.minZ + 98, 0, ctx)
	check("Overlapping houses are invalid", not ok and reason == PlacementRules.Reasons.OverlapBuilding, reason)
	roadOk = PlacementRules.validateRoad(plot.minX + 84, plot.minZ + 84, ctx)
	check("Duplicate road is invalid", not roadOk)
end

-- Road graph
local cells = {}
local a = { RoadId = "A", Type = "Straight", Rotation = 0, Ix = 0, Iz = 0 }
local b = { RoadId = "B", Type = "Straight", Rotation = 0, Ix = 0, Iz = 1 }
local c = { RoadId = "C", Type = "Straight", Rotation = 0, Ix = 1, Iz = 0 }
cells[GridMath.cellKey(0, 0)] = a
cells[GridMath.cellKey(0, 1)] = b
cells[GridMath.cellKey(1, 0)] = c
RoadGraph.recomputeAll(cells)
check("Straight N-S segments connect", a.Connected and table.find(a.Neighbours, "B") ~= nil)
check("Side-by-side straights do not connect", table.find(a.Neighbours, "C") == nil and table.find(a.Adjacent, "C") ~= nil)
check("Rotation maps N->E", GridMath.rotateDirection("N", 1) == "E")
local cross = RoadGraph.openings("Crossroad", 0)
check("Crossroad has 4 openings", cross.N and cross.E and cross.S and cross.W)

-- Population
local PopulationService = require(script.Parent.Parent:WaitForChild("Systems"):WaitForChild("Population"):WaitForChild("PopulationService"))
local popCountry = DefaultCountry.new(1, "Test", "DE", "Europe", "USA")
PopulationService.recalculate(popCountry)
check("No population without housing", popCountry.Population == 0 and popCountry.HousingCapacity == 0)
popCountry.Buildings.B1 = { Id = "B1", Type = "SmallHouse", State = "COMPLETED" }
PopulationService.recalculate(popCountry)
for _ = 1, 50 do
	PopulationService.grow(popCountry)
end
check("Population capped by housing", popCountry.Population == popCountry.HousingCapacity and popCountry.HousingCapacity > 0)

local status = results.failed == 0 and "PASS" or "FAIL"
ReplicatedStorage:SetAttribute("WarStateSelfTest", string.format("%s %d/%d", status, results.passed, results.passed + results.failed))
if results.failed == 0 then
	print(string.format("[WarState SelfTest] PASS (%d checks)", results.passed))
else
	warn(string.format("[WarState SelfTest] FAIL (%d passed, %d failed)", results.passed, results.failed))
	for _, failure in ipairs(results.failures) do
		warn("  - " .. failure)
	end
end
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Components/UIKit.luau'] = r'''-- UIKit: tiny UI toolkit (instance factory, theme, subtle TweenService motion).
-- Motion rules: short, subtle, no glow, no constant movement.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Theme = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("ThemeConfig"))

local UIKit = {}
UIKit.Theme = Theme
local C = Theme.Colors

function UIKit.new(className: string, props, children)
	local inst = Instance.new(className)
	local parent = nil
	for key, value in pairs(props or {}) do
		if key == "Parent" then
			parent = value
		else
			inst[key] = value
		end
	end
	for _, child in ipairs(children or {}) do
		child.Parent = inst
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end

function UIKit.tween(inst: Instance, duration: number, props, style, direction)
	local info = TweenInfo.new(duration, style or Theme.Motion.Style, direction or Theme.Motion.Direction)
	local tween = TweenService:Create(inst, info, props)
	tween:Play()
	return tween
end

function UIKit.corner(parent: Instance, radius: number?)
	local c = Instance.new("UICorner")
	if radius == nil or radius >= 999 then
		c.CornerRadius = UDim.new(1, 0)
	else
		c.CornerRadius = UDim.new(0, radius)
	end
	c.Parent = parent
	return c
end

function UIKit.stroke(parent: Instance, color: Color3?, thickness: number?, transparency: number?)
	local s = Instance.new("UIStroke")
	s.Color = color or C.Stroke
	s.Thickness = thickness or 1
	s.Transparency = transparency or 0
	s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
	s.Parent = parent
	return s
end

function UIKit.padding(parent: Instance, all: number, horizontal: number?)
	local p = Instance.new("UIPadding")
	local h = horizontal or all
	p.PaddingTop = UDim.new(0, all)
	p.PaddingBottom = UDim.new(0, all)
	p.PaddingLeft = UDim.new(0, h)
	p.PaddingRight = UDim.new(0, h)
	p.Parent = parent
	return p
end

function UIKit.list(parent: Instance, direction, spacing: number, hAlign, vAlign)
	local l = Instance.new("UIListLayout")
	l.FillDirection = direction or Enum.FillDirection.Vertical
	l.Padding = UDim.new(0, spacing or 6)
	l.SortOrder = Enum.SortOrder.LayoutOrder
	l.HorizontalAlignment = hAlign or Enum.HorizontalAlignment.Left
	l.VerticalAlignment = vAlign or Enum.VerticalAlignment.Top
	l.Parent = parent
	return l
end

function UIKit.label(props)
	local defaults = {
		BackgroundTransparency = 1,
		Font = Theme.Fonts.Medium,
		TextSize = Theme.TextSize.Body,
		TextColor3 = C.Text,
		TextXAlignment = Enum.TextXAlignment.Left,
		TextYAlignment = Enum.TextYAlignment.Center,
		Size = UDim2.new(1, 0, 0, 20),
		Text = "",
		TextTruncate = Enum.TextTruncate.AtEnd,
	}
	for k, v in pairs(props or {}) do
		defaults[k] = v
	end
	return UIKit.new("TextLabel", defaults)
end

-- Compact panel with white background, soft stroke and rounded corners.
function UIKit.panel(props)
	local defaults = {
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(320, 200),
	}
	for k, v in pairs(props or {}) do
		defaults[k] = v
	end
	local frame = UIKit.new("Frame", defaults)
	UIKit.corner(frame, Theme.Radius.Medium)
	UIKit.stroke(frame, C.Stroke, 1, 0)
	return frame
end

-- Button with hover / press / selection feedback.
-- style: "primary" | "secondary" | "ghost" | "danger"
function UIKit.button(props)
	local style = props.Style or "secondary"
	local palette = {
		primary = { bg = C.Accent, hover = C.AccentDark, text = C.TextOnAccent },
		secondary = { bg = C.Surface, hover = C.SurfaceAlt, text = C.Text },
		ghost = { bg = C.Background, hover = C.Surface, text = C.Text },
		danger = { bg = C.DangerSoft, hover = Color3.fromRGB(248, 214, 214), text = C.Danger },
	}
	local colors = palette[style] or palette.secondary
	local button = UIKit.new("TextButton", {
		Name = props.Name or "Button",
		AutoButtonColor = false,
		BackgroundColor3 = colors.bg,
		BorderSizePixel = 0,
		Size = props.Size or UDim2.fromOffset(120, 36),
		Position = props.Position,
		AnchorPoint = props.AnchorPoint,
		LayoutOrder = props.LayoutOrder or 0,
		Font = props.Font or Theme.Fonts.Medium,
		TextSize = props.TextSize or Theme.TextSize.Body,
		TextColor3 = colors.text,
		Text = props.Text or "",
		TextWrapped = true,
		Parent = props.Parent,
	})
	UIKit.corner(button, props.Radius or Theme.Radius.Small)
	local stroke = nil
	if style ~= "primary" then
		stroke = UIKit.stroke(button, C.Stroke, 1, 0)
	end
	local scale = Instance.new("UIScale")
	scale.Parent = button

	local state = { selected = false, disabled = false, hovering = false }

	local function restColor()
		if state.disabled then
			return C.Disabled
		end
		if state.selected then
			return C.AccentSoft
		end
		return colors.bg
	end

	button.MouseEnter:Connect(function()
		state.hovering = true
		if not state.disabled and not state.selected then
			UIKit.tween(button, Theme.Motion.Fast, { BackgroundColor3 = colors.hover })
		end
	end)
	button.MouseLeave:Connect(function()
		state.hovering = false
		UIKit.tween(button, Theme.Motion.Fast, { BackgroundColor3 = restColor() })
		UIKit.tween(scale, Theme.Motion.Fast, { Scale = 1 })
	end)
	button.MouseButton1Down:Connect(function()
		if not state.disabled then
			UIKit.tween(scale, Theme.Motion.Fast, { Scale = 0.96 })
		end
	end)
	button.MouseButton1Up:Connect(function()
		UIKit.tween(scale, Theme.Motion.Fast, { Scale = 1 })
	end)
	button.Activated:Connect(function()
		if not state.disabled and props.OnClick then
			props.OnClick(button)
		end
	end)

	local api = { Instance = button }
	function api.setSelected(selected: boolean)
		state.selected = selected
		UIKit.tween(button, Theme.Motion.Normal, { BackgroundColor3 = restColor() })
		if stroke then
			UIKit.tween(stroke, Theme.Motion.Normal, { Color = selected and C.Accent or C.Stroke })
		end
	end
	function api.setDisabled(disabled: boolean)
		state.disabled = disabled
		button.TextColor3 = disabled and C.TextMuted or colors.text
		button.BackgroundColor3 = restColor()
	end
	function api.setText(text: string)
		button.Text = text
	end
	return api
end

-- Subtle open: slight slide up + scale in. Frame must contain (or gets) a UIScale.
-- Only one UIScale per object is honoured, so motion reuses FitScale when present
-- and animates relative to its "BaseScale" attribute.
local function getScale(frame: GuiObject)
	local scale = frame:FindFirstChild("FitScale") or frame:FindFirstChild("MotionScale")
	if not scale then
		scale = Instance.new("UIScale")
		scale.Name = "MotionScale"
		scale.Parent = frame
	end
	return scale, (frame:GetAttribute("BaseScale") or 1)
end

function UIKit.open(frame: GuiObject, fromOffsetY: number?)
	local target = frame:GetAttribute("RestPosition")
	if not target then
		target = frame.Position
		frame:SetAttribute("RestPosition", target)
	end
	local scale, base = getScale(frame)
	scale.Scale = base * 0.97
	frame.Position = target + UDim2.fromOffset(0, fromOffsetY or 8)
	frame.Visible = true
	UIKit.tween(scale, Theme.Motion.Normal, { Scale = base })
	UIKit.tween(frame, Theme.Motion.Normal, { Position = target })
end

function UIKit.close(frame: GuiObject, toOffsetY: number?, onDone)
	if not frame.Visible then
		if onDone then
			onDone()
		end
		return
	end
	local target = frame:GetAttribute("RestPosition") or frame.Position
	local scale, base = getScale(frame)
	UIKit.tween(scale, Theme.Motion.Fast, { Scale = base * 0.97 })
	local tween = UIKit.tween(frame, Theme.Motion.Fast, { Position = target + UDim2.fromOffset(0, toOffsetY or 8) })
	tween.Completed:Connect(function()
		frame.Visible = false
		frame.Position = target
		scale.Scale = base
		if onDone then
			onDone()
		end
	end)
end

-- Horizontal ScrollingFrame that also scrolls with the mouse wheel (PC) and touch (mobile).
function UIKit.hScroll(props)
	local frame = UIKit.new("ScrollingFrame", {
		Name = props.Name or "HScroll",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = props.Size,
		Position = props.Position or UDim2.new(),
		ScrollingDirection = Enum.ScrollingDirection.X,
		AutomaticCanvasSize = Enum.AutomaticSize.X,
		CanvasSize = UDim2.new(),
		ScrollBarThickness = 3,
		ScrollBarImageColor3 = C.Stroke,
		ElasticBehavior = Enum.ElasticBehavior.WhenScrollable,
		LayoutOrder = props.LayoutOrder or 0,
		Parent = props.Parent,
	})
	UIKit.list(frame, Enum.FillDirection.Horizontal, props.Spacing or 6, nil, Enum.VerticalAlignment.Center)
	-- Mouse wheel -> horizontal scroll while hovering (children buttons do not block this).
	local hovering = false
	frame.MouseEnter:Connect(function()
		hovering = true
	end)
	frame.MouseLeave:Connect(function()
		hovering = false
	end)
	local connection
	connection = UserInputService.InputChanged:Connect(function(input)
		if not frame.Parent then
			connection:Disconnect()
			return
		end
		if hovering and frame.Visible and input.UserInputType == Enum.UserInputType.MouseWheel then
			local maxX = math.max(0, frame.AbsoluteCanvasSize.X - frame.AbsoluteWindowSize.X)
			local x = math.clamp(frame.CanvasPosition.X - input.Position.Z * 60, 0, maxX)
			UIKit.tween(frame, Theme.Motion.Fast, { CanvasPosition = Vector2.new(x, 0) })
		end
	end)
	return frame
end

function UIKit.vScroll(props)
	local frame = UIKit.new("ScrollingFrame", {
		Name = props.Name or "VScroll",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = props.Size,
		Position = props.Position or UDim2.new(),
		ScrollingDirection = Enum.ScrollingDirection.Y,
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		CanvasSize = UDim2.new(),
		ScrollBarThickness = 3,
		ScrollBarImageColor3 = C.Stroke,
		LayoutOrder = props.LayoutOrder or 0,
		Parent = props.Parent,
	})
	return frame
end

-- Flag display: real asset if FlagAsset is set, otherwise emoji fallback text.
function UIKit.flag(parent: Instance, entry, size: number)
	local holder = UIKit.new("Frame", {
		Name = "Flag",
		BackgroundColor3 = C.SurfaceAlt,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(size * 1.4, size),
		Parent = parent,
	})
	UIKit.corner(holder, 4)
	if entry and type(entry.FlagAsset) == "string" and entry.FlagAsset ~= "" then
		UIKit.new("ImageLabel", {
			BackgroundTransparency = 1,
			Size = UDim2.fromScale(1, 1),
			Image = entry.FlagAsset,
			ScaleType = Enum.ScaleType.Crop,
			Parent = holder,
		})
	else
		UIKit.new("TextLabel", {
			BackgroundTransparency = 1,
			Size = UDim2.fromScale(1, 1),
			Text = entry and entry.EmojiFallback or "?",
			TextScaled = true,
			Font = Theme.Fonts.Regular,
			TextColor3 = C.Text,
			Parent = holder,
		})
	end
	return holder
end

-- Scale a centered dialog down on small screens (mobile) so it never covers the whole screen.
function UIKit.autoScale(frame: GuiObject, designWidth: number, designHeight: number)
	local scale = Instance.new("UIScale")
	scale.Name = "FitScale"
	scale.Parent = frame
	local function update()
		local camera = Workspace.CurrentCamera
		if not camera then
			return
		end
		local viewport = camera.ViewportSize
		local s = math.max(math.min((viewport.X - 24) / designWidth, (viewport.Y - 96) / designHeight, 1), 0.55)
		frame:SetAttribute("BaseScale", s)
		scale.Scale = s
	end
	update()
	local camera = Workspace.CurrentCamera
	if camera then
		camera:GetPropertyChangedSignal("ViewportSize"):Connect(update)
	end
	return scale
end

return UIKit
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/BuildMenu.luau'] = r'''-- BuildMenu: compact bottom-center menu. HAMMER -> BUILD -> CATEGORY -> BUILDING.
-- Categories scroll horizontally (touch drag on mobile, mouse wheel / drag on PC).
-- Roads is always the FIRST category so it is always reachable.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local BuildMenuConfig = require(Config:WaitForChild("BuildMenuConfig"))
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local RoadConfig = require(Config:WaitForChild("RoadConfig"))
local BuildingModels = require(Shared:WaitForChild("Modules"):WaitForChild("BuildingModels"))
local RoadModels = require(Shared:WaitForChild("Modules"):WaitForChild("RoadModels"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local BuildMenu = {}
BuildMenu.__index = BuildMenu

local DESIGN_W, DESIGN_H = 560, 214

local function itemsForCategory(categoryId: string)
	local items = {}
	if categoryId == "Roads" then
		for _, roadType in ipairs(RoadConfig.Types) do
			if roadType.Active then
				table.insert(items, {
					Kind = "Road",
					Id = roadType.Id,
					Name = roadType.DisplayName,
					Meta = "Instant",
				})
			end
		end
	else
		for _, def in ipairs(BuildingConfig.Buildings) do
			if def.Category == categoryId and def.Active then
				table.insert(items, {
					Kind = "Building",
					Id = def.Id,
					Name = def.DisplayName,
					Meta = string.format("+%d housing · %ds", def.HousingCapacity or 0, def.BuildTimeSeconds),
					Def = def,
				})
			end
		end
	end
	return items
end

local function viewport(parent, item)
	local frame = UIKit.new("ViewportFrame", {
		BackgroundColor3 = C.SurfaceAlt,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, 70),
		Ambient = Color3.fromRGB(200, 205, 215),
		LightColor = Color3.fromRGB(255, 255, 255),
		LightDirection = Vector3.new(-1, -2, -1),
		Parent = parent,
	})
	UIKit.corner(frame, 8)
	local model
	if item.Kind == "Road" then
		model = RoadModels.build(item.Id)
	else
		model = BuildingModels.build(item.Def, item.Def.Variants[1])
	end
	model.Parent = frame
	local cf, size = model:GetBoundingBox()
	local radius = size.Magnitude / 2
	local camera = Instance.new("Camera")
	camera.FieldOfView = 30
	local direction = Vector3.new(1, 0.9, 1.2).Unit
	camera.CFrame = CFrame.lookAt(cf.Position + direction * radius * 3.4, cf.Position)
	camera.Parent = frame
	frame.CurrentCamera = camera
	return frame
end

function BuildMenu.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, BuildMenu)
	self.callbacks = callbacks
	self.categoryButtons = {}
	self.currentCategory = BuildMenuConfig.Categories[1].Id

	self.panel = UIKit.panel({
		Name = "BuildMenu",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H + 40)
	UIKit.padding(self.panel, 10)

	UIKit.label({
		Text = "BUILD",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		TextColor3 = C.AccentDark,
		Size = UDim2.fromOffset(60, 28),
		Parent = self.panel,
	})
	UIKit.button({
		Text = "Close",
		TextSize = T.TextSize.Small,
		Style = "ghost",
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.fromOffset(60, 28),
		Parent = self.panel,
		OnClick = function()
			self:hide()
			self.callbacks.onClose()
		end,
	})

	self.categories = UIKit.hScroll({
		Name = "Categories",
		Position = UDim2.fromOffset(64, 0),
		Size = UDim2.new(1, -64 - 66, 0, 32),
		Spacing = 6,
		Parent = self.panel,
	})
	for i, category in ipairs(BuildMenuConfig.Categories) do
		local b = UIKit.button({
			Text = category.DisplayName,
			TextSize = T.TextSize.Small,
			Size = UDim2.fromOffset(96, 28),
			Radius = 999,
			LayoutOrder = i,
			Parent = self.categories,
			OnClick = function()
				self:selectCategory(category.Id)
			end,
		})
		self.categoryButtons[category.Id] = b
	end

	self.items = UIKit.hScroll({
		Name = "Items",
		Position = UDim2.fromOffset(0, 40),
		Size = UDim2.new(1, 0, 1, -40),
		Spacing = 8,
		Parent = self.panel,
	})
	return self
end

function BuildMenu:selectCategory(categoryId: string)
	self.currentCategory = categoryId
	for id, b in pairs(self.categoryButtons) do
		b.setSelected(id == categoryId)
	end
	for _, child in ipairs(self.items:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	self.items.CanvasPosition = Vector2.new(0, 0)
	local items = itemsForCategory(categoryId)
	if #items == 0 then
		UIKit.label({
			Text = "Planned for a future update",
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			TextXAlignment = Enum.TextXAlignment.Center,
			Size = UDim2.fromOffset(DESIGN_W - 20, 120),
			Parent = self.items,
		})
		return
	end
	for i, item in ipairs(items) do
		local card = UIKit.button({
			Name = item.Id,
			Text = "",
			Size = UDim2.fromOffset(118, 124),
			LayoutOrder = i,
			Parent = self.items,
			OnClick = function()
				self:hide()
				self.callbacks.onSelect(item.Kind, item.Id)
			end,
		})
		UIKit.padding(card.Instance, 6)
		local vp = viewport(card.Instance, item)
		vp.Active = false
		UIKit.label({
			Text = item.Name,
			Font = T.Fonts.Bold,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(0, 76),
			Size = UDim2.new(1, 0, 0, 18),
			Parent = card.Instance,
		})
		UIKit.label({
			Text = item.Meta,
			TextColor3 = C.TextMuted,
			TextSize = 11,
			Position = UDim2.fromOffset(0, 96),
			Size = UDim2.new(1, 0, 0, 16),
			Parent = card.Instance,
		})
	end
end

function BuildMenu:show(categoryId: string?)
	self:selectCategory(categoryId or self.currentCategory)
	UIKit.open(self.panel)
end

function BuildMenu:hide()
	UIKit.close(self.panel)
end

function BuildMenu:isOpen(): boolean
	return self.panel.Visible
end

return BuildMenu
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/CreateStateScreen.luau'] = r'''-- CreateStateScreen: Country Name -> Flag (Continent -> Country) -> Technology Branch -> Create.
-- Name, Flag and Technology are independent (e.g. "Novaria" + Germany flag + USSR / Russia tech).
-- The client only collects choices; the server validates and creates the country.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Countries = require(Shared:WaitForChild("Modules"):WaitForChild("Countries"))
local TechnologyConfig = require(Shared:WaitForChild("Config"):WaitForChild("TechnologyConfig"))
local GameConfig = require(Shared:WaitForChild("Config"):WaitForChild("GameConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local CreateStateScreen = {}
CreateStateScreen.__index = CreateStateScreen

local DESIGN_W, DESIGN_H = 420, 470
local STEPS = { "Name", "Flag", "Technology", "Review" }

function CreateStateScreen.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, CreateStateScreen)
	self.callbacks = callbacks
	self.choice = { Name = "", FlagId = nil, Continent = nil, TechnologyBranch = nil }
	self.step = 1
	self.browseContinent = nil
	self.search = ""

	self.panel = UIKit.panel({
		Name = "CreateStateScreen",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H)
	UIKit.padding(self.panel, 18)

	self.title = UIKit.label({
		Text = "Create State",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Title,
		Size = UDim2.new(1, 0, 0, 22),
		Parent = self.panel,
	})
	self.stepLabel = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(0, 24),
		Size = UDim2.new(1, 0, 0, 16),
		Parent = self.panel,
	})
	self.dots = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, 0, 0, 6),
		Size = UDim2.fromOffset(4 * 18, 10),
		Parent = self.panel,
	})
	UIKit.list(self.dots, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Right)
	self.dotFrames = {}
	for i = 1, #STEPS do
		local dot = UIKit.new("Frame", {
			BackgroundColor3 = C.Stroke,
			BorderSizePixel = 0,
			Size = UDim2.fromOffset(10, 10),
			LayoutOrder = i,
			Parent = self.dots,
		})
		UIKit.corner(dot, 999)
		self.dotFrames[i] = dot
	end

	self.content = UIKit.new("Frame", {
		Name = "Content",
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 50),
		Size = UDim2.new(1, 0, 1, -50 - 48),
		ClipsDescendants = true,
		Parent = self.panel,
	})

	self.error = UIKit.label({
		Text = "",
		TextColor3 = C.Danger,
		TextSize = T.TextSize.Small,
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, -42),
		Size = UDim2.new(1, 0, 0, 16),
		Parent = self.panel,
	})

	self.backButton = UIKit.button({
		Text = "Back",
		Size = UDim2.fromOffset(96, 36),
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Parent = self.panel,
		OnClick = function()
			self:back()
		end,
	})
	self.nextButton = UIKit.button({
		Text = "Next",
		Style = "primary",
		Size = UDim2.fromOffset(120, 36),
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.fromScale(1, 1),
		Parent = self.panel,
		OnClick = function()
			self:next()
		end,
	})
	return self
end

function CreateStateScreen:setError(text: string?)
	self.error.Text = text or ""
end

function CreateStateScreen:clearContent()
	for _, child in ipairs(self.content:GetChildren()) do
		child:Destroy()
	end
end

function CreateStateScreen:canContinue(): (boolean, string?)
	if self.step == 1 then
		local name = string.match(self.choice.Name or "", "^%s*(.-)%s*$") or ""
		if #name < GameConfig.CountryName.MinLength then
			return false, "Name must be at least " .. GameConfig.CountryName.MinLength .. " characters"
		end
		if #name > GameConfig.CountryName.MaxLength then
			return false, "Name is too long"
		end
		return true, nil
	elseif self.step == 2 then
		if not self.choice.FlagId then
			return false, "Select a continent, then a country"
		end
		return true, nil
	elseif self.step == 3 then
		if not self.choice.TechnologyBranch then
			return false, "Select a technology branch"
		end
		return true, nil
	end
	return true, nil
end

function CreateStateScreen:renderName()
	UIKit.label({
		Text = "Country name",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local box = UIKit.new("TextBox", {
		Name = "NameInput",
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 0, 40),
		Font = T.Fonts.Medium,
		TextSize = T.TextSize.Body,
		TextColor3 = C.Text,
		PlaceholderText = "e.g. Novaria",
		PlaceholderColor3 = C.TextMuted,
		Text = self.choice.Name,
		ClearTextOnFocus = false,
		TextXAlignment = Enum.TextXAlignment.Left,
		Parent = self.content,
	})
	UIKit.corner(box, T.Radius.Small)
	local stroke = UIKit.stroke(box, C.Stroke)
	UIKit.padding(box, 0, 12)
	box.Focused:Connect(function()
		UIKit.tween(stroke, T.Motion.Fast, { Color = C.Accent })
	end)
	box.FocusLost:Connect(function()
		UIKit.tween(stroke, T.Motion.Fast, { Color = C.Stroke })
	end)
	box:GetPropertyChangedSignal("Text"):Connect(function()
		if #box.Text > GameConfig.CountryName.MaxLength then
			box.Text = string.sub(box.Text, 1, GameConfig.CountryName.MaxLength)
		end
		self.choice.Name = box.Text
		self:setError(nil)
	end)
	UIKit.label({
		Text = string.format(
			"%d-%d characters. Your name, flag and technology are independent choices.",
			GameConfig.CountryName.MinLength,
			GameConfig.CountryName.MaxLength
		),
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Position = UDim2.fromOffset(0, 74),
		Size = UDim2.new(1, 0, 0, 32),
		Parent = self.content,
	})
end

function CreateStateScreen:renderContinents()
	UIKit.label({
		Text = "Select continent",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local grid = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 1, -26),
		Parent = self.content,
	})
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.new(0.5, -4, 0, 52)
	layout.CellPadding = UDim2.fromOffset(8, 8)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = grid
	for i, continent in ipairs(Countries.Continents) do
		local count = #Countries.forContinent(continent)
		local b = UIKit.button({
			Text = string.upper(continent) .. "\n" .. count .. " countries",
			TextSize = T.TextSize.Small,
			LayoutOrder = i,
			Parent = grid,
			OnClick = function()
				self.browseContinent = continent
				self.search = ""
				self:render()
			end,
		})
		if self.choice.Continent == continent then
			b.setSelected(true)
		end
	end
end

function CreateStateScreen:renderCountries()
	local continent = self.browseContinent
	UIKit.button({
		Text = "< Continents",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(104, 28),
		Style = "ghost",
		Parent = self.content,
		OnClick = function()
			self.browseContinent = nil
			self:render()
		end,
	})
	UIKit.label({
		Text = string.upper(continent),
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		TextXAlignment = Enum.TextXAlignment.Right,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.new(0.5, 0, 0, 28),
		Parent = self.content,
	})
	local search = UIKit.new("TextBox", {
		Name = "Search",
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 34),
		Size = UDim2.new(1, 0, 0, 30),
		Font = T.Fonts.Regular,
		TextSize = T.TextSize.Small,
		TextColor3 = C.Text,
		PlaceholderText = "Search in " .. continent .. " (optional)",
		PlaceholderColor3 = C.TextMuted,
		Text = self.search,
		ClearTextOnFocus = false,
		TextXAlignment = Enum.TextXAlignment.Left,
		Parent = self.content,
	})
	UIKit.corner(search, T.Radius.Small)
	UIKit.stroke(search, C.Stroke)
	UIKit.padding(search, 0, 10)

	local list = UIKit.vScroll({
		Name = "CountryList",
		Position = UDim2.fromOffset(0, 70),
		Size = UDim2.new(1, 0, 1, -70),
		Parent = self.content,
	})
	local layout = Instance.new("UIGridLayout")
	layout.CellSize = UDim2.new(0.5, -6, 0, 36)
	layout.CellPadding = UDim2.fromOffset(6, 6)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = list
	UIKit.padding(list, 2, 2)

	local buttons = {}
	local function populate()
		for _, b in ipairs(buttons) do
			b.Instance:Destroy()
		end
		buttons = {}
		for i, entry in ipairs(Countries.search(self.search, continent)) do
			local b
			b = UIKit.button({
				Text = "",
				LayoutOrder = i,
				Parent = list,
				OnClick = function()
					self.choice.FlagId = entry.Id
					self.choice.Continent = entry.Continent
					self:setError(nil)
					for _, other in ipairs(buttons) do
						other.setSelected(other == b)
					end
				end,
			})
			local flag = UIKit.flag(b.Instance, entry, 18)
			flag.AnchorPoint = Vector2.new(0, 0.5)
			flag.Position = UDim2.new(0, 8, 0.5, 0)
			UIKit.label({
				Text = entry.DisplayNameEN,
				TextSize = T.TextSize.Small,
				Position = UDim2.fromOffset(40, 0),
				Size = UDim2.new(1, -46, 1, 0),
				Parent = b.Instance,
			})
			if self.choice.FlagId == entry.Id then
				b.setSelected(true)
			end
			table.insert(buttons, b)
		end
	end
	populate()
	search:GetPropertyChangedSignal("Text"):Connect(function()
		self.search = search.Text
		populate()
	end)
end

function CreateStateScreen:renderTechnology()
	UIKit.label({
		Text = "Technology branch",
		Font = T.Fonts.Medium,
		Size = UDim2.new(1, 0, 0, 18),
		Parent = self.content,
	})
	local holder = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 26),
		Size = UDim2.new(1, 0, 1, -26),
		Parent = self.content,
	})
	UIKit.list(holder, Enum.FillDirection.Vertical, 8)
	local buttons = {}
	for i, branch in ipairs(TechnologyConfig.Branches) do
		local b
		b = UIKit.button({
			Text = "",
			Size = UDim2.new(1, 0, 0, 58),
			LayoutOrder = i,
			Parent = holder,
			OnClick = function()
				self.choice.TechnologyBranch = branch.Id
				self:setError(nil)
				for _, other in ipairs(buttons) do
					other.setSelected(other == b)
				end
			end,
		})
		UIKit.label({
			Text = branch.DisplayName,
			Font = T.Fonts.Bold,
			Position = UDim2.fromOffset(14, 8),
			Size = UDim2.new(1, -28, 0, 20),
			Parent = b.Instance,
		})
		UIKit.label({
			Text = branch.Description,
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(14, 30),
			Size = UDim2.new(1, -28, 0, 18),
			Parent = b.Instance,
		})
		if self.choice.TechnologyBranch == branch.Id then
			b.setSelected(true)
		end
		table.insert(buttons, b)
	end
end

function CreateStateScreen:renderReview()
	local entry = Countries.get(self.choice.FlagId or "")
	local techName = self.choice.TechnologyBranch
	for _, branch in ipairs(TechnologyConfig.Branches) do
		if branch.Id == self.choice.TechnologyBranch then
			techName = branch.DisplayName
		end
	end
	local card = UIKit.new("Frame", {
		BackgroundColor3 = C.Surface,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, 150),
		Parent = self.content,
	})
	UIKit.corner(card, T.Radius.Small)
	UIKit.stroke(card, C.Stroke)
	UIKit.padding(card, 14)
	local flag = UIKit.flag(card, entry, 34)
	flag.Position = UDim2.fromOffset(0, 0)
	UIKit.label({
		Text = self.choice.Name,
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Title,
		Position = UDim2.fromOffset(60, 0),
		Size = UDim2.new(1, -60, 0, 22),
		Parent = card,
	})
	UIKit.label({
		Text = "Flag: " .. (entry and entry.DisplayNameEN or "-") .. " · " .. (self.choice.Continent or ""),
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(60, 24),
		Size = UDim2.new(1, -60, 0, 16),
		Parent = card,
	})
	UIKit.label({
		Text = "Technology: " .. tostring(techName),
		TextColor3 = C.Text,
		TextSize = T.TextSize.Small,
		Position = UDim2.fromOffset(0, 56),
		Size = UDim2.new(1, 0, 0, 18),
		Parent = card,
	})
	UIKit.label({
		Text = "Your state starts empty: no money, citizens, houses or roads. Build it from zero.",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Position = UDim2.fromOffset(0, 80),
		Size = UDim2.new(1, 0, 0, 36),
		Parent = card,
	})
end

function CreateStateScreen:render()
	self:clearContent()
	self.stepLabel.Text = string.format("Step %d of %d · %s", self.step, #STEPS, STEPS[self.step])
	for i, dot in ipairs(self.dotFrames) do
		UIKit.tween(dot, T.Motion.Normal, { BackgroundColor3 = (i <= self.step) and C.Accent or C.Stroke })
	end
	self.backButton.setText(self.step == 1 and "Cancel" or "Back")
	self.nextButton.setText(self.step == #STEPS and "Create State" or "Next")
	if self.step == 1 then
		self:renderName()
	elseif self.step == 2 then
		if self.browseContinent then
			self:renderCountries()
		else
			self:renderContinents()
		end
	elseif self.step == 3 then
		self:renderTechnology()
	else
		self:renderReview()
	end
end

function CreateStateScreen:next()
	if self.submitting then
		return
	end
	local ok, reason = self:canContinue()
	if not ok then
		self:setError(reason)
		return
	end
	self:setError(nil)
	if self.step < #STEPS then
		self.step += 1
		if self.step == 2 then
			self.browseContinent = self.choice.Continent
		end
		self:render()
		return
	end
	self.submitting = true
	self.nextButton.setText("Creating...")
	local payload = {
		Name = string.match(self.choice.Name, "^%s*(.-)%s*$"),
		FlagId = self.choice.FlagId,
		Continent = self.choice.Continent,
		TechnologyBranch = self.choice.TechnologyBranch,
	}
	task.spawn(function()
		local result = self.callbacks.onSubmit(self.slotIndex, payload)
		self.submitting = false
		if result and result.ok then
			self:hide()
		else
			self.nextButton.setText("Create State")
			self:setError(result and result.error or "Could not create state")
		end
	end)
end

function CreateStateScreen:back()
	if self.submitting then
		return
	end
	self:setError(nil)
	if self.step == 2 and self.browseContinent then
		self.browseContinent = nil
		self:render()
		return
	end
	if self.step == 1 then
		self:hide()
		self.callbacks.onCancel()
		return
	end
	self.step -= 1
	self:render()
end

function CreateStateScreen:show(slotIndex: number)
	self.slotIndex = slotIndex
	self.choice = { Name = "", FlagId = nil, Continent = nil, TechnologyBranch = nil }
	self.step = 1
	self.browseContinent = nil
	self.search = ""
	self.submitting = false
	self:setError(nil)
	self.title.Text = "Create State · Slot " .. slotIndex
	self:render()
	UIKit.open(self.panel)
end

function CreateStateScreen:hide()
	UIKit.close(self.panel)
end

return CreateStateScreen
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/HUD.luau'] = r'''-- HUD: TOP CENTER menu + country + population indicator; BOTTOM CENTER hammer (Build).
-- Compact pills only. Respects the Roblox Core UI safe inset (ScreenGui.ScreenInsets).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Countries = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Modules"):WaitForChild("Countries"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local HUD = {}
HUD.__index = HUD

function HUD.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, HUD)
	self.callbacks = callbacks

	-- TOP CENTER bar
	self.top = UIKit.new("Frame", {
		Name = "TopCenter",
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 8),
		Size = UDim2.fromOffset(0, 38),
		AutomaticSize = Enum.AutomaticSize.X,
		Visible = false,
		Parent = root,
	})
	UIKit.corner(self.top, 999)
	UIKit.stroke(self.top, C.Stroke)
	UIKit.padding(self.top, 4, 6)
	UIKit.list(self.top, Enum.FillDirection.Horizontal, 8, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)

	self.menuButton = UIKit.button({
		Name = "Menu",
		Text = "Menu",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(58, 30),
		Radius = 999,
		LayoutOrder = 1,
		Parent = self.top,
		OnClick = function()
			self:toggleMenu()
		end,
	})

	self.flagHolder = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Size = UDim2.fromOffset(25, 18),
		LayoutOrder = 2,
		Parent = self.top,
	})
	self.nameLabel = UIKit.label({
		Text = "",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 3,
		Parent = self.top,
	})
	UIKit.new("Frame", {
		BackgroundColor3 = C.Stroke,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(1, 18),
		LayoutOrder = 4,
		Parent = self.top,
	})
	self.popLabel = UIKit.label({
		Name = "Population",
		Text = "Population 0 / 0",
		TextSize = T.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 5,
		Parent = self.top,
	})
	self.saveChip = UIKit.label({
		Text = "Saving off",
		TextColor3 = C.Danger,
		TextSize = 11,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		LayoutOrder = 6,
		Visible = false,
		Parent = self.top,
	})

	-- Menu popover (under the top bar)
	self.menu = UIKit.panel({
		Name = "MenuPopover",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 52),
		Size = UDim2.fromOffset(180, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		Visible = false,
		Parent = root,
	})
	UIKit.padding(self.menu, 8)
	UIKit.list(self.menu, Enum.FillDirection.Vertical, 6)
	UIKit.button({
		Text = "Save now",
		Size = UDim2.new(1, 0, 0, 32),
		LayoutOrder = 1,
		Parent = self.menu,
		OnClick = function()
			self:closeMenu()
			self.callbacks.onSave()
		end,
	})
	UIKit.button({
		Text = "Change slot",
		Size = UDim2.new(1, 0, 0, 32),
		LayoutOrder = 2,
		Parent = self.menu,
		OnClick = function()
			self:closeMenu()
			self.callbacks.onChangeSlot()
		end,
	})
	self.statsLabel = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = 11,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Size = UDim2.new(1, 0, 0, 44),
		LayoutOrder = 3,
		Parent = self.menu,
	})

	-- BOTTOM CENTER hammer
	self.hammer = UIKit.new("TextButton", {
		Name = "Hammer",
		AutoButtonColor = false,
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(60, 60),
		Text = "",
		Visible = false,
		Parent = root,
	})
	UIKit.corner(self.hammer, 999)
	local hammerStroke = UIKit.stroke(self.hammer, C.Stroke, 1.5)
	local hammerScale = Instance.new("UIScale")
	hammerScale.Parent = self.hammer
	UIKit.label({
		Text = "🔨",
		TextSize = 22,
		TextXAlignment = Enum.TextXAlignment.Center,
		Position = UDim2.fromOffset(0, 8),
		Size = UDim2.new(1, 0, 0, 26),
		Parent = self.hammer,
	})
	UIKit.label({
		Text = "BUILD",
		Font = T.Fonts.Bold,
		TextSize = 10,
		TextColor3 = C.AccentDark,
		TextXAlignment = Enum.TextXAlignment.Center,
		Position = UDim2.fromOffset(0, 36),
		Size = UDim2.new(1, 0, 0, 14),
		Parent = self.hammer,
	})
	self.hammer.MouseEnter:Connect(function()
		UIKit.tween(self.hammer, T.Motion.Fast, { BackgroundColor3 = C.Surface })
		UIKit.tween(hammerStroke, T.Motion.Fast, { Color = C.Accent })
	end)
	self.hammer.MouseLeave:Connect(function()
		UIKit.tween(self.hammer, T.Motion.Fast, { BackgroundColor3 = C.Background })
		UIKit.tween(hammerStroke, T.Motion.Fast, { Color = C.Stroke })
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 1 })
	end)
	self.hammer.MouseButton1Down:Connect(function()
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 0.94 })
	end)
	self.hammer.MouseButton1Up:Connect(function()
		UIKit.tween(hammerScale, T.Motion.Fast, { Scale = 1 })
	end)
	self.hammer.Activated:Connect(function()
		self:toggleTools()
	end)

	-- Hammer tool popover: HAMMER -> BUILD
	self.tools = UIKit.panel({
		Name = "HammerTools",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -84),
		Size = UDim2.fromOffset(0, 48),
		AutomaticSize = Enum.AutomaticSize.X,
		Visible = false,
		Parent = root,
	})
	UIKit.padding(self.tools, 6)
	UIKit.list(self.tools, Enum.FillDirection.Horizontal, 6, nil, Enum.VerticalAlignment.Center)
	UIKit.button({
		Text = "Build",
		Style = "primary",
		Size = UDim2.fromOffset(92, 36),
		LayoutOrder = 1,
		Parent = self.tools,
		OnClick = function()
			self:closeTools()
			self.callbacks.onOpenBuild()
		end,
	})
	local demolish = UIKit.button({
		Text = "Demolish · soon",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(120, 36),
		LayoutOrder = 2,
		Parent = self.tools,
	})
	demolish.setDisabled(true)
	return self
end

function HUD:toggleTools()
	if self.tools.Visible then
		self:closeTools()
	else
		self.callbacks.onHammer()
		UIKit.open(self.tools)
	end
end

function HUD:closeTools()
	UIKit.close(self.tools)
end

function HUD:toggleMenu()
	if self.menu.Visible then
		self:closeMenu()
	else
		UIKit.open(self.menu, -6)
	end
end

function HUD:closeMenu()
	UIKit.close(self.menu, -6)
end

function HUD:setHammerVisible(visible: boolean)
	self.hammer.Visible = visible
	if not visible then
		self.tools.Visible = false
	end
end

function HUD:show()
	UIKit.open(self.top, -8)
	self.hammer.Visible = true
end

function HUD:hide()
	self.top.Visible = false
	self.menu.Visible = false
	self.tools.Visible = false
	self.hammer.Visible = false
end

function HUD:update(state)
	if not state or not state.Active then
		return
	end
	if self.lastFlag ~= state.FlagId then
		self.lastFlag = state.FlagId
		for _, child in ipairs(self.flagHolder:GetChildren()) do
			child:Destroy()
		end
		local flag = UIKit.flag(self.flagHolder, Countries.get(state.FlagId or ""), 18)
		flag.Size = UDim2.fromScale(1, 1)
	end
	self.nameLabel.Text = state.Name or ""
	local previous = self.lastPopulation
	self.popLabel.Text = string.format("Population %d / %d", state.Population or 0, state.HousingCapacity or 0)
	if previous ~= nil and state.Population ~= previous then
		self.popLabel.TextColor3 = C.AccentDark
		UIKit.tween(self.popLabel, T.Motion.Slow, { TextColor3 = C.Text })
	end
	self.lastPopulation = state.Population
	self.saveChip.Visible = state.Persistent == false
	self.statsLabel.Text = string.format(
		"Buildings %d (%d building) · Roads %d · Workers %d",
		state.BuildingCount or 0,
		state.UnderConstruction or 0,
		state.RoadCount or 0,
		state.Workers or 0
	)
end

return HUD
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/PlacementBar.luau'] = r'''-- PlacementBar: bottom-center controls while placing (works on PC and mobile).
-- Shows validity: valid = neutral text, invalid = subtle red reason.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Config = ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local RoadConfig = require(Config:WaitForChild("RoadConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local PlacementBar = {}
PlacementBar.__index = PlacementBar

local DESIGN_W, DESIGN_H = 440, 92

local function displayName(kind, id)
	local list = kind == "Road" and RoadConfig.Types or BuildingConfig.Buildings
	for _, entry in ipairs(list) do
		if entry.Id == id then
			return entry.DisplayName
		end
	end
	return id
end

function PlacementBar.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, PlacementBar)
	self.panel = UIKit.panel({
		Name = "PlacementBar",
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, -14),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H + 40)
	UIKit.padding(self.panel, 10)
	self.title = UIKit.label({
		Text = "",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Small,
		Size = UDim2.new(0.5, 0, 0, 18),
		Parent = self.panel,
	})
	self.status = UIKit.label({
		Text = "",
		TextSize = T.TextSize.Small,
		TextColor3 = C.TextMuted,
		TextXAlignment = Enum.TextXAlignment.Right,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.fromScale(1, 0),
		Size = UDim2.new(0.5, 0, 0, 18),
		Parent = self.panel,
	})
	local row = UIKit.new("Frame", {
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(0, 28),
		Size = UDim2.new(1, 0, 0, 42),
		Parent = self.panel,
	})
	UIKit.list(row, Enum.FillDirection.Horizontal, 6, Enum.HorizontalAlignment.Center, Enum.VerticalAlignment.Center)
	self.styleButton = UIKit.button({
		Text = "Style A",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(84, 38),
		LayoutOrder = 1,
		Parent = row,
		OnClick = callbacks.onStyle,
	})
	UIKit.button({
		Text = "Rotate (R)",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(96, 38),
		LayoutOrder = 2,
		Parent = row,
		OnClick = callbacks.onRotate,
	})
	self.placeButton = UIKit.button({
		Text = "Place",
		Style = "primary",
		Size = UDim2.fromOffset(110, 38),
		LayoutOrder = 3,
		Parent = row,
		OnClick = callbacks.onPlace,
	})
	UIKit.button({
		Text = "Done (Q)",
		TextSize = T.TextSize.Small,
		Size = UDim2.fromOffset(90, 38),
		LayoutOrder = 4,
		Parent = row,
		OnClick = callbacks.onDone,
	})
	return self
end

function PlacementBar:update(status)
	if not status.Active then
		return
	end
	self.title.Text = displayName(status.Kind, status.Id)
	self.styleButton.Instance.Visible = status.Kind == "Building"
	if status.Variant then
		local letter = string.match(status.Variant, "_(%w+)$") or "A"
		self.styleButton.setText("Style " .. letter)
	end
	if status.Valid then
		self.status.Text = "Ready to place"
		self.status.TextColor3 = C.TextMuted
	else
		self.status.Text = status.Reason or "Invalid placement"
		self.status.TextColor3 = C.Danger
	end
	self.placeButton.setDisabled(not status.Valid)
end

function PlacementBar:show()
	UIKit.open(self.panel)
end

function PlacementBar:hide()
	UIKit.close(self.panel)
end

return PlacementBar
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/SlotScreen.luau'] = r'''-- SlotScreen: exactly 3 save slots. Slot 1 FREE, slots 2-3 LOCKED (no monetization yet).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local Countries = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Modules"):WaitForChild("Countries"))
local TechnologyConfig =
	require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Config"):WaitForChild("TechnologyConfig"))

local C = UIKit.Theme.Colors
local T = UIKit.Theme

local SlotScreen = {}
SlotScreen.__index = SlotScreen

local DESIGN_W, DESIGN_H = 360, 350

local function techName(id)
	for _, branch in ipairs(TechnologyConfig.Branches) do
		if branch.Id == id then
			return branch.DisplayName
		end
	end
	return id or ""
end

function SlotScreen.new(root: ScreenGui, callbacks)
	local self = setmetatable({}, SlotScreen)
	self.callbacks = callbacks
	self.panel = UIKit.panel({
		Name = "SlotScreen",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(DESIGN_W, DESIGN_H),
		Visible = false,
		Parent = root,
	})
	UIKit.autoScale(self.panel, DESIGN_W, DESIGN_H)
	UIKit.padding(self.panel, 18)
	UIKit.list(self.panel, Enum.FillDirection.Vertical, 8)

	UIKit.label({
		Text = "WAR STATE",
		Font = T.Fonts.Bold,
		TextSize = T.TextSize.Header,
		Size = UDim2.new(1, 0, 0, 26),
		LayoutOrder = 1,
		Parent = self.panel,
	})
	UIKit.label({
		Text = "Select a save slot",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		Size = UDim2.new(1, 0, 0, 16),
		LayoutOrder = 2,
		Parent = self.panel,
	})
	self.rows = UIKit.new("Frame", {
		Name = "Rows",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 3 * 64 + 2 * 8),
		LayoutOrder = 3,
		Parent = self.panel,
	})
	UIKit.list(self.rows, Enum.FillDirection.Vertical, 8)
	self.note = UIKit.label({
		Text = "",
		TextColor3 = C.TextMuted,
		TextSize = T.TextSize.Small,
		TextWrapped = true,
		TextTruncate = Enum.TextTruncate.None,
		Size = UDim2.new(1, 0, 0, 30),
		LayoutOrder = 4,
		Parent = self.panel,
	})
	return self
end

function SlotScreen:render(profile)
	for _, child in ipairs(self.rows:GetChildren()) do
		if child:IsA("GuiObject") then
			child:Destroy()
		end
	end
	for _, slot in ipairs(profile.slots) do
		local row = UIKit.new("Frame", {
			Name = "Slot" .. slot.Index,
			BackgroundColor3 = slot.Locked and C.Surface or C.Background,
			BorderSizePixel = 0,
			Size = UDim2.new(1, 0, 0, 64),
			LayoutOrder = slot.Index,
			Parent = self.rows,
		})
		UIKit.corner(row, T.Radius.Small)
		UIKit.stroke(row, C.Stroke)
		UIKit.padding(row, 10, 12)

		local title = "SLOT " .. slot.Index
		local subtitle
		if slot.Locked then
			subtitle = "Locked"
		elseif slot.Empty then
			subtitle = "Free · Empty"
		else
			subtitle = string.format("%s · Pop %d", techName(slot.TechnologyBranch), slot.Population or 0)
			title = slot.Name or title
		end

		local flagEntry = (not slot.Empty) and Countries.get(slot.FlagId or "") or nil
		local textX = 0
		if flagEntry then
			local flag = UIKit.flag(row, flagEntry, 26)
			flag.AnchorPoint = Vector2.new(0, 0.5)
			flag.Position = UDim2.fromScale(0, 0.5)
			textX = 44
		end
		UIKit.label({
			Text = title,
			Font = T.Fonts.Bold,
			Position = UDim2.fromOffset(textX, 2),
			Size = UDim2.new(1, -(textX + 150), 0, 20),
			TextColor3 = slot.Locked and C.TextMuted or C.Text,
			Parent = row,
		})
		UIKit.label({
			Text = subtitle,
			TextColor3 = C.TextMuted,
			TextSize = T.TextSize.Small,
			Position = UDim2.fromOffset(textX, 24),
			Size = UDim2.new(1, -(textX + 150), 0, 16),
			Parent = row,
		})

		if slot.Locked then
			local lock = UIKit.button({
				Text = "Locked",
				Size = UDim2.fromOffset(84, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
			})
			lock.setDisabled(true)
		elseif slot.Empty then
			UIKit.button({
				Text = "Create",
				Style = "primary",
				Size = UDim2.fromOffset(84, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
				OnClick = function()
					self.callbacks.onCreate(slot.Index)
				end,
			})
		else
			UIKit.button({
				Text = "Play",
				Style = "primary",
				Size = UDim2.fromOffset(64, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.fromScale(1, 0.5),
				Parent = row,
				OnClick = function()
					self.callbacks.onPlay(slot.Index)
				end,
			})
			local armed = false
			local delete
			delete = UIKit.button({
				Text = "Delete",
				Style = "danger",
				TextSize = T.TextSize.Small,
				Size = UDim2.fromOffset(70, 32),
				AnchorPoint = Vector2.new(1, 0.5),
				Position = UDim2.new(1, -72, 0.5, 0),
				Parent = row,
				OnClick = function()
					if not armed then
						armed = true
						delete.setText("Confirm")
						task.delay(3, function()
							armed = false
							if delete.Instance.Parent then
								delete.setText("Delete")
							end
						end)
					else
						self.callbacks.onDelete(slot.Index)
					end
				end,
			})
		end
	end
	if profile.persistent then
		self.note.Text = "Progress is saved to your slots."
	else
		self.note.Text = "Saving is OFF this session (Studio API access disabled or DataStore unavailable)."
	end
end

function SlotScreen:show(profile)
	self:render(profile)
	UIKit.open(self.panel)
end

function SlotScreen:hide()
	UIKit.close(self.panel)
end

return SlotScreen
'''

EMBEDDED_FILES['src/StarterGui/MainUI/Screens/Toast.luau'] = r'''-- Toast: small, short-lived notification under the top-center HUD.

local UIKit = require(script.Parent.Parent:WaitForChild("Components"):WaitForChild("UIKit"))
local C = UIKit.Theme.Colors

local Toast = {}
Toast.__index = Toast

function Toast.new(root: ScreenGui)
	local self = setmetatable({}, Toast)
	self.container = UIKit.new("Frame", {
		Name = "Toasts",
		BackgroundTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 58),
		Size = UDim2.fromOffset(320, 120),
		Parent = root,
	})
	UIKit.list(self.container, Enum.FillDirection.Vertical, 6, Enum.HorizontalAlignment.Center)
	return self
end

function Toast:show(text: string, kind: string?)
	local color = C.Text
	if kind == "error" then
		color = C.Danger
	elseif kind == "success" then
		color = C.AccentDark
	end
	local item = UIKit.new("Frame", {
		Name = "Toast",
		BackgroundColor3 = C.Background,
		BorderSizePixel = 0,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		Parent = self.container,
	})
	UIKit.corner(item, 999)
	UIKit.stroke(item, C.Stroke)
	UIKit.padding(item, 0, 14)
	local label = UIKit.label({
		Text = text,
		TextColor3 = color,
		TextSize = UIKit.Theme.TextSize.Small,
		AutomaticSize = Enum.AutomaticSize.X,
		Size = UDim2.fromOffset(0, 30),
		TextXAlignment = Enum.TextXAlignment.Center,
		Parent = item,
	})
	label.TextTransparency = 1
	item.BackgroundTransparency = 1
	UIKit.tween(label, 0.15, { TextTransparency = 0 })
	UIKit.tween(item, 0.15, { BackgroundTransparency = 0 })
	task.delay(2.4, function()
		if item.Parent then
			UIKit.tween(label, 0.2, { TextTransparency = 1 })
			local t = UIKit.tween(item, 0.2, { BackgroundTransparency = 1 })
			t.Completed:Connect(function()
				item:Destroy()
			end)
		end
	end)
	local items = {}
	for _, child in ipairs(self.container:GetChildren()) do
		if child:IsA("Frame") then
			table.insert(items, child)
		end
	end
	if #items > 3 then
		items[1]:Destroy()
	end
end

return Toast
'''

EMBEDDED_FILES['src/StarterPlayer/StarterPlayerScripts/ClientMain.client.luau'] = r'''-- ClientMain: the single client entry point.
-- Client responsibilities: input, UI, preview. Everything permanent is requested from the server.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local player = Players.LocalPlayer
local playerGui = player:WaitForChild("PlayerGui")
local mainUI = playerGui:WaitForChild("MainUI")

mainUI.ResetOnSpawn = false
mainUI.IgnoreGuiInset = false
mainUI.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
pcall(function()
	mainUI.ScreenInsets = Enum.ScreenInsets.CoreUISafeInsets
end)

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local Remotes = ReplicatedStorage:WaitForChild("Remotes")

local Controllers = script.Parent:WaitForChild("Controllers")
local ClientState = require(Controllers:WaitForChild("ClientState"))
local PlacementController = require(Controllers:WaitForChild("PlacementController"))

local Screens = mainUI:WaitForChild("Screens")
local Toast = require(Screens:WaitForChild("Toast"))
local SlotScreen = require(Screens:WaitForChild("SlotScreen"))
local CreateStateScreen = require(Screens:WaitForChild("CreateStateScreen"))
local HUD = require(Screens:WaitForChild("HUD"))
local BuildMenu = require(Screens:WaitForChild("BuildMenu"))
local PlacementBar = require(Screens:WaitForChild("PlacementBar"))

local function remote(name: string)
	return Remotes:WaitForChild(name)
end

local function invoke(name: string, ...)
	local args = table.pack(...)
	local ok, result = pcall(function()
		return remote(name):InvokeServer(table.unpack(args, 1, args.n))
	end)
	if not ok then
		return { ok = false, error = "Connection problem" }
	end
	if type(result) ~= "table" then
		return { ok = false, error = "Unexpected server response" }
	end
	return result
end

player.CameraMaxZoomDistance = math.max(player.CameraMaxZoomDistance, 180)

local toast = Toast.new(mainUI)
local slotScreen, createScreen, hud, buildMenu, placementBar

local function showSlots()
	local profile = invoke(Constants.Remotes.GetProfile)
	if not profile.ok then
		toast:show(profile.error or "Could not load slots", "error")
		task.delay(2, showSlots)
		return
	end
	hud:hide()
	slotScreen:show(profile)
end

local function enterGame(result)
	if not result.ok then
		toast:show(result.error or "Could not enter state", "error")
		return false
	end
	slotScreen:hide()
	if result.state then
		ClientState.set(result.state)
	end
	hud:show()
	hud:update(ClientState.snapshot)
	toast:show("Welcome to " .. tostring(ClientState.snapshot.Name or "your state"), "success")
	return true
end

slotScreen = SlotScreen.new(mainUI, {
	onCreate = function(index)
		slotScreen:hide()
		createScreen:show(index)
	end,
	onPlay = function(index)
		enterGame(invoke(Constants.Remotes.LoadSlot, index))
	end,
	onDelete = function(index)
		local result = invoke(Constants.Remotes.DeleteSlot, index)
		if result.ok then
			toast:show("Slot " .. index .. " deleted")
		else
			toast:show(result.error or "Delete failed", "error")
		end
		showSlots()
	end,
})

createScreen = CreateStateScreen.new(mainUI, {
	onSubmit = function(index, payload)
		local result = invoke(Constants.Remotes.CreateCountry, index, payload)
		if result.ok then
			enterGame(result)
		end
		return result
	end,
	onCancel = function()
		showSlots()
	end,
})

local function exitPlacement()
	PlacementController.cancel()
	placementBar:hide()
	hud:setHammerVisible(true)
end

buildMenu = BuildMenu.new(mainUI, {
	onSelect = function(kind, id)
		hud:setHammerVisible(false)
		PlacementController.start(kind, id)
		placementBar:show()
	end,
	onClose = function()
		hud:setHammerVisible(true)
	end,
})

placementBar = PlacementBar.new(mainUI, {
	onStyle = function()
		PlacementController.cycleVariant()
	end,
	onRotate = function()
		PlacementController.rotate()
	end,
	onPlace = function()
		PlacementController.confirm()
	end,
	onDone = function()
		exitPlacement()
		buildMenu:show()
		hud:setHammerVisible(false)
	end,
})

hud = HUD.new(mainUI, {
	onHammer = function()
		hud:closeMenu()
	end,
	onOpenBuild = function()
		hud:setHammerVisible(false)
		buildMenu:show()
	end,
	onSave = function()
		local result = invoke(Constants.Remotes.SaveNow)
		if result.ok and result.persistent then
			toast:show("Saved", "success")
		elseif result.ok then
			toast:show("Saving is off in this session", "error")
		else
			toast:show(result.error or "Save failed", "error")
		end
	end,
	onChangeSlot = function()
		exitPlacement()
		buildMenu.panel.Visible = false
		local result = invoke(Constants.Remotes.LeaveState)
		if result.ok then
			ClientState.set({ Active = false })
			showSlots()
		else
			toast:show(result.error or "Could not leave", "error")
		end
	end,
})

PlacementController.onStatus(function(status)
	if status.Active then
		placementBar:update(status)
	else
		placementBar:hide()
		if not buildMenu:isOpen() and ClientState.snapshot.Active then
			hud:setHammerVisible(true)
		end
	end
end)

PlacementController.onResult(function(success, message)
	if not success then
		toast:show(message, "error")
	end
end)

remote(Constants.Remotes.StateChanged).OnClientEvent:Connect(function(snapshot)
	ClientState.set(snapshot)
end)

remote(Constants.Remotes.Notify).OnClientEvent:Connect(function(payload)
	if type(payload) == "table" and type(payload.Text) == "string" then
		toast:show(payload.Text, payload.Kind)
	end
end)

ClientState.onChanged(function(snapshot)
	if snapshot.Active then
		hud:update(snapshot)
	end
end)

pcall(function()
	StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
end)

showSlots()
'''

EMBEDDED_FILES['src/StarterPlayer/StarterPlayerScripts/Controllers/ClientState.luau'] = r'''-- ClientState: read-only mirror of the server-authoritative country snapshot.
-- The client NEVER edits gameplay state here; it only displays what the server sent.

local ClientState = {}

local listeners = {}
ClientState.snapshot = { Active = false }

function ClientState.set(snapshot)
	ClientState.snapshot = snapshot or { Active = false }
	for _, fn in ipairs(listeners) do
		task.spawn(fn, ClientState.snapshot)
	end
end

function ClientState.onChanged(fn)
	table.insert(listeners, fn)
	return function()
		local index = table.find(listeners, fn)
		if index then
			table.remove(listeners, index)
		end
	end
end

return ClientState
'''

EMBEDDED_FILES['src/StarterPlayer/StarterPlayerScripts/Controllers/PlacementController.luau'] = r'''-- PlacementController: client-side build preview only.
-- Shows a snapped preview, validates it locally with the SAME PlacementRules the server uses,
-- and sends a placement REQUEST. The server re-validates and decides.
-- PC: mouse to aim, Left click place, R rotate, Q/Esc cancel.
-- Mobile: tap the ground to aim, then use the on-screen Place / Rotate / Cancel buttons.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = Shared:WaitForChild("Config")
local Modules = Shared:WaitForChild("Modules")
local BuildingConfig = require(Config:WaitForChild("BuildingConfig"))
local PlacementConfig = require(Config:WaitForChild("PlacementConfig"))
local Constants = require(Shared:WaitForChild("Constants"):WaitForChild("Constants"))
local GridMath = require(Modules:WaitForChild("GridMath"))
local PlacementRules = require(Modules:WaitForChild("PlacementRules"))
local BuildingModels = require(Modules:WaitForChild("BuildingModels"))
local RoadModels = require(Modules:WaitForChild("RoadModels"))
local Plots = require(Modules:WaitForChild("Plots"))

local player = Players.LocalPlayer
local Remotes = ReplicatedStorage:WaitForChild("Remotes")

local PlacementController = {}

local defsById = {}
for _, def in ipairs(BuildingConfig.Buildings) do
	defsById[def.Id] = def
end

local active = nil -- { kind, id, variantIndex, rotation, model, highlight, valid, reason, info }
local connections = {}
local listeners = {}
local aimScreen = nil -- Vector2 (touch aim point) or nil for mouse
local requesting = false

local INVALID_COLOR = Color3.fromRGB(
	PlacementConfig.PreviewInvalidColor[1],
	PlacementConfig.PreviewInvalidColor[2],
	PlacementConfig.PreviewInvalidColor[3]
)

local function emit()
	local status = PlacementController.getStatus()
	for _, fn in ipairs(listeners) do
		task.spawn(fn, status)
	end
end

function PlacementController.onStatus(fn)
	table.insert(listeners, fn)
end

function PlacementController.getStatus()
	if not active then
		return { Active = false }
	end
	local variantName = nil
	if active.kind == "Building" then
		variantName = defsById[active.id].Variants[active.variantIndex]
	end
	return {
		Active = true,
		Kind = active.kind,
		Id = active.id,
		Variant = variantName,
		Valid = active.valid,
		Reason = active.reason,
		Rotation = active.rotation,
		HasAim = active.info ~= nil,
	}
end

local function plotBounds()
	local index = player:GetAttribute(Constants.Attributes.PlotIndex)
	if not index then
		return nil
	end
	return Plots.getBounds(index)
end

-- Build validation context from replicated world models (server-created, attribute-tagged).
local function buildContext(bounds)
	local ctx = { plot = bounds, buildingRects = {}, roadCells = {} }
	local folderName = "Plot_" .. bounds.index
	local buildings = Workspace:FindFirstChild("Buildings")
	local roads = Workspace:FindFirstChild("Roads")
	local bFolder = buildings and buildings:FindFirstChild(folderName)
	local rFolder = roads and roads:FindFirstChild(folderName)
	local function rectOf(model)
		local minX = model:GetAttribute("RectMinX")
		if minX == nil then
			return nil
		end
		return {
			minX = minX,
			maxX = model:GetAttribute("RectMaxX"),
			minZ = model:GetAttribute("RectMinZ"),
			maxZ = model:GetAttribute("RectMaxZ"),
		}
	end
	if bFolder then
		for _, model in ipairs(bFolder:GetChildren()) do
			local rect = rectOf(model)
			if rect then
				table.insert(ctx.buildingRects, rect)
			end
		end
	end
	if rFolder then
		for _, model in ipairs(rFolder:GetChildren()) do
			local rect = rectOf(model)
			local ix, iz = model:GetAttribute("Ix"), model:GetAttribute("Iz")
			if rect and ix ~= nil and iz ~= nil then
				ctx.roadCells[GridMath.cellKey(ix, iz)] = rect
			end
		end
	end
	return ctx
end

local function setPreviewLook(model, valid: boolean)
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("BasePart") then
			local base = d:GetAttribute("BaseTransparency") or 0
			d.Transparency = math.max(base, PlacementConfig.PreviewTransparency)
		end
	end
	if active and active.highlight then
		active.highlight.Enabled = not valid
	end
end

local function destroyPreview()
	if active and active.model then
		active.model:Destroy()
		active.model = nil
	end
	if active and active.highlight then
		active.highlight:Destroy()
		active.highlight = nil
	end
end

local function createPreview()
	destroyPreview()
	local model
	if active.kind == "Road" then
		model = RoadModels.build(active.id)
	else
		local def = defsById[active.id]
		model = BuildingModels.build(def, def.Variants[active.variantIndex])
	end
	model.Name = "PlacementPreview"
	local highlight = Instance.new("Highlight")
	highlight.Name = "InvalidHighlight"
	highlight.FillColor = INVALID_COLOR
	highlight.OutlineColor = INVALID_COLOR
	highlight.FillTransparency = 0.55
	highlight.OutlineTransparency = 0.4
	highlight.DepthMode = Enum.HighlightDepthMode.Occluded
	highlight.Enabled = false
	highlight.Adornee = model
	highlight.Parent = model
	active.model = model
	active.highlight = highlight
	model.Parent = Workspace.CurrentCamera
	setPreviewLook(model, true)
end

local function raycastGround(screenPoint: Vector2)
	local camera = Workspace.CurrentCamera
	local map = Workspace:FindFirstChild("Map")
	if not camera or not map then
		return nil
	end
	local ray = camera:ViewportPointToRay(screenPoint.X, screenPoint.Y)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Include
	params.FilterDescendantsInstances = { map }
	local result = Workspace:Raycast(ray.Origin, ray.Direction * PlacementConfig.MaxPlacementRayDistance, params)
	return result and result.Position or nil
end

local function currentScreenPoint(): Vector2?
	if aimScreen then
		return aimScreen
	end
	if UserInputService.MouseEnabled then
		-- GetMouseLocation is in viewport space, matching ViewportPointToRay.
		return UserInputService:GetMouseLocation()
	end
	return nil
end

local function update()
	if not active or not active.model then
		return
	end
	local bounds = plotBounds()
	local screenPoint = currentScreenPoint()
	local hit = (bounds and screenPoint) and raycastGround(screenPoint) or nil
	if not hit then
		active.info = nil
		active.valid = false
		active.reason = "Aim at your territory"
		active.model.Parent = nil
		return
	end
	active.model.Parent = Workspace.CurrentCamera
	local ctx = buildContext(bounds)
	local ok, reason, info
	if active.kind == "Road" then
		ok, reason, info = PlacementRules.validateRoad(hit.X, hit.Z, ctx)
	else
		ok, reason, info = PlacementRules.validateBuilding(defsById[active.id], hit.X, hit.Z, active.rotation, ctx)
	end
	active.hitX, active.hitZ = hit.X, hit.Z
	active.info = info
	local changed = active.valid ~= ok or active.reason ~= reason
	active.valid = ok
	active.reason = reason
	if info then
		active.model:PivotTo(
			CFrame.new(info.centerX, bounds.surfaceY + 0.02, info.centerZ)
				* CFrame.Angles(0, GridMath.yawForRotation(active.rotation), 0)
		)
	end
	if changed then
		setPreviewLook(active.model, ok)
		emit()
	end
end

function PlacementController.isActive(): boolean
	return active ~= nil
end

function PlacementController.start(kind: string, id: string)
	PlacementController.cancel()
	active = { kind = kind, id = id, variantIndex = 1, rotation = 0, valid = false, reason = "Aim at your territory" }
	aimScreen = nil
	createPreview()
	table.insert(connections, RunService.RenderStepped:Connect(update))
	table.insert(connections, UserInputService.InputBegan:Connect(function(input, processed)
		if processed then
			return
		end
		if input.KeyCode == Enum.KeyCode.R then
			PlacementController.rotate()
		elseif input.KeyCode == Enum.KeyCode.Q or input.KeyCode == Enum.KeyCode.Escape then
			PlacementController.cancel()
		elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
			aimScreen = nil
			PlacementController.confirm()
		end
	end))
	table.insert(connections, UserInputService.TouchTapInWorld:Connect(function(position, processed)
		if not processed then
			aimScreen = position
		end
	end))
	emit()
end

function PlacementController.rotate()
	if not active then
		return
	end
	active.rotation = (active.rotation + 1) % 4
	active.reason = nil
	emit()
end

function PlacementController.cycleVariant()
	if not active or active.kind ~= "Building" then
		return
	end
	local def = defsById[active.id]
	active.variantIndex = (active.variantIndex % #def.Variants) + 1
	createPreview()
	active.reason = nil
	emit()
end

function PlacementController.cancel()
	for _, c in ipairs(connections) do
		c:Disconnect()
	end
	connections = {}
	destroyPreview()
	local wasActive = active ~= nil
	active = nil
	aimScreen = nil
	if wasActive then
		emit()
	end
end

-- Returns via callback(ok, message). The server is the authority.
function PlacementController.confirm(callback)
	if not active or requesting then
		return
	end
	if not active.info or not active.valid then
		if callback then
			callback(false, active.reason or "Invalid placement")
		end
		emit()
		return
	end
	requesting = true
	local request
	local remote
	if active.kind == "Road" then
		remote = Remotes:WaitForChild(Constants.Remotes.PlaceRoad)
		request = { Type = active.id, X = active.info.centerX, Z = active.info.centerZ, Rotation = active.rotation }
	else
		remote = Remotes:WaitForChild(Constants.Remotes.PlaceBuilding)
		local def = defsById[active.id]
		request = {
			Type = active.id,
			Variant = def.Variants[active.variantIndex],
			X = active.info.centerX,
			Z = active.info.centerZ,
			Rotation = active.rotation,
		}
	end
	task.spawn(function()
		local ok, result = pcall(function()
			return remote:InvokeServer(request)
		end)
		requesting = false
		local success = ok and type(result) == "table" and result.ok == true
		local message = success and "Placed" or ((ok and type(result) == "table" and result.error) or "Request failed")
		for _, fn in ipairs(PlacementController.resultListeners) do
			task.spawn(fn, success, message)
		end
		if callback then
			callback(success, message)
		end
	end)
end

PlacementController.resultListeners = {}
function PlacementController.onResult(fn)
	table.insert(PlacementController.resultListeners, fn)
end

return PlacementController
'''

# ---------------------------------------------------------------------------
# GENERATED (data-driven) SOURCES
# ---------------------------------------------------------------------------
def gen_constants_luau() -> str:
    lines = [
        "-- Constants: GENERATED by build_war_state.py from the Python remote/attribute lists.",
        "-- Edit REMOTE_FUNCTIONS / REMOTE_EVENTS in build_war_state.py, not this file.",
        "",
        "local Constants = {}",
        "",
        "Constants.Remotes = {",
    ]
    for name, _ in REMOTE_FUNCTIONS + REMOTE_EVENTS:
        lines.append(f'\t{name} = "{name}",')
    lines += ["}", "", "Constants.RemoteFunctions = {"]
    for name, _ in REMOTE_FUNCTIONS:
        lines.append(f'\t"{name}",')
    lines += ["}", "", "Constants.RemoteEvents = {"]
    for name, _ in REMOTE_EVENTS:
        lines.append(f'\t"{name}",')
    lines += [
        "}",
        "",
        "Constants.BuildState = {",
        '\tPlanned = "PLANNED",',
        '\tUnderConstruction = "UNDER_CONSTRUCTION",',
        '\tCompleted = "COMPLETED",',
        "}",
        "",
        "Constants.Attributes = {",
        '\tPlotIndex = "PlotIndex",',
        '\tOwnerUserId = "OwnerUserId",',
        '\tKind = "Kind",',
        '\tTypeId = "TypeId",',
        "}",
        "",
        "return Constants",
        "",
    ]
    return "\n".join(lines)


def to_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def list_src_children(root: Path, rel: str):
    """Top-level entries of a src directory, mapped to Rojo instance names."""
    base = root / rel
    result = []
    if not base.is_dir():
        return result
    for entry in sorted(base.iterdir(), key=lambda p: p.name):
        if entry.name.startswith("."):
            continue
        name = entry.name
        for suffix in (".server.luau", ".client.luau", ".luau", ".server.lua", ".client.lua", ".lua", ".json"):
            if entry.is_file() and name.endswith(suffix):
                name = name[: -len(suffix)]
                break
        else:
            if entry.is_file():
                continue
        result.append((name, f"{rel}/{entry.name}"))
    return result


def gen_project_json(root: Path) -> str:
    def mapped(rel):
        node = {}
        for name, path in list_src_children(root, rel):
            node[name] = {"$path": path}
        return node

    remotes = {"$className": "Folder"}
    for name, _ in REMOTE_FUNCTIONS:
        remotes[name] = {"$className": "RemoteFunction"}
    for name, _ in REMOTE_EVENTS:
        remotes[name] = {"$className": "RemoteEvent"}

    replicated = {"$className": "ReplicatedStorage", "$ignoreUnknownInstances": True}
    replicated.update(mapped("src/ReplicatedStorage"))
    replicated["Remotes"] = remotes

    server = {"$className": "ServerScriptService", "$ignoreUnknownInstances": True}
    server.update(mapped("src/ServerScriptService"))

    player_scripts = {"$className": "StarterPlayerScripts", "$ignoreUnknownInstances": True}
    player_scripts.update(mapped("src/StarterPlayer/StarterPlayerScripts"))

    main_ui = {
        "$className": "ScreenGui",
        "$properties": {"ResetOnSpawn": False, "IgnoreGuiInset": False},
    }
    main_ui.update(mapped("src/StarterGui/MainUI"))

    workspace = {"$className": "Workspace", "$ignoreUnknownInstances": True}
    for folder in WORKSPACE_FOLDERS:
        workspace[folder] = {"$path": f"src/Workspace/{folder}", "$ignoreUnknownInstances": True}

    project = {
        "name": "WarState",
        "servePort": ROJO_PORT,
        "tree": {
            "$className": "DataModel",
            "ReplicatedStorage": replicated,
            "ServerScriptService": server,
            "StarterPlayer": {
                "$className": "StarterPlayer",
                "$ignoreUnknownInstances": True,
                "StarterPlayerScripts": player_scripts,
            },
            "StarterGui": {
                "$className": "StarterGui",
                "$ignoreUnknownInstances": True,
                "MainUI": main_ui,
            },
            "Workspace": workspace,
        },
    }
    return to_json(project)


PLUGIN_PROJECT = {"name": "WarStateBridge", "tree": {"$path": "plugin/WarStateBridge.server.luau"}}


def expected_instance_paths(root: Path):
    """Instance paths (for the Studio bridge) that must exist after Rojo sync."""
    paths = []

    def walk(rel_dir: Path, inst_prefix: str):
        for name, path in list_src_children(root, rel_dir.as_posix()):
            inst = f"{inst_prefix}/{name}"
            paths.append(inst)
            full = root / path
            if full.is_dir():
                walk(Path(path), inst)

    walk(Path("src/ReplicatedStorage"), "ReplicatedStorage")
    walk(Path("src/ServerScriptService"), "ServerScriptService")
    walk(Path("src/StarterPlayer/StarterPlayerScripts"), "StarterPlayer/StarterPlayerScripts")
    paths.append("StarterGui/MainUI")
    walk(Path("src/StarterGui/MainUI"), "StarterGui/MainUI")
    for name, _ in REMOTE_FUNCTIONS + REMOTE_EVENTS:
        paths.append(f"ReplicatedStorage/Remotes/{name}")
    for folder in WORKSPACE_FOLDERS:
        paths.append(f"Workspace/{folder}")
    return paths


# ---------------------------------------------------------------------------
# GENERATED PYTHON TESTS (tests/*.py) - standard library unittest
# ---------------------------------------------------------------------------
TEST_COMMON = r'''
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CONFIG = SRC / "ReplicatedStorage" / "Shared" / "Config"


def load_json(name):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")
'''

TEST_FILES = {}

TEST_FILES["tests/test_structure.py"] = TEST_COMMON + r'''

REQUIRED_FILES = [
    "default.project.json",
    "src/ServerScriptService/ServerMain.server.luau",
    "src/ServerScriptService/Systems/Data/DataService.luau",
    "src/ServerScriptService/Systems/Country/CountryService.luau",
    "src/ServerScriptService/Systems/World/WorldService.luau",
    "src/ServerScriptService/Systems/Buildings/BuildingService.luau",
    "src/ServerScriptService/Systems/Construction/ConstructionService.luau",
    "src/ServerScriptService/Systems/Population/PopulationService.luau",
    "src/ServerScriptService/Systems/Roads/RoadService.luau",
    "src/ServerScriptService/Systems/Resources/ResourceService.luau",
    "src/ServerScriptService/Systems/Research/ResearchService.luau",
    "src/ServerScriptService/Systems/Production/ProductionService.luau",
    "src/ServerScriptService/Systems/Economy/EconomyService.luau",
    "src/ServerScriptService/Systems/Military/MilitaryService.luau",
    "src/ServerScriptService/Tests/RuntimeSelfTest.server.luau",
    "src/ReplicatedStorage/Shared/Constants/Constants.luau",
    "src/ReplicatedStorage/Shared/Types/Types.luau",
    "src/ReplicatedStorage/Shared/Config/GameConfig.json",
    "src/ReplicatedStorage/Shared/Config/BuildingConfig.json",
    "src/ReplicatedStorage/Shared/Config/RoadConfig.json",
    "src/ReplicatedStorage/Shared/Config/PlacementConfig.json",
    "src/ReplicatedStorage/Shared/Config/BuildMenuConfig.json",
    "src/ReplicatedStorage/Shared/Config/TechnologyConfig.json",
    "src/ReplicatedStorage/Shared/Config/CountryRegistry.json",
    "src/ReplicatedStorage/Shared/Config/ThemeConfig.luau",
    "src/ReplicatedStorage/Shared/Modules/GridMath.luau",
    "src/ReplicatedStorage/Shared/Modules/PlacementRules.luau",
    "src/ReplicatedStorage/Shared/Modules/RoadGraph.luau",
    "src/ReplicatedStorage/Shared/Modules/BuildingModels.luau",
    "src/ReplicatedStorage/Shared/Modules/RoadModels.luau",
    "src/ReplicatedStorage/Shared/Modules/Countries.luau",
    "src/ReplicatedStorage/Shared/Modules/DefaultCountry.luau",
    "src/ReplicatedStorage/Shared/Modules/Plots.luau",
    "src/StarterPlayer/StarterPlayerScripts/ClientMain.client.luau",
    "src/StarterPlayer/StarterPlayerScripts/Controllers/ClientState.luau",
    "src/StarterPlayer/StarterPlayerScripts/Controllers/PlacementController.luau",
    "src/StarterGui/MainUI/Components/UIKit.luau",
    "src/StarterGui/MainUI/Screens/SlotScreen.luau",
    "src/StarterGui/MainUI/Screens/CreateStateScreen.luau",
    "src/StarterGui/MainUI/Screens/HUD.luau",
    "src/StarterGui/MainUI/Screens/BuildMenu.luau",
    "src/StarterGui/MainUI/Screens/PlacementBar.luau",
    "src/StarterGui/MainUI/Screens/Toast.luau",
    "DEVELOPMENT_ROADMAP.md",
    "AGENTS.md",
]

REQUIRED_DIRS = [
    "src/ReplicatedStorage/Shared/Config",
    "src/ReplicatedStorage/Shared/Constants",
    "src/ReplicatedStorage/Shared/Types",
    "src/ReplicatedStorage/Shared/Modules",
    "src/ReplicatedStorage/Assets",
    "src/Workspace/Map",
    "src/Workspace/Buildings",
    "src/Workspace/Roads",
    "src/Workspace/Vehicles",
    "src/Workspace/NPCs",
]


class StructureTests(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()]
        self.assertEqual(missing, [], "Missing files: %s" % missing)

    def test_required_dirs_exist(self):
        missing = [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
        self.assertEqual(missing, [])

    def test_project_json_paths_exist(self):
        project = json.loads(read("default.project.json"))
        self.assertEqual(project["tree"]["$className"], "DataModel")
        bad = []

        def walk(node):
            for key, value in node.items():
                if key == "$path" and not (ROOT / value).exists():
                    bad.append(value)
                elif isinstance(value, dict) and not key.startswith("$"):
                    walk(value)

        walk(project["tree"])
        self.assertEqual(bad, [])

    def test_services_do_not_wipe_existing_place(self):
        tree = json.loads(read("default.project.json"))["tree"]
        for service in ("ReplicatedStorage", "ServerScriptService", "StarterPlayer", "StarterGui", "Workspace"):
            self.assertIn(service, tree)
            self.assertNotIn("$path", tree[service], "%s must not be mapped wholesale" % service)
            self.assertTrue(tree[service].get("$ignoreUnknownInstances"), service)

    def test_remotes_match_constants(self):
        tree = json.loads(read("default.project.json"))["tree"]
        remotes = {k for k in tree["ReplicatedStorage"]["Remotes"] if not k.startswith("$")}
        constants = read("src/ReplicatedStorage/Shared/Constants/Constants.luau")
        block = re.search(r"Constants\.Remotes = \{(.*?)\n\}", constants, re.S).group(1)
        declared = set(re.findall(r'^\t(\w+) = "\1",$', block, re.M))
        self.assertEqual(remotes, declared)


if __name__ == "__main__":
    unittest.main()
'''

TEST_FILES["tests/test_countries.py"] = TEST_COMMON + r'''

class CountryRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_json("CountryRegistry.json")
        cls.countries = cls.registry["Countries"]

    def test_exactly_195(self):
        self.assertEqual(len(self.countries), 195)

    def test_no_duplicate_ids(self):
        ids = [c["Id"] for c in self.countries]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_duplicate_names(self):
        names = [c["DisplayNameEN"] for c in self.countries]
        self.assertEqual(len(names), len(set(names)))

    def test_required_fields(self):
        for c in self.countries:
            for field in ("Id", "DisplayNameEN", "DisplayNameRU", "Continent", "FlagAsset", "EmojiFallback"):
                self.assertIn(field, c, c.get("Id"))
            self.assertRegex(c["Id"], r"^[A-Z]{2}$")
            self.assertTrue(c["DisplayNameEN"])
            self.assertTrue(c["DisplayNameRU"])

    def test_holy_see_and_palestine(self):
        ids = {c["Id"] for c in self.countries}
        self.assertIn("VA", ids)
        self.assertIn("PS", ids)

    def test_continent_distribution(self):
        continents = self.registry["Continents"]
        self.assertEqual(
            continents, ["Europe", "Asia", "Africa", "North America", "South America", "Oceania"]
        )
        counts = {k: 0 for k in continents}
        for c in self.countries:
            self.assertIn(c["Continent"], counts)
            counts[c["Continent"]] += 1
        self.assertEqual(counts, self.registry["ExpectedContinentCounts"])
        self.assertEqual(sum(counts.values()), 195)

    def test_flag_assets_never_invented(self):
        for c in self.countries:
            asset = c["FlagAsset"]
            self.assertTrue(asset == "" or re.match(r"^rbxassetid://\d+$", asset), c["Id"])

    def test_emoji_fallback_matches_iso(self):
        for c in self.countries:
            expected = "".join(chr(0x1F1E6 + ord(ch) - 65) for ch in c["Id"])
            self.assertEqual(c["EmojiFallback"], expected, c["Id"])


if __name__ == "__main__":
    unittest.main()
'''

TEST_FILES["tests/test_config.py"] = TEST_COMMON + r'''

class GameConfigTests(unittest.TestCase):
    def setUp(self):
        self.game = load_json("GameConfig.json")

    def test_exactly_three_slots(self):
        slots = self.game["Slots"]
        self.assertEqual(self.game["SlotCount"], 3)
        self.assertEqual(len(slots), 3)
        self.assertEqual([s["Unlocked"] for s in slots], [True, False, False])
        self.assertEqual([s["Label"] for s in slots], ["FREE", "LOCKED", "LOCKED"])

    def test_empty_country_defaults(self):
        empty = self.game["EmptyCountry"]
        for key in ("Money", "Oil", "Fuel", "Steel", "Supplies", "Population", "Workers", "HousingCapacity"):
            self.assertEqual(empty[key], 0, key)
        for key in ("Buildings", "Roads", "Military"):
            self.assertEqual(empty[key], {}, key)


class BuildingConfigTests(unittest.TestCase):
    def setUp(self):
        self.buildings = load_json("BuildingConfig.json")["Buildings"]
        self.placement = load_json("PlacementConfig.json")
        self.models = read("src/ReplicatedStorage/Shared/Modules/BuildingModels.luau")

    def test_three_residential_types(self):
        ids = [b["Id"] for b in self.buildings if b["Category"] == "Housing"]
        self.assertEqual(ids, ["SmallHouse", "MediumHouse", "LargeHouse"])

    def test_building_fields(self):
        grid = self.placement["GridSize"]
        for b in self.buildings:
            self.assertGreater(b["HousingCapacity"], 0)
            self.assertGreater(b["BuildTimeSeconds"], 0)
            self.assertEqual(len(b["Footprint"]), 2)
            for side in b["Footprint"]:
                self.assertEqual(side % grid, 0, b["Id"])
                self.assertLessEqual(side, 24, "buildings must stay small")

    def test_variants_exist_in_models(self):
        defined = set(re.findall(r"^Variants\.(\w+) = function", self.models, re.M))
        for b in self.buildings:
            self.assertGreaterEqual(len(b["Variants"]), 4, b["Id"])
            for v in b["Variants"]:
                self.assertIn(v, defined)

    def test_no_permanent_labels_on_buildings(self):
        self.assertNotIn("BillboardGui", self.models)


class RoadAndPlacementTests(unittest.TestCase):
    def setUp(self):
        self.roads = load_json("RoadConfig.json")
        self.placement = load_json("PlacementConfig.json")

    def test_road_types(self):
        ids = [t["Id"] for t in self.roads["Types"]]
        self.assertEqual(ids, ["Straight", "Corner", "TJunction", "Crossroad"])
        expected = {"Straight": 2, "Corner": 2, "TJunction": 3, "Crossroad": 4}
        for t in self.roads["Types"]:
            self.assertEqual(len(t["Openings"]), expected[t["Id"]])
            self.assertTrue(set(t["Openings"]) <= {"N", "E", "S", "W"})

    def test_road_tile_matches_grid(self):
        self.assertEqual(self.roads["TileSize"], self.placement["RoadTileSize"])
        self.assertEqual(self.placement["RoadTileSize"] % self.placement["GridSize"], 0)
        self.assertLess(self.roads["RoadWidth"], self.roads["TileSize"])

    def test_placement_config(self):
        self.assertGreater(self.placement["MaxRoadDistance"], 0)
        self.assertTrue(self.placement["RequireRoadAccess"])
        game = load_json("GameConfig.json")
        self.assertEqual(game["Territory"]["Size"] % self.placement["RoadTileSize"], 0)


class MenuAndTechTests(unittest.TestCase):
    def test_build_menu_categories(self):
        cats = [c["Id"] for c in load_json("BuildMenuConfig.json")["Categories"]]
        self.assertEqual(
            cats,
            ["Roads", "Housing", "Services", "Commercial", "Agriculture", "Resources", "Industrial", "Other"],
        )

    def test_technology_branches(self):
        branches = load_json("TechnologyConfig.json")["Branches"]
        self.assertEqual([b["DisplayName"] for b in branches], ["USSR / Russia", "USA", "Germany"])


if __name__ == "__main__":
    unittest.main()
'''

TEST_FILES["tests/test_no_doctrine.py"] = TEST_COMMON + r'''

WORD = "doc" + "trine"  # split so this test file does not match itself


def all_keys(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from all_keys(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_keys(v)


class NoDoctrineTests(unittest.TestCase):
    def test_no_doctrine_config_fields(self):
        for path in CONFIG.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            bad = [k for k in all_keys(data) if WORD in str(k).lower()]
            self.assertEqual(bad, [], path.name)

    def test_no_doctrine_in_game_code(self):
        offenders = []
        for path in SRC.rglob("*"):
            if path.is_file() and path.suffix in (".luau", ".lua", ".json"):
                if "Tests" in path.parts:
                    continue  # the runtime self-test checks for the word on purpose
                if WORD in path.read_text(encoding="utf-8").lower():
                    offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
'''

TEST_FILES["tests/test_luau_static.py"] = TEST_COMMON + r'''
import importlib.util
import sys

_spec = importlib.util.spec_from_file_location("luau_static", Path(__file__).with_name("luau_static.py"))
luau_static = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(luau_static)


class LuauStaticTests(unittest.TestCase):
    def test_all_luau_files(self):
        failures = {}
        files = list(SRC.rglob("*.luau")) + list((ROOT / "plugin").rglob("*.luau"))
        self.assertGreater(len(files), 20)
        for path in files:
            is_module = not (path.name.endswith(".server.luau") or path.name.endswith(".client.luau"))
            errors = luau_static.check_luau(path.read_text(encoding="utf-8"), is_module)
            if errors:
                failures[str(path.relative_to(ROOT))] = errors
        self.assertEqual(failures, {})

    def test_no_todo_placeholders_in_required_code(self):
        offenders = [
            str(p.relative_to(ROOT)) for p in SRC.rglob("*.luau") if "TODO" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_json_configs_parse(self):
        for path in CONFIG.glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
'''

# ---------------------------------------------------------------------------
# DOCUMENTATION: PROJECT.md (current reality), DEVELOPMENT_ROADMAP.md (future), AGENTS.md (roles)
# ---------------------------------------------------------------------------
FEATURES = [
    # (feature, code status, notes)
    ("Save slots (3: Slot 1 FREE, Slots 2-3 LOCKED)", "IMPLEMENTED", "Server-validated; no monetization"),
    ("DataStore save/load (per-slot keys)", "PARTIAL", "Works; no session locking yet (last write wins)"),
    ("Country creation (name / flag / technology independent)", "IMPLEMENTED", "Server validates + filters name"),
    ("Flag selection (Continent -> Country, 195 states, search secondary)", "IMPLEMENTED", "UI + registry"),
    ("Flag images", "PLACEHOLDER", "No verified asset ids; emoji fallback used for all 195"),
    ("Technology branch selection (USSR / Russia, USA, Germany)", "IMPLEMENTED", "Selection + save only"),
    ("Technology / research tree", "PLANNED", "ResearchService is a placeholder"),
    ("Empty world (flat green territory, no pre-built city)", "IMPLEMENTED", "One plot per active country"),
    ("Residential buildings (Small / Medium / Large, 4 variants each)", "IMPLEMENTED", "Procedural low-poly"),
    ("Construction (PLANNED -> UNDER_CONSTRUCTION -> COMPLETED)", "IMPLEMENTED", "Progress bar removed on completion"),
    ("Population (logical, capped by HousingCapacity)", "IMPLEMENTED", "No physical NPCs"),
    ("Roads (Straight, Corner, T-Junction, Crossroad; grid snap)", "IMPLEMENTED", ""),
    ("Road graph (RoadId, Position, Rotation, Type, Neighbours, Connected)", "IMPLEMENTED", "Ready for pathfinding"),
    ("Road access check (MaxRoadDistance from config)", "IMPLEMENTED", "Shared client/server rules"),
    ("Build menu (8 scrollable categories, Roads first)", "IMPLEMENTED", "6 categories show 'Planned'"),
    ("Build preview (valid / subtle red invalid + reason)", "IMPLEMENTED", ""),
    ("Demolish / undo", "PLANNED", "Hammer shows disabled 'Demolish - soon'"),
    ("Resources (Money, Oil, Fuel, Steel, Supplies)", "PARTIAL", "Stored + replicated, always 0, inactive"),
    ("Production / industry chains", "PLANNED", "ProductionService placeholder"),
    ("Economy / civilian traffic", "PLANNED", "EconomyService placeholder"),
    ("Logistics (Truck, Freight Truck, Fuel Truck)", "PLANNED", "Needs stable road graph first"),
    ("Military layer", "PLANNED", "MilitaryService placeholder, no combat"),
    ("Reconnaissance / Satellites / UAV / Aircraft / Helicopters / Electronic Warfare", "PLANNED", "Interface stubs"),
    ("Studio bridge plugin (read-only verification)", "IMPLEMENTED", "Optional"),
]

KNOWN_ISSUES = [
    "No DataStore session locking: two servers writing the same slot = last write wins.",
    "Construction and population only advance while the owner is in the server (progress is saved).",
    "No demolish/undo yet: misplaced roads and buildings are permanent until Demolish ships.",
    "Flags are emoji fallbacks; emoji rendering depends on the device font.",
    "Mobile aiming assumes TouchTapInWorld positions are viewport-space (verify on a phone).",
    "The Luau static check is heuristic (blocks/brackets), not a full parser. Studio is the real compiler.",
    "Characters can walk off the territory edge (no walls by design).",
]

RUNTIME_CHECKLIST = [
    "Press Play in Studio",
    "Output shows '[WarState] Server ready' and '[WarState SelfTest] PASS'",
    "Slot Selection appears (Slot 1 Create, Slots 2-3 Locked)",
    "Create State on Slot 1",
    "Enter a country name (e.g. Novaria)",
    "Flag step: Select Continent (e.g. Europe)",
    "Select Country (e.g. Germany) from the scrollable list",
    "Select Technology (e.g. USSR / Russia)",
    "Review -> Create State",
    "You are teleported to an EMPTY green territory; HUD shows Population 0 / 0",
    "Tap the Hammer (bottom center) -> Build",
    "Roads category is first -> pick Straight",
    "Place a road (click / tap ground then Place)",
    "Open Housing -> Small House",
    "Preview far from road shows red 'Too far from road'",
    "Place the house next to the road",
    "House appears as a ghost (PLANNED) then fills in with a progress bar (UNDER_CONSTRUCTION)",
    "Progress bar disappears (COMPLETED); toast 'Small House completed'",
    "HUD: Population 0 / 4 then grows gradually to 4 / 4 and never above",
    "Menu -> Change slot, then Play Slot 1 again: road + house are restored",
]

AGENT_ROLES = [
    ("LEAD", "Owns the plan, assigns files, merges work, updates PROJECT.md status/changelog. Only role that edits PROJECT.md status tables."),
    ("ARCHITECT", "Owns module boundaries, data schemas (Types.luau, GameConfig.EmptyCountry) and remote contracts."),
    ("IMPLEMENTATION", "Writes Luau/Python for an assigned file set. Edits only files the Lead assigned."),
    ("CODE REVIEW", "Reviews diffs for correctness, server authority and idempotency. Read-only."),
    ("UI/UX REVIEW", "Checks white + light-blue style, compactness, safe insets, mobile scaling, English-only text."),
    ("GAMEPLAY TESTER", "Runs the Studio runtime checklist and records PASS/FAIL per step."),
    ("BUG HUNTER", "Tries to break placement, saves, remotes (spam, invalid payloads, rejoin)."),
    ("DATA AUDITOR", "Verifies registry (195), save schema, migrations, no doctrine fields, no granted resources."),
    ("PERFORMANCE REVIEW", "Part counts, per-frame work in PlacementController, server tick costs."),
    ("ASSET/VISUAL REVIEW", "Building variant readability/size, flag assets (only verified ids), no permanent labels."),
]

MANUAL_BLOCKS = ["known-bugs", "runtime-results", "review-log"]
MANUAL_DEFAULTS = {
    "known-bugs": "- (none recorded yet)",
    "runtime-results": "- Not run yet. Record: date, tester, step, PASS/FAIL, notes.",
    "review-log": "- (no reviews recorded yet)",
}


def extract_manual_blocks(text: str) -> dict:
    blocks = {}
    for name in MANUAL_BLOCKS:
        m = re.search(
            r"<!-- MANUAL:BEGIN %s -->\n(.*?)\n<!-- MANUAL:END %s -->" % (re.escape(name), re.escape(name)),
            text,
            re.S,
        )
        if m:
            blocks[name] = m.group(1)
    return blocks


def manual(name: str, blocks: dict) -> str:
    body = blocks.get(name, MANUAL_DEFAULTS[name])
    return f"<!-- MANUAL:BEGIN {name} -->\n{body}\n<!-- MANUAL:END {name} -->"


def classify_script(path: Path) -> str:
    n = path.name
    if n.endswith(".server.luau"):
        return "Script"
    if n.endswith(".client.luau"):
        return "LocalScript"
    return "ModuleScript"


def module_status(text: str) -> str:
    if 'Status = "PLANNED"' in text:
        return "PLANNED"
    if 'Status = "PARTIAL"' in text:
        return "PARTIAL"
    return "IMPLEMENTED"


def instance_path(rel: str) -> str:
    p = rel
    for prefix, repl in (
        ("src/StarterPlayer/", "StarterPlayer/"),
        ("src/", ""),
    ):
        if p.startswith(prefix):
            p = repl + p[len(prefix):]
            break
    for suffix in (".server.luau", ".client.luau", ".luau", ".json"):
        if p.endswith(suffix):
            return p[: -len(suffix)]
    return p


def gen_project_md(root: Path, results: dict, changelog: list, existing: str, file_list) -> str:
    blocks = extract_manual_blocks(existing or "")
    registry = country_registry()
    real = sum(1 for c in registry["Countries"] if c["FlagAsset"])
    total = len(registry["Countries"])

    scripts, locals_, modules = [], [], []
    functions = []
    for path in sorted((root / "src").rglob("*")):
        if not path.is_file() or path.suffix not in (".luau", ".json"):
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        kind = "ModuleScript" if path.suffix == ".json" else classify_script(path)
        status = "IMPLEMENTED" if path.suffix == ".json" else module_status(text)
        row = f"| `{instance_path(rel)}` | `{rel}` | {status} |"
        {"Script": scripts, "LocalScript": locals_, "ModuleScript": modules}[kind].append(row)
        if path.suffix == ".luau":
            names = re.findall(r"^function ([\w\.:]+)\(", text, re.M)
            if names:
                functions.append(f"- `{instance_path(rel)}`: " + ", ".join(f"`{n}`" for n in names))

    def table(rows):
        head = "| Instance | File | Status |\n|---|---|---|"
        return head + "\n" + "\n".join(rows) if rows else "_none_"

    feature_rows = "\n".join(
        f"| {f} | {s} | {'n/a' if s == 'PLANNED' else 'NOT VERIFIED'} | {n} |" for f, s, n in FEATURES
    )
    remote_rows = "\n".join(f"| `{n}` | RemoteFunction | {d} |" for n, d in REMOTE_FUNCTIONS)
    remote_rows += "\n" + "\n".join(f"| `{n}` | RemoteEvent | {d} |" for n, d in REMOTE_EVENTS)
    configs = "\n".join(
        f"- `src/ReplicatedStorage/Shared/Config/{n}`"
        for n in (
            "GameConfig.json",
            "PlacementConfig.json",
            "BuildingConfig.json",
            "RoadConfig.json",
            "BuildMenuConfig.json",
            "TechnologyConfig.json",
            "CountryRegistry.json",
            "ThemeConfig.luau",
        )
    )
    empty = json.dumps(GAME_CONFIG["EmptyCountry"], indent=2)
    build_rows = "\n".join(f"| {k} | {v} |" for k, v in results.items())
    changes = []
    for entry in reversed(changelog[-30:]):
        changes.append(
            f"- {entry['date']} (generator {entry['version']}): "
            f"{len(entry.get('created', []))} created, {len(entry.get('updated', []))} updated"
            + (": " + ", ".join(f"`{p}`" for p in (entry.get("created", []) + entry.get("updated", []))[:12]) if entry.get("created") or entry.get("updated") else "")
            + (" ..." if len(entry.get("created", []) + entry.get("updated", [])) > 12 else "")
        )
    files_list = "\n".join(f"- `{p}`" for p in sorted(set(file_list) | {"PROJECT.md"}))
    checklist = "\n".join(f"{i}. {s}" for i, s in enumerate(RUNTIME_CHECKLIST, 1))
    issues = "\n".join(f"- {s}" for s in KNOWN_ISSUES)
    roles = "\n".join(f"- **{r}**: {d}" for r, d in AGENT_ROLES)

    return f"""# WAR STATE - PROJECT.md (LIVE)

> Current reality of the generated project. Regenerated by `build_war_state.py` on every run.
> Future plans live in `DEVELOPMENT_ROADMAP.md`. Sections between `MANUAL:BEGIN/END` markers are preserved.

**Status legend:** IMPLEMENTED = code for the feature's current scope exists (does NOT mean runtime-verified) ·
PARTIAL · BROKEN · PLACEHOLDER · PLANNED. The *Runtime* column only changes after a human/agent runs the Studio checklist.

## Game concept
The player creates a country from zero: Join -> Save Slot -> Create State (Country Name, Flag via Continent -> Country,
Technology Branch) -> an empty flat green territory. The player builds roads and housing; construction takes time;
citizens appear only after housing exists and population grows gradually up to HousingCapacity.

## Current phase
**{CURRENT_PHASE}** · generator {GENERATOR_VERSION}

## Feature status
| Feature | Code | Runtime | Notes |
|---|---|---|---|
{feature_rows}

## Architecture
```
Python (build_war_state.py) -> files in src/ -> Rojo (default.project.json) -> Roblox Studio
Client: input, UI, preview          Server: validation, placement, construction, population, saves
ReplicatedStorage
  Shared/Config     JSON + Theme (Rojo turns *.json into ModuleScripts)
  Shared/Constants  Remote names, build states, attribute names (generated)
  Shared/Types      Luau types
  Shared/Modules    GridMath, PlacementRules, RoadGraph, BuildingModels, RoadModels, Countries, DefaultCountry, Plots
  Remotes           defined in default.project.json (server creates any missing ones once)
  Assets            (empty; no external assets)
ServerScriptService
  ServerMain        requires all Systems, init() then start()
  Systems/Data Country World Buildings Construction Population Roads Resources Research Production Economy Military
  Tests/RuntimeSelfTest (Studio only)
StarterPlayer/StarterPlayerScripts   ClientMain + Controllers (ClientState, PlacementController)
StarterGui/MainUI                     ScreenGui + Components (UIKit) + Screens
Workspace  Map Buildings Roads Vehicles NPCs  (territory/plots generated at runtime, never a pre-built city)
```
Rojo safety: services use `$ignoreUnknownInstances: true` and only our sub-folders are mapped, so existing
content in your "War State" place is not deleted by live sync.

## Scripts (server)
{table(scripts)}

## LocalScripts (client)
{table(locals_)}

## ModuleScripts
{table(modules)}

## RemoteEvents / RemoteFunctions
| Name | Type | Purpose |
|---|---|---|
{remote_rows}

## GUI hierarchy (built at runtime by ClientMain inside PlayerGui.MainUI)
```
MainUI (ScreenGui, ResetOnSpawn=false, ScreenInsets=CoreUISafeInsets)
  SlotScreen            centered compact panel, 3 slot rows
  CreateStateScreen     4-step wizard: Name -> Flag (Continent grid -> scrollable Country grid + optional search) -> Technology -> Review
  TopCenter             pill: Menu | flag + country name | Population X / Y | "Saving off" chip
  MenuPopover           Save now, Change slot, stats
  Hammer                BOTTOM CENTER round button
  HammerTools           popover: Build | Demolish (disabled, planned)
  BuildMenu             bottom-center panel: horizontal category tabs (Roads first) + horizontal item cards (3D previews)
  PlacementBar          Style / Rotate / Place / Done + validity reason
  Toasts                short notifications under the top bar
```

## Important functions
{chr(10).join(functions)}

## Configuration files
{configs}

Key values: MaxRoadDistance = {PLACEMENT_CONFIG['MaxRoadDistance']} studs, GridSize = {PLACEMENT_CONFIG['GridSize']},
RoadTileSize = {PLACEMENT_CONFIG['RoadTileSize']}, Territory = {GAME_CONFIG['Territory']['Size']}x{GAME_CONFIG['Territory']['Size']} studs.

## Data structure
DataStore `{GAME_CONFIG['DataStoreName']}`: `profile_<userId>` (slot summaries) and `slot_<userId>_<n>` (one country per slot).
New country (from `GameConfig.EmptyCountry`, nothing granted):
```json
{empty}
```
Building record: `Id, Type, Variant, X, Z (plot-local), Rotation, State, PlannedElapsed, Progress, CreatedAt`.
Road segment: `RoadId, Type, Rotation, Ix, Iz, Position {{X, Z}}, Neighbours, Adjacent, Connected`.

## Flags
- RegistryCount: **{total}**
- RealAssetCount: **{real}**
- FallbackCount: **{total - real}**

## Known bugs / limitations
{issues}

Manually recorded bugs:
{manual("known-bugs", blocks)}

## Build tests (last generator run)
| Check | Result |
|---|---|
{build_rows}

## Runtime tests (Studio) - checklist
Static tests are not sufficient. Run this in Studio and record the results below.
{checklist}

Runtime results:
{manual("runtime-results", blocks)}

## Agent roles
See `AGENTS.md`. Summary:
{roles}

Review log (major review results):
{manual("review-log", blocks)}

## Changelog
{chr(10).join(changes) if changes else "- (no changes recorded)"}

## Generated files
{files_list}

## Current status
Code exists and static checks/tests run from Python. **Rojo build: {results.get('Rojo build', 'NOT RUN')}.**
Studio sync and gameplay are **NOT VERIFIED** until the runtime checklist above is recorded.
"""


def gen_roadmap_md() -> str:
    return """# WAR STATE - DEVELOPMENT_ROADMAP.md

> Future plan only. What exists today is in PROJECT.md. Do not mark anything here as done; move it to PROJECT.md when it ships.

## Phase 1 - First playable foundation (current)
Save slots, country creation, flag selection (195), technology selection, empty world, residential buildings,
construction, logical population, roads, road access, build menu.

## Phase 2 - Stabilize the city builder
- Demolish / undo for roads and buildings (with refunds once economy exists)
- Road auto-tiling (choose Straight/Corner/T/Cross automatically from neighbours)
- Drag-to-place road lines
- DataStore session locking + save versioning/migrations
- Offline construction progress (timestamp based)
- Verified flag image assets (only real, checked Roblox asset ids)

## Phase 3 - Services and commerce
- Services (clinic, school, police) and Commercial (shops)
- Civilian trips on the road graph: House -> Road -> Shop -> Road -> House, House -> Road -> Service -> House
- A small number of visual cars/NPCs driven by logical demand (no mass NPC simulation)

## Phase 4 - Resources and industry
- Oil Well -> Crude Oil -> Refinery -> Fuel
- Steel, Supplies production
- Factory -> Road -> Truck -> Warehouse
- Logistics vehicles: Truck, Freight Truck, Fuel Truck (after road graph pathfinding is stable)

## Phase 5 - Research
- Time-based research: ResearchTime, Requirements, Unlocks
- Branch-specific equipment lines for USSR / Russia, USA, Germany (no doctrine system)

## Phase 6 - Military layer
- Military data + UI (units, production queues) built on top of industry and logistics
- Reserved modules: Reconnaissance, Satellites, UAV, Aircraft, Helicopters, Electronic Warfare

## Phase 7 - Slots 2 and 3
- Unlock mechanism (monetization design decided later)

## Engineering rules for every phase
- Server authority for all permanent state; client = input, UI, preview
- Config in JSON under Shared/Config; no magic numbers in systems
- Keep build_war_state.py idempotent; update PROJECT.md on every major change
"""


def gen_agents_md() -> str:
    roles = "\n".join(f"### {r}\n{d}\n" for r, d in AGENT_ROLES)
    return f"""# WAR STATE - AGENTS.md

Recommended specialised agents for an external AI coding environment.

{roles}
## Coordination rules
1. The **LEAD** coordinates all changes and assigns file ownership before work starts.
2. **No two agents edit the same file concurrently.** Claim files in `.warstate/agent_locks.json`
   (`{{"path": "agent-role"}}`) before editing and release them afterwards. The Lead resolves conflicts.
3. Generated files are owned by `build_war_state.py`. To change them, change the generator, then rerun it.
   Hand edits to generated files are detected and never silently overwritten (use `--force` to replace; a backup is kept).
4. Review roles are read-only. They record major results in PROJECT.md under **Review log** (MANUAL block).
5. Nobody marks a feature IMPLEMENTED unless the code exists; runtime status changes only after the Studio checklist.
6. Distinguish: code exists / code compiles / Rojo builds / Studio received files / game runs / feature works.
"""

# ---------------------------------------------------------------------------
# ENGINE: safe writes, manifest, validation, tests, Rojo, bridge
# ---------------------------------------------------------------------------
STATE_DIR = ".warstate"


class BuildError(Exception):
    """Readable, fatal error. Stops the build."""


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(root: Path) -> dict:
    path = root / STATE_DIR / "manifest.json"
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"files": {}}
    return {"files": {}}


class SafeWriter:
    """Idempotent, non-destructive writer.

    - new file                       -> CREATED
    - identical content              -> SKIPPED (unchanged)
    - changed, last written by us    -> backup + UPDATED
    - changed by a human (hash drift)-> SKIPPED + WARNING (proposal saved to .warstate/pending) unless --force
    Never deletes anything.
    """

    def __init__(self, root: Path, force: bool, dry_run: bool):
        self.root = root
        self.force = force
        self.dry_run = dry_run
        self.manifest = load_manifest(root)
        self.stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.created, self.updated, self.skipped, self.backed_up, self.warnings = [], [], [], [], []

    def _backup(self, rel: str, current: str):
        dest = self.root / STATE_DIR / "backups" / self.stamp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(current, encoding="utf-8")
        self.backed_up.append(f"{rel} -> {dest.relative_to(self.root).as_posix()}")

    def _pending(self, rel: str, content: str):
        dest = self.root / STATE_DIR / "pending" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return dest.relative_to(self.root).as_posix()

    def write(self, rel: str, content: str, always_regenerate: bool = False):
        path = self.root / rel
        new_hash = sha(content)
        record = self.manifest["files"].get(rel)
        if self.dry_run:
            if not path.is_file():
                self.warnings.append(f"{rel}: missing (check-only mode, not written)")
            elif sha(path.read_text(encoding="utf-8")) != new_hash:
                self.skipped.append(f"{rel} (differs from generator; check-only mode)")
            else:
                self.skipped.append(f"{rel} (unchanged)")
            return
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
                self.created.append(rel)
            else:
                current = path.read_text(encoding="utf-8")
                current_hash = sha(current)
                if current_hash == new_hash:
                    self.skipped.append(f"{rel} (unchanged)")
                else:
                    ours = record is not None and record.get("sha256") == current_hash
                    if ours or self.force or always_regenerate:
                        if not ours and not always_regenerate:
                            self.warnings.append(f"{rel}: hand edits replaced because of --force (backup kept)")
                        elif always_regenerate and not ours:
                            self.warnings.append(f"{rel}: regenerated live document (backup kept)")
                        self._backup(rel, current)
                        path.write_text(content, encoding="utf-8", newline="\n")
                        self.updated.append(rel)
                    else:
                        pending = self._pending(rel, content)
                        self.skipped.append(f"{rel} (edited by hand, kept yours)")
                        self.warnings.append(
                            f"{rel}: you edited this generated file; not overwritten. "
                            f"New version saved to {pending}. Use --force to replace."
                        )
                        return
        except PermissionError as exc:
            raise BuildError(f"Write permission denied: {path} ({exc})")
        except OSError as exc:
            raise BuildError(f"Could not write {path}: {exc}")
        self.manifest["files"][rel] = {"sha256": new_hash, "generator": GENERATOR_VERSION}

    def save_manifest(self):
        if self.dry_run:
            return
        path = self.root / STATE_DIR / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_environment(root: Path, dry_run: bool):
    if sys.version_info < MIN_PYTHON:
        raise BuildError(
            "Python %d.%d+ is required (found %s)." % (MIN_PYTHON[0], MIN_PYTHON[1], platform.python_version())
        )
    if dry_run:
        return
    try:
        (root / STATE_DIR).mkdir(parents=True, exist_ok=True)
        probe = root / STATE_DIR / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise BuildError(f"Write permission denied in project folder {root}: {exc}")


def detect_rojo():
    exe = shutil.which("rojo")
    if not exe:
        return None, None
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
        version = (out.stdout or out.stderr).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise BuildError(f"Rojo was found at {exe} but could not run: {exc}")
    return exe, version


def ensure_dirs(root: Path, dry_run: bool):
    created = []
    for rel in REQUIRED_DIRS:
        path = root / rel
        if not path.is_dir():
            if dry_run:
                continue
            try:
                path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise BuildError(f"Could not create folder {rel}: {exc}")
            created.append(rel + "/")
    return created


def generated_files(root: Path) -> dict:
    """Every generated file except PROJECT.md (which needs build results)."""
    files = dict(EMBEDDED_FILES)
    files["src/ReplicatedStorage/Shared/Constants/Constants.luau"] = gen_constants_luau()
    cfg = "src/ReplicatedStorage/Shared/Config/"
    files[cfg + "GameConfig.json"] = to_json(GAME_CONFIG)
    files[cfg + "PlacementConfig.json"] = to_json(PLACEMENT_CONFIG)
    files[cfg + "BuildingConfig.json"] = to_json(BUILDING_CONFIG)
    files[cfg + "RoadConfig.json"] = to_json(ROAD_CONFIG)
    files[cfg + "BuildMenuConfig.json"] = to_json(BUILD_MENU_CONFIG)
    files[cfg + "TechnologyConfig.json"] = to_json(TECHNOLOGY_CONFIG)
    files[cfg + "CountryRegistry.json"] = to_json(country_registry())
    files["plugin.project.json"] = to_json(PLUGIN_PROJECT)
    files["tests/luau_static.py"] = "# Generated by build_war_state.py - Luau heuristic checker\n" + LUAU_CHECKER_SOURCE
    files["tests/__init__.py"] = ""
    files.update(TEST_FILES)
    files["DEVELOPMENT_ROADMAP.md"] = gen_roadmap_md()
    files["AGENTS.md"] = gen_agents_md()
    return files


def static_validate(root: Path) -> list:
    errors = []
    for path in sorted((root / "src").rglob("*.luau")) + sorted((root / "plugin").rglob("*.luau")):
        is_module = not (path.name.endswith(".server.luau") or path.name.endswith(".client.luau"))
        for err in check_luau(path.read_text(encoding="utf-8"), is_module):
            errors.append(f"{path.relative_to(root).as_posix()}: {err}")
    for path in sorted((root / "src").rglob("*.json")) + [root / "default.project.json"]:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root).as_posix()}: invalid JSON ({exc})")
    return errors


def run_tests(root: Path):
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-p", "test_*.py"]
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (proc.stdout + proc.stderr).strip()
    m = re.search(r"Ran (\d+) tests?", output)
    count = int(m.group(1)) if m else 0
    return proc.returncode == 0 and count > 0, count, output


def rojo_build(exe: str, root: Path):
    out_dir = root / "build"
    out_dir.mkdir(exist_ok=True)
    output = out_dir / "WarState.validation.rbxlx"
    cmd = [exe, "build", "default.project.json", "--output", str(output)]
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = proc.returncode == 0 and output.is_file()
    return ok, (proc.stdout + proc.stderr).strip(), output


def http_json(url: str, timeout: float = 1.5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def rojo_serve(exe: str, root: Path, port: int):
    existing = http_json(f"http://127.0.0.1:{port}/api/rojo")
    if existing:
        return None, f"A Rojo server is already running on 127.0.0.1:{port} ({existing.get('projectName', '?')}); reusing it."
    if not port_free(port):
        return None, f"Port {port} is busy (not Rojo). Use --port."
    proc = subprocess.Popen(
        [exe, "serve", "default.project.json", "--address", "127.0.0.1", "--port", str(port)],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    deadline = time.time() + 15
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            return None, f"rojo serve exited with code {proc.returncode}: {out.strip()}"
        info = http_json(f"http://127.0.0.1:{port}/api/rojo")
        if info:
            threading.Thread(target=_drain, args=(proc,), daemon=True).start()
            return proc, f"Rojo {info.get('serverVersion', '')} serving '{info.get('projectName', '')}' on 127.0.0.1:{port}"
        time.sleep(0.4)
    proc.terminate()
    return None, "rojo serve did not answer on /api/rojo within 15 s"


def _drain(proc):
    try:
        for _line in proc.stdout:
            pass
    except (OSError, ValueError):
        pass


# --- Studio bridge (localhost only, read-only structured commands) ---------
class BridgeState:
    def __init__(self, expected_paths):
        self.lock = threading.Lock()
        self.commands = queue.Queue()
        self.last_hello = None
        self.place_name = None
        self.verify_result = None
        self.expected_paths = expected_paths
        self.next_id = 1
        self.enqueue_verify()

    def enqueue_verify(self):
        with self.lock:
            cid = self.next_id
            self.next_id += 1
        self.commands.put({"id": cid, "type": "verify_structure", "paths": self.expected_paths})


def make_bridge_handler(state: BridgeState, port: int):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}", "127.0.0.1", "localhost"}

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "WarStateBridge/1"

        def log_message(self, *_args):
            pass

        def _reject(self, code, msg):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": msg}).encode())

        def _guard(self):
            if self.client_address[0] != "127.0.0.1":
                self._reject(403, "localhost only")
                return False
            if self.headers.get("Host") not in allowed_hosts:
                self._reject(403, "bad host")
                return False
            if self.headers.get("Origin"):
                self._reject(403, "browser requests are not allowed")
                return False
            return True

        def _send(self, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length > 1_000_000:
                return None
            try:
                return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except ValueError:
                return None

        def do_GET(self):
            if not self._guard():
                return
            if self.path == "/v1/command":
                try:
                    self._send(state.commands.get_nowait())
                except queue.Empty:
                    self._send({"type": "none"})
            else:
                self._reject(404, "unknown endpoint")

        def do_POST(self):
            if not self._guard():
                return
            data = self._read_json()
            if not isinstance(data, dict):
                self._reject(400, "invalid json")
                return
            if self.path == "/v1/hello":
                with state.lock:
                    state.last_hello = time.time()
                    state.place_name = str(data.get("placeName", ""))[:100]
                self._send({"ok": True})
            elif self.path == "/v1/result":
                if data.get("type") == "verify_structure":
                    with state.lock:
                        state.verify_result = {
                            "ok": bool(data.get("ok")),
                            "found": int(data.get("found") or 0),
                            "missing": [str(m) for m in (data.get("missing") or [])][:50],
                        }
                self._send({"ok": True})
            else:
                self._reject(404, "unknown endpoint")

    return Handler


def start_bridge(port: int, expected_paths):
    state = BridgeState(expected_paths)
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), make_bridge_handler(state, port))
    except OSError as exc:
        return None, None, f"Bridge could not bind 127.0.0.1:{port}: {exc}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, state, f"Bridge listening on 127.0.0.1:{port} (localhost only)"


def studio_status(state) -> str:
    if state is None:
        return "NOT VERIFIED (bridge not running)"
    with state.lock:
        hello = state.last_hello
        result = state.verify_result
        place = state.place_name
    if not hello or time.time() - hello > 10:
        return "NOT VERIFIED (no Studio bridge heartbeat)"
    if result is None:
        return f"CONNECTED (bridge, place '{place}'), files not verified yet"
    if result["ok"]:
        return f"CONNECTED (place '{place}'), synced files VERIFIED ({result['found']} instances found)"
    return (
        f"CONNECTED (place '{place}'), but {len(result['missing'])} expected instances are MISSING "
        f"(is the Rojo plugin connected?) e.g. {result['missing'][:3]}"
    )


def plugins_dir():
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / "Roblox" / "Plugins" if base else None
    if system == "Darwin":
        return Path.home() / "Documents" / "Roblox" / "Plugins"
    return None

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def banner(title: str):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_list(title, items):
    print(f"{title}:")
    if not items:
        print("  - (none)")
    for item in items:
        print(f"  - {item}")


def parse_args(argv):
    p = argparse.ArgumentParser(description="Generate, validate and live-sync the War State Roblox project.")
    p.add_argument("--project-dir", default=None, help="Project folder (default: folder of this script)")
    p.add_argument("--no-rojo", action="store_true", help="Skip rojo build/serve (reported as SKIPPED)")
    p.add_argument("--no-serve", action="store_true", help="Do not start rojo serve")
    p.add_argument("--port", type=int, default=ROJO_PORT, help="rojo serve port (default %d)" % ROJO_PORT)
    p.add_argument("--no-bridge", action="store_true", help="Do not start the localhost Studio verification bridge")
    p.add_argument("--bridge-port", type=int, default=BRIDGE_PORT)
    p.add_argument("--studio-wait", type=int, default=20, help="Seconds to wait for the Studio bridge before the summary")
    p.add_argument("--install-plugin", action="store_true", help="Build the Studio bridge plugin into your Plugins folder")
    p.add_argument("--force", action="store_true", help="Replace hand-edited generated files (backups kept)")
    p.add_argument("--check-only", action="store_true", help="Write nothing; validate, test and rojo build")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    root = Path(args.project_dir).resolve() if args.project_dir else Path(__file__).resolve().parent
    results = {}
    warnings = []
    rojo_status, tests_status, live_status, studio = "NOT RUN", "NOT RUN", "NOT STARTED", "NOT VERIFIED"
    serve_proc = None
    bridge_state = None
    exit_code = 0

    banner(f"WAR STATE BUILD  (generator {GENERATOR_VERSION})")
    print(f"Project: {root}")
    print(f"Python : {platform.python_version()} ({sys.executable})")

    try:
        check_environment(root, args.check_only)

        rojo_exe, rojo_version = (None, None)
        if not args.no_rojo:
            rojo_exe, rojo_version = detect_rojo()
            if not rojo_exe:
                raise BuildError(
                    "Rojo was not found on PATH.\n"
                    "  Install Rojo 7.x: https://rojo.space/docs/v7/getting-started/installation/\n"
                    "  (e.g. `aftman add rojo-rbx/rojo` / `rokit add rojo-rbx/rojo`, or download rojo.exe and add it to PATH)\n"
                    "  Or run with --no-rojo to only generate files and run tests."
                )
            print(f"Rojo   : {rojo_version} ({rojo_exe})")
            m = re.search(r"(\d+)\.(\d+)", rojo_version or "")
            if m and (int(m.group(1)), int(m.group(2))) < (7, 3):
                raise BuildError(f"Rojo 7.3+ is required for .luau files (found '{rojo_version}'). Please update Rojo.")
        else:
            print("Rojo   : SKIPPED (--no-rojo)")

        # 1-2. folders
        created_dirs = ensure_dirs(root, args.check_only)

        # 3-7. files
        writer = SafeWriter(root, force=args.force, dry_run=args.check_only)
        for rel, content in generated_files(root).items():
            writer.write(rel, content)
        writer.write("default.project.json", gen_project_json(root))
        gitignore = root / ".gitignore"
        if not gitignore.exists() and not args.check_only:
            writer.write(".gitignore", "build/\n.warstate/backups/\n.warstate/pending/\n__pycache__/\n")

        # 10. verify required files
        missing = [rel for rel in list(generated_files(root)) + ["default.project.json"] if not (root / rel).is_file()]
        if missing and not args.check_only:
            raise BuildError("Required files missing after generation: " + ", ".join(missing[:10]))

        # static validation (Luau generation check)
        errors = static_validate(root)
        results["Luau/JSON static check"] = "PASS" if not errors else f"FAIL ({len(errors)} errors)"
        if errors:
            for e in errors:
                print("  STATIC ERROR:", e)
            raise BuildError("Luau/JSON static validation failed. Fix the errors above.")

        # 7. tests
        ok, count, output = run_tests(root)
        tests_status = f"PASS ({count} tests)" if ok else "FAIL"
        results["Python tests"] = tests_status
        if not ok:
            print(output)
            exit_code = 1

        # 11. rojo build
        if rojo_exe:
            ok_build, build_out, build_file = rojo_build(rojo_exe, root)
            rojo_status = "PASS" if ok_build else "FAIL"
            results["Rojo build"] = rojo_status + (f" ({build_file.relative_to(root).as_posix()})" if ok_build else "")
            if not ok_build:
                print("ROJO BUILD OUTPUT:\n" + build_out)
                exit_code = 1
        else:
            rojo_status = "SKIPPED"
            results["Rojo build"] = "SKIPPED"

        # optional plugin install
        if args.install_plugin:
            if not rojo_exe:
                warnings.append("--install-plugin needs Rojo; skipped")
            else:
                target_dir = plugins_dir()
                if not target_dir:
                    warnings.append("Unknown Roblox Plugins folder on this OS; build plugin manually with plugin.project.json")
                else:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / "WarStateBridge.rbxm"
                    proc = subprocess.run(
                        [rojo_exe, "build", "plugin.project.json", "--output", str(target)],
                        cwd=str(root), capture_output=True, text=True,
                    )
                    if proc.returncode == 0:
                        print(f"Plugin installed: {target} (restart Studio or reload plugins)")
                    else:
                        warnings.append("Plugin build failed: " + (proc.stdout + proc.stderr).strip())

        # 8. PROJECT.md (live doc, manual blocks preserved)
        project_md_path = root / "PROJECT.md"
        existing = project_md_path.read_text(encoding="utf-8") if project_md_path.is_file() else ""
        changelog_path = root / STATE_DIR / "changelog.json"
        changelog = []
        if changelog_path.is_file():
            try:
                changelog = json.loads(changelog_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                changelog = []
        changed = [p for p in writer.created + writer.updated if p != "PROJECT.md"]
        if changed and not args.check_only:
            changelog.append(
                {
                    "date": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "version": GENERATOR_VERSION,
                    "created": [p for p in writer.created if p != "PROJECT.md"],
                    "updated": [p for p in writer.updated if p != "PROJECT.md"],
                }
            )
            changelog_path.write_text(json.dumps(changelog, indent=2) + "\n", encoding="utf-8")
        if not args.check_only:
            doc_results = {k: v for k, v in results.items()}
            writer.write("PROJECT.md", gen_project_md(root, doc_results, changelog, existing, writer.manifest["files"].keys()), always_regenerate=True)
            writer.save_manifest()

        if not args.check_only:
            if not (root / "PROJECT.md").is_file():
                raise BuildError("PROJECT.md could not be written")
            (root / STATE_DIR / "last_run.json").write_text(
                json.dumps({"results": results, "created": writer.created, "updated": writer.updated}, indent=2) + "\n",
                encoding="utf-8",
            )

        # 12. live sync
        if rojo_exe and not args.no_serve and not args.check_only:
            if rojo_status != "PASS":
                live_status = "NOT STARTED (rojo build failed)"
            else:
                serve_proc, msg = rojo_serve(rojo_exe, root, args.port)
                if serve_proc is not None:
                    live_status = "RUNNING"
                elif "already running" in msg:
                    live_status = "RUNNING (existing server)"
                else:
                    live_status = "FAILED"
                    exit_code = 1
                print(msg)
                if not args.no_bridge and live_status.startswith("RUNNING"):
                    _server, bridge_state, bmsg = start_bridge(args.bridge_port, expected_instance_paths(root))
                    print(bmsg)
                    if bridge_state is not None and args.studio_wait > 0:
                        print(f"Waiting up to {args.studio_wait}s for the Studio bridge plugin (optional)...")
                        deadline = time.time() + args.studio_wait
                        while time.time() < deadline:
                            with bridge_state.lock:
                                done = bridge_state.verify_result is not None
                            if done:
                                break
                            time.sleep(0.5)
        elif args.no_serve:
            live_status = "NOT STARTED (--no-serve)"
        elif args.no_rojo:
            live_status = "NOT STARTED (--no-rojo)"
        elif args.check_only:
            live_status = "NOT STARTED (--check-only)"

        studio = studio_status(bridge_state)

        banner("MANIFEST")
        print_list("CREATED", created_dirs + writer.created)
        print_list("UPDATED", writer.updated)
        print_list("SKIPPED", writer.skipped if len(writer.skipped) <= 15 else writer.skipped[:15] + [f"... and {len(writer.skipped) - 15} more unchanged"])
        print_list("BACKED UP", writer.backed_up)
        print_list("WARNINGS", writer.warnings + warnings)

    except BuildError as exc:
        banner("WAR STATE BUILD FAILED")
        print(f"ERROR: {exc}")
        print(f"\nRojo: {rojo_status}\nTests: {tests_status}\nLive Sync: {live_status}\nStudio: NOT VERIFIED")
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130

    banner("WAR STATE BUILD COMPLETE" if exit_code == 0 else "WAR STATE BUILD FINISHED WITH FAILURES")
    print(f"Project:\n  {root}")
    print(f"Files created:\n  {len(writer.created)} created, {len(writer.updated)} updated, {len(writer.skipped)} unchanged/skipped")
    print(f"Rojo:\n  {rojo_status}")
    print(f"Tests:\n  {tests_status}")
    print(f"Live Sync:\n  {live_status}")
    print(f"Studio:\n  {studio}")
    if live_status.startswith("RUNNING"):
        print(
            "\nNext: in Roblox Studio open your 'War State' place -> Rojo plugin -> Connect "
            f"(127.0.0.1:{args.port}) -> press Play and follow the checklist in PROJECT.md."
        )
        if serve_proc is not None:
            print("Live sync keeps running. Press Ctrl+C to stop.")
            last = studio
            try:
                while serve_proc.poll() is None:
                    time.sleep(2)
                    now = studio_status(bridge_state)
                    if now != last:
                        print(f"Studio: {now}")
                        last = now
                print(f"rojo serve stopped (exit code {serve_proc.returncode}). Live Sync: STOPPED")
                return 1
            except KeyboardInterrupt:
                serve_proc.terminate()
                print("\nLive sync stopped.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
