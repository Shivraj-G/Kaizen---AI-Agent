import logging

from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler("kaizenlogs.log",maxBytes= 1_000_000_000,backupCount=4,encoding="utf-8")

logging.basicConfig(level=logging.WARNING, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",handlers=[logging.StreamHandler(),file_handler])
logging.getLogger("__main__").setLevel(logging.DEBUG)