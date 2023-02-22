import logging.config
import os

log_config_path = os.path.join(os.path.dirname(__file__), 'log.ini')
logging.config.fileConfig(log_config_path)
logger = logging.getLogger(__name__)
