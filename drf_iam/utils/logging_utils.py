import logging

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

LOG_LEVEL_COLORS = {
    logging.DEBUG: Colors.BLUE,
    logging.INFO: Colors.GREEN,
    logging.WARNING: Colors.YELLOW,
    logging.ERROR: Colors.RED,
    logging.CRITICAL: Colors.BOLD + Colors.RED,
}

class ColorfulFormatter(logging.Formatter):
    def __init__(self, datefmt='%H:%M:%S'):
        super().__init__(datefmt=datefmt)

    def format(self, record):
        level_color = LOG_LEVEL_COLORS.get(record.levelno, Colors.RESET)
        
        msg_body_color = Colors.WHITE # Default for message body
        if record.levelno == logging.INFO:
            msg_body_color = Colors.GREEN 
        elif record.levelno == logging.DEBUG:
            msg_body_color = Colors.BLUE
        elif record.levelno >= logging.WARNING:
            msg_body_color = level_color # Errors, Warnings use their level's color for message body

        asctime_str = f"{Colors.CYAN}{self.formatTime(record, self.datefmt)}{Colors.RESET}"
        name_str = f"{Colors.MAGENTA}[{record.name}]{Colors.RESET}"
        levelname_str = f"{level_color}{record.levelname.center(8)}{Colors.RESET}" # Padded levelname
        message_str = f"{msg_body_color}{record.getMessage()}{Colors.RESET}"
        
        return f"{asctime_str} {name_str} {levelname_str} : {message_str}"

def setup_colorful_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Sets up and returns a logger instance with colorful formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers: # Avoid adding multiple handlers if called multiple times
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = ColorfulFormatter()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.propagate = False # Prevent double logging if root logger is configured
    return logger
