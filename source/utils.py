import os
import logging
import sys


def check_path_exists(path: str) -> bool:

    if(os.path.exists(path)):
        return True
    else:
        return False
    
    
def check_path_writeable(path: str) -> bool:

    if(os.access(path, os.W_OK)):
        return True
    else:
        return False
    

def construct_default_path(folder='APL-Velcro'):
    username = os.getlogin()
    path = 'C:/Users/' + username + '/' + folder + '/'
    if(not os.path.exists(path)):
        os.mkdir(path)                  # Measurement directory

    return path
    

def setup_logging(name: str, level=logging.INFO):

    logging.basicConfig(filename=name, encoding='utf-8', format='%(asctime)s %(levelname)s:%(message)s', level=level, datefmt='%d-%m-%Y %H:%M:%S')
    log = logging.getLogger()
    sys.stderr.write = log.error