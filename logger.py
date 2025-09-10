import logging
import os
from datetime import datetime

def setup_logger(name, level=logging.INFO):
    """To set up as many loggers as you want"""

    # Ensure the 'logs' directory exists
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Set up the formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create the log file name
    td = datetime.today().date()
    log_file = os.path.join(log_dir, f"{name}_{td}.log")

    # Set up the file handler
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    # Get or create the logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Add a stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Setup loggers
child2WSLogger = setup_logger('Log_Child2_WS', level=logging.INFO)
child3WSLogger = setup_logger('Log_Child3_WS', level=logging.INFO)
child4WSLogger = setup_logger('Log_Child4_WS', level=logging.INFO)
master1WSLogger = setup_logger('Log_Master1_WS', level=logging.INFO)
applicationLogger = setup_logger('applicationLogger', level=logging.INFO)

#################################################LOGGER EXAMPLE ####################################
# Example usage
# masterLogger.info("This is an informational message for masterLogger")
# masterLogger.warning("This is a warning message for masterLogger")
# masterLogger.error("This is an error message for masterLogger")

# consoleLogger.info("This is an informational message for consoleLogger")
# consoleLogger.warning("This is a warning message for consoleLogger")
# consoleLogger.error("This is an error message for consoleLogger")

# childLogger.info("This is an informational message for childLogger")
# childLogger.warning("This is a warning message for childLogger")
# childLogger.error("This is an error message for childLogger")
