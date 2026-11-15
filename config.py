import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN", "")
PREFIX = os.getenv("PREFIX", "!")
GUILD_ID = os.getenv("GUILD_ID", "")
GUILD_ID = int(GUILD_ID) if GUILD_ID and GUILD_ID.isdigit() else None

COLOR_DEFAULT = 0x3B5866
COLOR_SUCCESS = 0x2ECC71
COLOR_ERROR = 0xE74C3C
COLOR_WARNING = 0xF1C40F
COLOR_INFO = 0x3498DB

MOD_LOG_CHANNEL_ID = os.getenv("MOD_LOG_CHANNEL_ID", "")

ROBLOX_USERS_URL = "https://users.roblox.com/v1/usernames/users"
ROBLOX_USER_INFO_URL = "https://users.roblox.com/v1/users/{user_id}"
ROBLOX_BADGES_URL = "https://badges.roblox.com/v1/users/{user_id}/badges"
ROBLOX_BADGE_IMAGE_URL = "https://www.roblox.com/asset-thumbnail/image?assetId={badge_id}&width=420&height=420&format=png"

RECENT_ACCOUNT_DAYS = 30
