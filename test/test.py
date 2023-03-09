
from pathlib import Path
import sys
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.append(BASE_DIR)

from configparser import ConfigParser
import sys

config = ConfigParser()
config['DEFAULT'] = {'Pool': '4'}

with open(sys.path[-1] + '/conf/config.ini', 'w',  encoding='utf-8') as configfile:
    config.write(configfile)