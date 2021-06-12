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
	'logStart': "string(default='')"
}

config.conf.spec['sprites'] = confspec

def onInstall():
	config.conf['sprites']['userID'] = str(uuid.uuid1())
	config.conf['sprites']['logID'] = 0
	config.conf['sprites']['spritesID'] = 0
	config.conf['sprites']['searchID'] = 0
	config.conf['sprites']['logStart'] = date.today().strftime('%Y-%m-%d')

def onUninstall():
	config.conf['sprites'] = {}
	config.conf.spec['sprites'] = {}
	config.conf.save()
