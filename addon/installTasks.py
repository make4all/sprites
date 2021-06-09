import config
import uuid
import os
from datetime import date
from logHandler import log


confspec = {
	'userID': "string(default='')",
	'logID': "integer(default=0)",
	'spritesID': "integer(default=0)",
	'searchID': "integer(default=0)",
	'firstUse': "boolean(default=False)",
	'logStart': "string(default='')",
	'logPath': "string(default='')"
}

config.conf.spec['sprites'] = confspec


def onInstall():
	config.conf['sprites']['userID'] = str(uuid.uuid1())
	config.conf['sprites']['logID'] = 0
	config.conf['sprites']['spritesID'] = 0
	config.conf['sprites']['searchID'] = 0
	config.conf['sprites']['firstUse'] = True
	config.conf['sprites']['logStart'] = date.today().strftime('%Y-%m-%d')

	path = os.path.join(os.environ['APPDATA'], 'nvda\\sprites')
	config.conf['sprites']['logPath'] = path
	if not os.path.exists(path):
		os.makedirs(path)
	logFileName = path + '\\log.txt'
	f = open(logFileName, 'w', encoding='utf-8')
	f.close()


def onUninstall():
	os.remove(config.conf['sprites']['logPath'] + '\\log.txt')
	os.rmdir(config.conf['sprites']['logPath'])
