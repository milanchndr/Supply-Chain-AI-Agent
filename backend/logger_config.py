import logging
import sys
import os

def setup_logger(name='AI_SupplyChain_Agent', level=logging.INFO):
    logger = logging.getLogger(name)
    
    
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(level)

    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level) # Set handler level

    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)
    return logger


logger = setup_logger()


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, LOG_LEVEL, None)
if isinstance(numeric_level, int):
    logger.setLevel(numeric_level)
    for handler in logger.handlers:
        handler.setLevel(numeric_level)
else:
    logger.warning(f"Invalid LOG_LEVEL: {LOG_LEVEL}. Defaulting to INFO.")