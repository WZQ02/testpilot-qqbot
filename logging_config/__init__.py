import logging
import os

def setup_logging():
    print("初始化日志记录...")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,  # Set the minimum logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "bot.log")),  # Log to a file
            logging.StreamHandler()  # Log to console
        ]
    )

    # Optionally, set a higher level for some noisy loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
