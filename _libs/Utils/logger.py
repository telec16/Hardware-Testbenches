from pathlib import Path
from datetime import datetime


class Logger:

    def __init__(self, *, logger_id: str, time_format: str = "%H:%M:%S", path: Path = None, default_save: bool = False):
        """Initialize the Logger class.
        If path is None and default_save == False, nothing is written on disk,
        else, default path is ./ or folders are created to math defined path

        :param logger_id: personal id for the logger
        :param time_format: cf Datetime doc
        :param path: path to the log file
        :param default_save: default behaviour when logging (overwritten by save)
        """
        self.__id = logger_id
        self.__time_format = time_format
        self.__path = path or Path("./")
        self.__default_save = default_save
        self.__logfile = None

        if default_save or path is not None:
            self.__path.mkdir(parents=True, exist_ok=True)
            self.__logfile = open((self.__path / self.__id).with_suffix(".log"), "a+", buffering=1)  # Line buffering

    def log(self, lvl: int, logs: str, save: bool = None):
        """Log some text to the console and optionally in a file

        :param lvl: tab level of the log
        :param logs: string to log (multi-lines authorized)
        :param save: save to file ?
        """
        save = save or self.__default_save

        time = datetime.now().strftime(self.__time_format)
        str_lvl = '\t' * lvl
        str_id = self.__id

        log = []
        for l in logs.split('\n'):
            log.append(f'{time} - {str_id}  {str_lvl}{l}')
        log = '\n'.join(log)

        print(log)
        if save and self.__logfile is not None:
            self.__logfile.write(log + "\r\n")

    def __del__(self):
        if self.__logfile is not None:
            self.__logfile.close()


if __name__ == "__main__":
    import time

    logger = Logger(logger_id="loggy", path=Path("D:/log"))

    for i in range(0, 5):
        logger.log(i, "hey !")
        time.sleep(2)

    logger.log(0, "ploup", True)
