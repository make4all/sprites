import config
import uuid
import os
from datetime import date
from logHandler import log
import globalVars


confspec = {
	'userID': "string(default='')",
	'logID': "integer(default=0)",
	'spritesID': "integer(default=0)",
	'searchID': "integer(default=0)",
	'firstUse': "boolean(default=True)",
	'logStart': "string(default='')",
	'logPath': "string(default='')"
}

config.conf.spec['sprites'] = confspec
LOG_PATH = os.path.join(globalVars.appArgs.configPath, "addons", "sprites-nvda", "logs")
log.info(LOG_PATH)
def onInstall():
	config.conf['sprites']['userID'] = str(uuid.uuid1())
	config.conf['sprites']['logID'] = 0
	config.conf['sprites']['spritesID'] = 0
	config.conf['sprites']['searchID'] = 0
	config.conf['sprites']['logStart'] = date.today().strftime('%Y-%m-%d')

	path = LOG_PATH
	config.conf['sprites']['logPath'] = path


def onUninstall():
	os.remove(config.conf['sprites']['logPath'] + '\\log.txt')
	os.rmdir(config.conf['sprites']['logPath'])
	config.conf['sprites'] = {}
	config.conf.spec['sprites'] = {}
	config.conf.save()
