import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(f"logs/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log", encoding="utf-8")
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)