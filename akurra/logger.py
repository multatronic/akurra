"""Logging module."""
import logging
import logging.config


DEBUG_LEVEL_INSANE_NUM = 9


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


def configure_logging(config=None, log_level='NOT_SET'):
    """Configure logging with a provided configuration."""
    cfg = defaults.copy()

    if config:
        cfg.update(config)

    logging.config.dictConfig(cfg)

    # Add log level: insane
    def insane(self, message, *args, **kwargs):
        if self.isEnabledFor(DEBUG_LEVEL_INSANE_NUM):
            self._log(DEBUG_LEVEL_INSANE_NUM, message, args, **kwargs)

    logging.addLevelName(DEBUG_LEVEL_INSANE_NUM, 'INSANE')
    logging.INSANE = DEBUG_LEVEL_INSANE_NUM
    logging.Logger.insane = insane

    logging.root.setLevel(getattr(logging, log_level))
