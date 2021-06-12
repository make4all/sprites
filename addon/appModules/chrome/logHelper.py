import json
from datetime import datetime
from datetime import date
import threading
import config
from logHandler import log
import addonHandler
import os

ADDON_NAME = addonHandler.getCodeAddon().manifest["name"]

def thisAddon():
	for addon in addonHandler.getRunningAddons():
		if addon.name == ADDON_NAME:
			return addon
	return None

class LogHelper:

	def __init__(self):
		addon = thisAddon()
		if addon is None:
			raise RuntimeError('Error retrieving addon path')
		else:
			self.path = os.path.join(addon.path, 'logs')
			self.logFileName = os.path.join(self.path, 'log.txt')
			if not os.path.exists(self.path):
				try:
					os.makedirs(self.path)
					f = open(self.logFileName, 'w', encoding='utf-8')
					f.close()
				except Exception:
					raise RuntimeError('Error creating log file directory')
			self.lock = threading.Lock()
			self.checkDate()

	def checkDate(self):
		dateString = config.conf['sprites']['logStart']
		# dateString is in the form 'YYYY-MM-DD'
		startDate = date(int(dateString[0:4]), int(dateString[5:7]), int(dateString[8:]))
		delta = date.today() - startDate
		if delta.days > 30:
			self.clearLog()
			config.conf['sprites']['logStart'] = datetime.today().strftime('%Y-%m-%d')

	def clearLog(self):
		with self.lock:
			try:
				f = open(self.logFileName, 'w', encoding='utf-8')
				f.close()
			except Exception:
				raise RuntimeError('Failed to clear log file')

	def log(self, logObj):
		with self.lock:
			try:
				f = open(self.logFileName, 'a', encoding='utf-8')
				print(logObj.stringify(), file=f)
				f.close()
			except Exception:
				raise RuntimeError('Cannot write to log file')

	def logSpritesToggle(self, spritesID, searchID, state):
		self.updateID()
		obj = LogObj('sprites_toggle', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'state': state})
		self.log(obj)

	def logTableInfo(self, spritesID, searchID, row, col):
		self.updateID()
		obj = LogObj('table_info', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'row': row, 'col': col})
		self.log(obj)

	def logTableFound(self, spritesID, searchID, row, col):
		self.updateID()
		obj = LogObj('table_found', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'row': row, 'col': col})
		self.log(obj)

	def logMapping(self, spritesID, searchID, rows, cols):
		self.updateID()
		obj = LogObj('mapping', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'rows': rows, 'cols': cols})
		self.log(obj)

	def logNav(self, spritesID, searchID, key, scroll):
		self.updateID()
		obj = LogObj('nav', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'key': key, 'scroll': scroll})
		self.log(obj)

	def logSearchToggle(self, spritesID, searchID, state):
		self.updateID()
		obj = LogObj('search_toggle', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'state': state})
		self.log(obj)

	def logSearchNav(self, spritesID, searchID, direction, index):
		self.updateID()
		obj = LogObj('search_nav', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'direction': direction, 'index': index})
		self.log(obj)

	def logSearchConfig(self, spritesID, searchID, case, rowF, colF):
		self.updateID()
		obj = LogObj('search_config', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'case': case, 'row_f': rowF, 'col_f': colF})
		self.log(obj)

	def logSearchResult(self, spritesID, searchID, results, duration):
		self.updateID()
		obj = LogObj('search_result', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'results': results, 'duration': duration})
		self.log(obj)

	def logErrorException(self, spritesID, searchID, message):
		self.updateID()
		obj = LogObj('error_exception', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'message': message})
		self.log(obj)

	def logErrorEdge(self, spritesID, searchID, key):
		self.updateID()
		obj = LogObj('error_edge', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'key': key})
		self.log(obj)

	def logErrorGesture(self, spritesID, searchID, key):
		self.updateID()
		obj = LogObj('error_gesture', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({'key': key})
		self.log(obj)

	def logErrorSearching(self, spritesID, searchID):
		self.updateID()
		obj = LogObj('error_searching', config.conf['sprites']['logID'], spritesID, searchID)
		obj.addInfo({})
		self.log(obj)

	def updateID(self):
		with self.lock:
			config.conf['sprites']['logID'] = int(config.conf['sprites']['logID']) + 1


class LogObj:

	def __init__(self, logType, logID, spritesID, searchID):
		self.obj = {}
		self.obj['type'] = logType
		self.obj['time'] = f'{datetime.now()}'
		self.obj['log_id'] = logID
		self.obj['sprites_id'] = spritesID
		self.obj['search_id'] = searchID
	
	def addInfo(self, info):
		self.obj['info'] = info

	def stringify(self):
		return json.dumps(self.obj)
