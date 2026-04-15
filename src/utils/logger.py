import sys
from loguru import logger

def setup_logger():
    logger.remove()

    FORMAT = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<blue>{process}</blue>:<blue>{thread}</blue> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True,
        backtrace=True,
        diagnose=True,
        format=FORMAT
    )
    return logger

log = setup_logger()
