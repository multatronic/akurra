"""Logging module."""
import logging
import logging.config


defaults = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'extended': {
            'format': '%(asctime)s %(name)s.%(levelname)s[%(process)s]: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple_colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'simple_colored'
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log'
        }
        # 'file': {
        #     'class': 'logging.handlers.RotatingFileHandler',
        #     'filename': '/var/log/akurra.log',
        #     'maxBytes': 10485760,
        #     'backupCount': 5,
        #     'formatter': 'extended',
        #     'encoding': 'utf8'
        # }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'syslog']
    }
}


def configure_logging(config=None, debug=False):
    """Configure logging with a provided configuration."""
    cfg = defaults.copy()

    if config:
        cfg.update(config)

    logging.config.dictConfig(cfg)

    if debug:
        logging.root.setLevel(logging.DEBUG)
