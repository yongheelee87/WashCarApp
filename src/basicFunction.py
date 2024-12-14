import os
import pygetwindow as gw
from logging.config import dictConfig
import logging
import win32api
import win32file

BRIGHT_BLACK = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
BRIGHT_WHITE = '\033[97m'
BRIGHT_END = '\033[0m'

def isdir_and_make(dir_name):
    if not (os.path.isdir(dir_name)):
        os.mkdir(dir_name)
        logging_print(BRIGHT_GREEN + "성공: 생성 {}\n".format(dir_name) + BRIGHT_END)
    else:
        logging_print(BRIGHT_GREEN + "성공: 접근 {}\n".format(dir_name) + BRIGHT_END)


def isfile_and_pass(file_path):
    if not os.path.isfile(file_path):
        logging_print(BRIGHT_RED + "실패: 접근 {}\n".format(os.path.basename(file_path)) + BRIGHT_END)
        return False
    else:
        logging_print(BRIGHT_GREEN + "성공: 접근 {}\n".format(os.path.basename(file_path)) + BRIGHT_END)
        return True


def to_do_process_close(keyword_str):
    to_do_process = gw.getWindowsWithTitle(keyword_str)
    num_of_process = len(to_do_process)
    if num_of_process == 0:
        pass
    else:
        for i in range(num_of_process):
            to_do_process[i].close()

def logging_initialize():
    if os. path.isfile("Debug.log"):
        os.remove("Debug.log")
    else:
        pass

    dictConfig({
        'version': 1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s]\n%(message)s',
                'datefmt': '%d-%b-%Y %H:%M:%S'

            },
            'simple': {
                'format': '%(message)s',
            }
        },

        'handlers': {
            'console': {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
             },

            'file': {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "default",
                "encoding": "utf-8",
                "filename": "Debug.log"
            }
        },

        'root': {
            'level': 'INFO',
            'handlers': ["console", "file"]
        }
    })


def logging_print(text):
    logging.info(text)


def get_usb_drive():
    """DRIVE_TYPES
        0  Unknown                 // win32file.DRIVE_UNKNOWN
        1  No Root Directory       // win32file.DRIVE_NO_ROOT_DIR
        2  Removable Disk          // win32file.DRIVE_REMOVABLE
        3  Local Disk              // win32file.DRIVE_FIXED
        4  Network Drive           // win32file.DRIVE_REMOTE
        5  Compact Disc            // win32file.DRIVE_CDROM
        6  RAM Disk                // win32file.DRIVE_RAMDISK
    """
    drive = win32api.GetLogicalDriveStrings()
    drive = drive.split('\000')[:-1]
    drive_list = []
    rdrive = []

    for drv in drive:
        if win32file.GetDriveType(drv) == win32file.DRIVE_REMOVABLE:
            drive_list.append(drv)
    for drv in drive_list:
        try:
            if os.path.getsize(drv) >= 0:
                rdrive.append(drv)
        except OSError:
            pass
    return rdrive


def is_file_close(exe_name):
    to_do_process = gw.getWindowsWithTitle(exe_name)
    if len(to_do_process) == 0:
        return 'Close'
    else:
        return 'Open'

def is_file_exist(file_path):
    if os.path.isfile(file_path):
        return 'Yes'
    else:
        return 'No'