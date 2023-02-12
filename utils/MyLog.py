import logging
import os
from datetime import datetime

dir_path = 'logs'# 設定 logs 目錄
filename = "{:%Y-%m-%d}".format(datetime.now()) + '.log' # 設定檔名

def create_logger(log_folder):

	logging.captureWarnings(True)
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	my_logger = logging.getLogger('py.warnings')
	my_logger.setLevel(logging.INFO)

	os.makedirs(log_folder,exist_ok=True)


	fileHandler = logging.FileHandler(log_folder+'/'+filename, 'w', 'utf-8')
	fileHandler.setFormatter(formatter)
	my_logger.addHandler(fileHandler)



	consoleHandler = logging.StreamHandler()
	consoleHandler.setLevel(logging.DEBUG)
	consoleHandler.setFormatter(formatter)
	my_logger.addHandler(consoleHandler)
	return my_logger

logger = create_logger(dir_path)	