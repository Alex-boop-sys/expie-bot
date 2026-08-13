from config import var, log, env
from Cogs.dicts import dicts
import platform
import re
import sys

class Utils:
    def __init__(self):
        self.current_os = platform.system().lower()

    @staticmethod
    def get_size_limit(guild):
        if guild is None:
            return 8 * 1024 * 1024
        return var.limits.get(guild.premium_tier, 8 * 1024 * 1024)

    @staticmethod
    def have_nsfw(text):
        text_lower = text.lower()
        for pattern in dicts.nsfw_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    @staticmethod
    def check_tokens():
        for name, value in env:
            if value is None:
                log.fatal(f"Токен {name} не найден!")
                sys.exit(1)

utils = Utils()