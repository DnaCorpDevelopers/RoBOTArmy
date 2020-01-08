import logging
import logging.config
import os
import yaml

dir_path = os.path.dirname(os.path.realpath(__file__))


class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO


def setup_logging():
    log_dir = os.path.join('logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    f_yaml = os.path.join(dir_path, 'logging.yaml')
    if os.path.exists(f_yaml):
        with open(f_yaml, 'rt') as f:
            try:
                log_conf = yaml.safe_load(f.read())
                logging.config.dictConfig(log_conf)
            except Exception as e:
                logging.basicConfig(level=logging.INFO)
                logging.exception(e)
                logging.error('Error in logging configuration, using default configs')
