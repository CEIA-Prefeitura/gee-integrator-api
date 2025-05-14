import os
import sys

from dynaconf import Dynaconf
from loguru import logger


def start_logger():
    type_logger = "development"
    if os.environ.get("TILES_ENV") == "production":
        type_logger = "production"
    logger.info(f"The system is operating in mode {type_logger}")


confi_format = "[ {time} | process: {process.id} | {level: <8}] {module}.{function}:{line} {message}"
rotation = "500 MB"

if os.environ.get("TILES_ENV") == "production":
    logger.remove()
    logger.add(sys.stderr, level="INFO", format=confi_format)

try:
    logger.add("/logs/tiles/tiles.log", rotation=rotation, level="INFO")
except:
    logger.add(
        "./logs/tiles/tiles.log",
        rotation=rotation,
        level="INFO",
    )
try:
    logger.add(
        "/logs/tiles/tiles_WARNING.log",
        level="WARNING",
        rotation=rotation,
    )
except:
    logger.add(
        "./logs/tiles/tiles_WARNING.log",
        level="WARNING",
        rotation=rotation,
    )

settings = Dynaconf(
    envvar_prefix="ECOTILES",
    settings_files=[
        "settings.toml",
        ".secrets.toml",
        "../settings.toml",
        "/data/settings.toml",
    ],
    environments=True,
    load_dotenv=True,
)

env = Dynaconf(
    environments=True,
    load_dotenv=False,
    envvar_prefix=False,
    case_sensitive=True
)


required_keys_map = {
    "SSO_SERVER_URL": env.get("SSO_SERVER_URL"),
    "SSO_REALM": env.get("SSO_REALM"),
    "SSO_CLIENT_ID": env.get("SSO_CLIENT_ID"),
    "SSO_CLIENT_SECRET": env.get("SSO_CLIENT_SECRET"),
    "SSO_ADMIN_CLIENT_SECRET": env.get("SSO_ADMIN_CLIENT_SECRET"),
    "SSO_CALLBACK_URI": env.get("SSO_CALLBACK_URI"),
    "VALKEY_HOST": env.get("VALKEY_HOST"),
    "VALKEY_PORT": env.get("VALKEY_PORT"),
}

missing_keys = [key for key, value in required_keys_map.items() if value is None]

if missing_keys:
    logger.error(f"As seguintes configurações estão faltando: {', '.join(missing_keys)}")