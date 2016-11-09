import logging
from collections import deque

LOG_FORMAT = "[%(levelname)s] %(message)s"
LOG_FORMAT_EXT = "%(asctime)s,%(msecs)d [%(name)s] |%(levelname)s| %(message)s"
LOG_DATA_FORMAT = "%H:%M:%S"


class QueueHandler(logging.Handler):
    """
    This handler store logs events into a queue.
    """

    def __init__(self, queue):
        """
        Initialize an instance, using the passed queue.
        """
        logging.Handler.__init__(self)
        self.queue = queue

    def enqueue(self, record):
        """
        Enqueue a log record.
        """
        self.queue.append(record)

    def emit(self, record):
        self.enqueue(self.format(record))


log_queue = deque(maxlen=1000)
concise_formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATA_FORMAT)
extended_formatter = logging.Formatter(fmt=LOG_FORMAT_EXT, datefmt=LOG_DATA_FORMAT)


def setup_logging(debug=True, logfile=None):
    """
    All the produced logs using the standard logging function
    will be collected in a queue by the `queue_handler` as well
    as outputted on the standard error `stderr_handler`.

    The verbosity and the format of the log message is
    controlled by the `debug` parameter

     - debug=False:
            a concise log format will be used, debug messsages will be discarded
            and only important message will be passed to the `stderr_handler`

     - debug=True:
            an extended log format will be used, all messages will be processed
            by both the handlers
    """
    root_logger = logging.getLogger()

    if debug:
        # print all logging in extended format
        log_level = logging.DEBUG
        formatter = extended_formatter
    else:
        # print only warning and critical message
        # in a concise format
        log_level = logging.INFO
        formatter = concise_formatter

    handlers = []
    handlers.append(QueueHandler(log_queue))
    if logfile:
        if logfile is '-':
            handlers.append(logging.StreamHandler())
        else:
            handlers.append(logging.FileHandler(logfile))

    for handler in handlers:
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(0)
