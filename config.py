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

config = Config()
