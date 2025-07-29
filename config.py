from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Headers
    header_font: str = "Segoe UI"
    header_font_size: int = 20
    header_font_color: str = "white"

    # Body
    body_font: str = "Segoe UI"
    body_font_size: int = 16
    body_font_color: str = "white"

    # Colors
    green: str = "#2c8a21"
    red: str = "#ff0000"
    blue: str = "#116ed9"
    yellow: str = "#ffff00"
    purple: str = "#8523c2"
    orange: str = "#ffa500"

config = Config()
