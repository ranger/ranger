from __future__ import (absolute_import, division, print_function)

import logging
from collections import deque


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


QUEUE = deque(maxlen=1000)
FMT_NORMAL = logging.Formatter(
    fmt='%(asctime)s %(levelname).4s %(message)s', datefmt='%H:%M:%S')
FMT_DEBUG = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d %(levelname).4s [%(name)s] %(message)s', datefmt='%H:%M:%S')


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
        log_level = logging.DEBUG
        formatter = FMT_DEBUG
    else:
        log_level = logging.INFO
        formatter = FMT_NORMAL

    handlers = []
    handlers.append(QueueHandler(QUEUE))
    if logfile:
        if logfile == '-':
            handlers.append(logging.StreamHandler())
        else:
            handlers.append(logging.FileHandler(logfile))

    for handler in handlers:
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    root_logger.setLevel(0)
