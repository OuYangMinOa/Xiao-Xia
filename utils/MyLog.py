import logging
import os
from datetime import datetime


def create_logger(log_folder):

	dir_path = 'logs'# 設定 logs 目錄
	filename = "{:%Y-%m-%d_%X}".format(datetime.now()) + '.log' # 設定檔名

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
