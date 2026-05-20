HOUSE_CATALOG = [
    {
        "key": "wolf",
        "name": "Дом Волка",
        "motto": "Сила в стае",
        "color": "gray",
        "style": "давление, воля, прямое действие",
        "scores": {"power": 5, "diplomacy": 2, "wealth": 1, "knowledge": 1, "shadow": 2, "risk": 3},
    },
    {
        "key": "tower",
        "name": "Дом Башни",
        "motto": "Стоим выше смуты",
        "color": "stone",
        "style": "устойчивость, защита, выдержка",
        "scores": {"power": 4, "diplomacy": 1, "wealth": 2, "knowledge": 3, "shadow": 1, "risk": 1},
    },
    {
        "key": "sun",
        "name": "Дом Солнца",
        "motto": "Свет делает власть видимой",
        "color": "gold",
        "style": "харизма, открытое влияние, яркая игра",
        "scores": {"power": 2, "diplomacy": 4, "wealth": 3, "knowledge": 2, "shadow": 1, "risk": 3},
    },
    {
        "key": "sword",
        "name": "Дом Меча",
        "motto": "Решение должно быть острым",
        "color": "steel",
        "style": "силовой ход, напор, решительность",
        "scores": {"power": 5, "diplomacy": 1, "wealth": 1, "knowledge": 1, "shadow": 1, "risk": 4},
    },
    {
        "key": "scroll",
        "name": "Дом Свитка",
        "motto": "Кто знает больше — правит дольше",
        "color": "ivory",
        "style": "знание, анализ, дальний расчёт",
        "scores": {"power": 1, "diplomacy": 2, "wealth": 1, "knowledge": 5, "shadow": 2, "risk": 1},
    },
    {
        "key": "seal",
        "name": "Дом Печати",
        "motto": "Союз, признанный словом, сильнее стали",
        "color": "violet",
        "style": "договорённости, право, политический вес",
        "scores": {"power": 1, "diplomacy": 5, "wealth": 3, "knowledge": 2, "shadow": 2, "risk": 1},
    },
    {
        "key": "key",
        "name": "Дом Ключа",
        "motto": "Не каждый вход должен быть виден",
        "color": "bronze",
        "style": "доступ, скрытые решения, редкие возможности",
        "scores": {"power": 1, "diplomacy": 2, "wealth": 2, "knowledge": 4, "shadow": 4, "risk": 2},
    },
    {
        "key": "fire",
        "name": "Дом Огня",
        "motto": "Кто боится пламени — не кует судьбу",
        "color": "red",
        "style": "риск, дерзость, резкий поворот",
        "scores": {"power": 3, "diplomacy": 2, "wealth": 1, "knowledge": 1, "shadow": 2, "risk": 5},
    },
    {
        "key": "raven",
        "name": "Дом Ворона",
        "motto": "Тот, кто знает первым, действует первым",
        "color": "black",
        "style": "сведения, тайна, скрытое влияние",
        "scores": {"power": 1, "diplomacy": 3, "wealth": 1, "knowledge": 4, "shadow": 5, "risk": 2},
    },
    {
        "key": "cup",
        "name": "Дом Чаши",
        "motto": "Из изобилия рождается власть",
        "color": "emerald",
        "style": "богатство, гостеприимство, мягкое подчинение",
        "scores": {"power": 1, "diplomacy": 3, "wealth": 5, "knowledge": 2, "shadow": 1, "risk": 2},
    },
]


def get_house_by_key(house_key: str):
    for house in HOUSE_CATALOG:
        if house["key"] == house_key:
            return house
    return None


def get_taken_house_keys(houses):
    return {house.house_key for house in houses if house.house_key}


def score_available_houses(available_houses, answers):
    scored = []

    for house in available_houses:
        total = 0
        for axis, value in answers.items():
            total += house["scores"].get(axis, 0) * value

        scored.append(
            {
                "house": house,
                "score": total,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored