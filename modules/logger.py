import logging
import sys

logger = logging.getLogger('race_bot')

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('race_bot')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)

logging.getLogger('httpx').setLevel(logging.WARNING)
