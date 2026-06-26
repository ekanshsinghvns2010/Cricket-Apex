import random

STADIUMS = [
    {
        "name": "Wankhede Stadium",
        "country": "India",
        "weather": ["Sunny ☀️", "Cloudy ☁️", "Humid 🌫️"],
        "pitch": "Batting Friendly"
    },
    {
        "name": "Narendra Modi Stadium",
        "country": "India",
        "weather": ["Sunny ☀️", "Cloudy ☁️"],
        "pitch": "Balanced"
    },
    {
        "name": "Eden Gardens",
        "country": "India",
        "weather": ["Cloudy ☁️", "Rainy 🌧️"],
        "pitch": "Spin Friendly"
    },
    {
        "name": "Lord's",
        "country": "England",
        "weather": ["Overcast 🌥️", "Cloudy ☁️"],
        "pitch": "Swing Friendly"
    },
    {
        "name": "The Oval",
        "country": "England",
        "weather": ["Sunny ☀️", "Overcast 🌥️"],
        "pitch": "Balanced"
    },
    {
        "name": "Melbourne Cricket Ground",
        "country": "Australia",
        "weather": ["Sunny ☀️", "Windy 🌬️"],
        "pitch": "Pace Friendly"
    },
    {
        "name": "Newlands",
        "country": "South Africa",
        "weather": ["Windy 🌬️", "Sunny ☀️"],
        "pitch": "Pace Friendly"
    },
    {
        "name": "Gaddafi Stadium",
        "country": "Pakistan",
        "weather": ["Sunny ☀️", "Cloudy ☁️"],
        "pitch": "Batting Friendly"
    }
]

def get_random_stadium():
    stadium = random.choice(STADIUMS)
    return {
        "name": stadium["name"],
        "country": stadium["country"],
        "weather": random.choice(stadium["weather"]),
        "pitch": stadium["pitch"]
    }