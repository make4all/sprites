# Chrome add-on for SPRITEs

import appModuleHandler
import api
from logHandler import log
import controlTypes
import ui
import speech
from core import callLater
import inputCore
import config
import time
import review
import wx
import gui
import textInfos
import threading
from .spritesTable import SpritesTable
from .dialogs import SearchDialog
from .dialogs import SearchResultDialog
from .dialogs import SpritesSettingsPanel
from .logHelper import LogHelper
import os
from gui import NVDASettingsDialog
import uuid
import traceback
from datetime import date
import webbrowser
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

if 'sprites' not in config.conf:
	config.conf['sprites'] = {}
if 'spritesID' not in config.conf['sprites']:
	config.conf['sprites']['spritesID'] = 0
if 'searchID' not in config.conf['sprites']:
	config.conf['sprites']['searchID'] = 0
if 'logID' not in config.conf['sprites']:
	config.conf['sprites']['logID'] = 0
if 'userID' not in config.conf['sprites']:
	config.conf['sprites']['userID'] = str(uuid.uuid1())
if 'logStart' not in config.conf['sprites'] or config.conf['sprites']['logStart'] == '':
	config.conf['sprites']['logStart'] = date.today().strftime('%Y-%m-%d')
if 'firstUse' not in config.conf['sprites']:
	config.conf['sprites']['firstUse'] = True

# Translators: The key on the right of the "0" key in the alpha-numeric part of the keyboard.
KEY_11 = _("-")
# Translators: The key just on the left of the backspace key.
KEY_12 = _("=")
# Translators: The key just on the left of the "1" key. If this has to be modified for a different layout,
# please also change the key mapping in self.rowKeys definition
ROW_KEY_1 = _("graav")

class AppModule(appModuleHandler.AppModule):

	def __init__(self, *args, **kwargs):
		super(AppModule, self).__init__(*args, **kwargs)
		# store current parsed sprites table
		self.table = None
		# save the state of sprites mode
		self.spritesMode = False
		# define the sprites gestures
		self.keyboard = 'EN_US'
		self.defineGestures()
		# store original inputCore.manager captureFunc
		self.oldCaptureFunc = inputCore.manager._captureFunc
		# save the last key pressed
		self.lastKey = None
		self.lastKeyPressTime = 0
		self.hasAnnouncedTable = False
		self.searching = False
		self.spritesID = None
		self.searchID = None
		self.logHelper = LogHelper()
		self.searchStartTime = None
		NVDASettingsDialog.categoryClasses.append(SpritesSettingsPanel)
		# Not a bug, for some reason it is retrieved as a string when the field is initialized from install task
		# TODO: remove this log statement after confirming firstUse has been changed
		log.info('firstUse: ' + str(config.conf['sprites']['firstUse']))
		if 'firstUse' not in config.conf['sprites'] or config.conf['sprites']['firstUse'] == True:
			self.showFirstUseDialog()

	def showFirstUseDialog(self):
		config.conf['sprites']['firstUse'] = False
		webbrowser.open('https://make4all.github.io/sprites/firstUseMessage.html')

	def terminate(self):
		self.removeHooks()
		inputCore.manager._captureFunc = self.oldCaptureFunc
		NVDASettingsDialog.categoryClasses.remove(SpritesSettingsPanel)

	# ===== table detection related functions ===== #
	def injectHooks(self):
		'''
		Replaces the handleCaretMove function in review mode with custom version with table detection
		'''
		global original_handleCaretMove
		if review.handleCaretMove != self.post_handleCaretMove:
			original_handleCaretMove = review.handleCaretMove
			review.handleCaretMove = self.post_handleCaretMove

	def post_handleCaretMove(self, pos, *args, **kwargs):
		'''
		Detect tables in browse mode.
		'''
		try:
			original_handleCaretMove(pos, *args, **kwargs)
			tableInfo = self.getTableInfo()
			if tableInfo and not self.hasAnnouncedTable and not self.spritesMode:
				self.hasAnnouncedTable = True
				# Translators: message announcing sprites mode is available upon entry to a table
				ui.message(_('Sprites mode available. Press NVDA+Shift+T to activate.'))
				self.logHelper.logTableFound(None, None, tableInfo[1], tableInfo[2])
			if not tableInfo:
				self.hasAnnouncedTable = False
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def removeHooks(self):
		'''
		Restores the replaced functions on terminate
		'''
		review.handleCaretMove = original_handleCaretMove

	# ===== end of table detection related functions ===== #

	def defineGestures(self):
		'''
		Defines all gestures available during sprites mode, including:
		1. The row and column keys for table exploration
		2. Special (modifier) keys for manual overwrite
		3. Other keys map to misc functions (exit, search, cancel speech, etc.)
		'''
		self.rowKeys = None
		self.columnKeys = None
		self.otherKeys = None
		self.specialKeys = None
		if self.keyboard == 'EN_US':
			self.rowKeys = ['`', 'tab', 'capsLock', 'leftShift', 'leftControl']
			self.columnKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', KEY_11, KEY_12]
			self.specialKeys = {'capsLock', 'leftShift', 'leftControl'}
			self.otherKeys = {'escape', 'f', 'upArrow', 'downArrow', 'rightShift', 'rightControl', 'r', 'c', 'b'}
		# save all gestures available when sprites mode is on in a set
		self.spritesGestures = set()
		self.addAllGestures(self.rowKeys)
		self.addAllGestures(self.columnKeys)
		self.addAllGestures(self.otherKeys)

	def addAllGestures(self, keys):
		'''
		Adds the given collection of keys into the sprites gesture set
		'''
		for key in keys:
			self.spritesGestures.add(key)

	def script_spritesOn(self, gesture):
		'''
		Toggle sprites mode on and set up the table state and gestures
		'''
		try:
			# retreive the table object and tableID if available
			tableInfo = self.getTableInfo()
			if tableInfo:
				tableID, rowCount, columnCount = tableInfo
				self.table = SpritesTable(tableID, rowCount, columnCount, len(self.rowKeys), len(self.columnKeys))
				# Translators: message announcing sprites mode activation and the key to exit
				ui.message(_('Sprites mode on. Press escape to exit. Press F to enter search mode.'))
				# bind gestures to the table
				self.bindSpritesGesture()
				# disable other gestures
				self.toggleSpritesGesture(True)
				self.spritesID = int(config.conf['sprites']['spritesID']) + 1
				config.conf['sprites']['spritesID'] = self.spritesID
				self.logHelper.logSpritesToggle(self.spritesID, None, 'on')
				self.logHelper.logTableInfo(self.spritesID, None, rowCount, columnCount)
				self.speakMapping()
				self.spritesMode = True
			else:
				# Translators: message when sprites mode is not available
				ui.message(_('Not a table. Sprites mode unavailable'))
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())


	def getTableInfo(self):
		'''
		Returns the table object and the tableID associated with the given navigator object
		Returns None if the navigator is currently not in a table
		'''
		focus = api.getFocusObject()
		try:
			selection = focus.treeInterceptor.selection
			tableID, origRow, origCol, origRowSpan, origColSpan = focus.treeInterceptor._getTableCellCoords(selection)
			if selection.isCollapsed:
				selection = selection.copy()
				selection.expand(textInfos.UNIT_CHARACTER)
			fields = list(selection.getTextWithFields())
			for field in fields:
				if not (isinstance(field, textInfos.FieldCommand) and field.command == "controlStart"):
					# Not a control field.
					continue
				attrs = field.field
				tableID = attrs.get('table-id')
				if tableID is not None:
					break
			return (attrs["table-id"],
				int(attrs["table-rowcount"]), int(attrs["table-columncount"]))
		except (AttributeError, LookupError):
			return None

	def bindSpritesGesture(self):
		'''
		Binds all sprites related gestures
		'''
		self.bindGesture('kb:escape', 'spritesOff')
		self.bindGesture('kb:upArrow', 'toPrevResult')
		self.bindGesture('kb:downArrow', 'toNextResult')
		self.bindGesture('kb:r', 'speakRowNumber')
		self.bindGesture('kb:c', 'speakColumnNumber')
		self.bindGesture('kb:b', 'speakBothNumber')

		for key in self.columnKeys:
			self.bindGesture(f'kb:{key}', 'changeColumnSelection')
		for key in self.rowKeys:
			self.bindGesture(f'kb:{key}', 'changeRowSelection')
		self.bindGesture(f'kb:f', 'spritesSearchOn')

	def speakMapping(self):
		'''
		Announces the current key mapping and scroll controls
		'''
		self.speakRowColumnKeyMapping()
		self.speakScrollKeyControl()

	def speakRowColumnKeyMapping(self):
		'''
		Announces key mapping for exploring row and columns
		'''
		mappedRows = self.table.getMappedRows()
		mappedColumns = self.table.getMappedColumns()
		# handle graav key not being spoken as it-is
		mappedRowRange = list(self.rowKeys[0:len(mappedRows)])
		mappedRowRange[0] = ROW_KEY_1

		rowCombo = ', '.join(mappedRowRange)
		if len(mappedColumns) == 1:
			columnCombo = '1'
		else:
			columnCombo = f'1 through {len(mappedColumns)}'
		mappedRowsString = ' '.join(str(r) for r in mappedRows)
		mappedColumnsString = ' '.join(str(c) for c in mappedColumns)
		# Translators: announces the mapping from each key to each row number and column number
		ui.message(_(f'Keys {rowCombo} mapped to row {mappedRowsString}'))
		ui.message(_(f'Keys {columnCombo} mapped to column {mappedColumnsString}'))
		self.logHelper.logMapping(self.spritesID, self.searchID, mappedRows, mappedColumns)

	def speakScrollKeyControl(self):
		'''
		Announces scroll key controls if available
		'''
		rowScrollKeys = []
		if self.table.hasPreviousRows():
			# handle graav key not being spoken as it-is
			rowScrollKeys.append(ROW_KEY_1)
		if self.table.hasNextRows():
			rowScrollKeys.append(self.rowKeys[-1])
		if rowScrollKeys:
			rowScrollKeys = ' and '.join(rowScrollKeys)
			# Translators: message on the control for row scroll keys
			ui.message(_(f'Use key {rowScrollKeys} for exploring more rows'))

		columnScrollKeys = []
		if self.table.hasPreviousColumns():
			columnScrollKeys.append(self.columnKeys[0])
		if self.table.hasNextColumns():
			columnScrollKeys.append(self.columnKeys[-1])
		if columnScrollKeys:
			columnScrollKeys = ' and '.join(columnScrollKeys)
			# Translators: message on the control for column scroll keys
			ui.message(_(f'Use key {columnScrollKeys} for exploring more columns'))

	def toggleSpritesGesture(self, useSprites=False):
		'''
		If useSprites is on, inputCore will use the custom capture func, which allows
		associating capslock, leftShift and leftControl with actions and disables other
		gestures on the keyboard
		otherwise use the default captureFunc.
		'''
		if useSprites:
			inputCore.manager._captureFunc = self.captureFunc
		else:
			inputCore.manager._captureFunc = self.oldCaptureFunc

	def captureFunc(self, gesture):
		'''
		Returns True if the given gesture will pass through to NVDA, False otherwise
		'''
		try:
			key = gesture._keyNamesInDisplayOrder[0]
			if config.conf["keyboard"]["useCapsLockAsNVDAModifierKey"] and key == 'NVDA':
				key = 'capsLock'
			if self.spritesMode and key in self.spritesGestures:
				# Hack for overwriting the modifier keys and bind them to some action
				if key in self.specialKeys:
					callLater(0, self.script_changeRowSelection, gesture)
					return False
				return True
			else:
				# announce gesture unavailable
				callLater(0, self.speakUndefinedGesture, key)
				return False
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def event_appModule_loseFocus(self):
		'''
		Set inputCore to use default captureFunc if not focus on chrome
		'''
		self.toggleSpritesGesture(False)
		self.removeHooks()

	def event_appModule_gainFocus(self):
		'''
		Determine which captureFunc to use when focus back on chrome
		'''
		if self.spritesMode:
			self.toggleSpritesGesture(True)
		self.injectHooks()

	def speakUndefinedGesture(self, key):
		'''
		Announce the gesture is undefined
		'''
		# Translators: message presented when the user presses keys is not defined in Sprites mode
		ui.message(_('gesture not available. Press escape to exit Sprites'))
		self.logHelper.logErrorGesture(self.spritesID, self.searchID, key)

	def script_spritesOff(self, gesture):
		'''
		Turn off Sprites and clear the states and gestures
		'''
		if self.table.searchActive():
			self.clearSearch()
		else:
			self.table = None
			self.clearTableGesture()
			self.spritesMode = False
			# Translators: message presented when turn off sprites mode
			ui.message(_('Sprites mode off'))
			self.logHelper.logSpritesToggle(self.spritesID, None, 'off')

	def clearTableGesture(self):
		'''
		Clears the sprites gesture bindings and resets to default gestures
		'''
		self.clearGestureBindings()
		self.bindGestures(self.__gestures)
		self.toggleSpritesGesture(False)

	def script_speakRowNumber(self, gesture):
		'''
		Announces the row number of the selected cell
		'''
		ui.message(_((f'Row {self.table.getCurrPosition()[0]}')))

	def script_speakColumnNumber(self, gesture):
		'''
		Announces the column number of the selected cell
		'''
		ui.message(_((f'Column {self.table.getCurrPosition()[1]}')))

	def script_speakBothNumber(self, gesture):
		'''
		Announces both the row number and the column number of the selected cell
		'''
		ui.message(_((f'Row {self.table.getCurrPosition()[0]} Column {self.table.getCurrPosition()[1]}')))

	def script_changeColumnSelection(self, gesture):
		'''
		Set the column selected in the SpritesTable to the one given by the gesture
		'''
		try:
			key = gesture._keyNamesInDisplayOrder[0]
			keyIdx = self.columnKeys.index(key)
			if self.table.getColumn(keyIdx) is None:
				# Translators: message presented when the key press maps to outside the table
				ui.message(_('edge of table'))
				self.logHelper.logErrorEdge(self.spritesID, self.searchID, key)
			elif self.isDoublePress(key) and self.isScrollKey(keyIdx, 1):
				self.scroll(keyIdx, 1)
				self.logHelper.logNav(self.spritesID, self.searchID, key, True)
			else:
				self.speakCell(column=keyIdx)
				self.logHelper.logNav(self.spritesID, self.searchID, key, False)
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def script_changeRowSelection(self, gesture):
		'''
		Set the row selected in the SpritesTable to the one given by the gesture
		'''
		try:
			key = gesture._keyNamesInDisplayOrder[0]
			# handles the case where capsLock is the NVDA key
			if key == 'NVDA':
				key = 'capsLock'
			keyIdx = self.rowKeys.index(key)
			if self.table.getRow(keyIdx) is None:
				# Translators: message presented when the key press maps to outside the table
				ui.message(_('edge of table'))
				self.logHelper.logErrorEdge(self.spritesID, self.searchID, key)
			elif self.isDoublePress(key) and self.isScrollKey(keyIdx, 0):
				self.scroll(keyIdx, 0)
				self.logHelper.logNav(self.spritesID, self.searchID, key, True)
			else:
				self.speakCell(row=keyIdx)
				self.logHelper.logNav(self.spritesID, self.searchID, key, False)
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def speakCell(self, row=None, column=None):
		'''
		Speaks announcements associate with the given cell. If one of the params is not
		specified, use the last spoken row or column.
		Announcements include:
		1. (If in search mode) 'Found' if the search keyword is found in given cell
		2. Position and content of the given cell
		3. (If in search mode) number of other occurrences in the same row/column, if any
		4. Scroll key action if is scroll key and scroll action is available
		'''
		formatConfig=config.conf["documentFormatting"].copy()
		formatConfig["reportTables"]=True
		# Retrieve text info at given position and also move the cursor over
		info = self.table.getCellAt(row=row, column=column)
		currRow, currColumn = self.table.getCurrPosition()
		if self.table.hasResultAt(currRow, currColumn):
			ui.message(_('Found'))
		speech.speakTextInfo(info, formatConfig=formatConfig, reason=controlTypes.OutputReason.CARET)
		# Announce other occurrences on the same row/column
		# if the given position contains search result, would exclude current position
		# when calculating the occurrences
		if self.table.getSearchResults():
			numInRow, numInColumn = self.table.getOccurrences()
			if row is not None and numInRow:
				ui.message(f'{numInRow} more found in this row')
			if column is not None and numInColumn:
				ui.message(f'{numInColumn} more found in this column')
		# Announce scroll key control
		if row is None or column is None:
			direction = 0 if column is None else 1
			keyIdx = row if column is None else column
			if self.isScrollKey(keyIdx, direction):
				self.speakScrollKey(keyIdx, direction)

	def isScrollKey(self, keyIdx, direction):
		'''
		Returns true if the given key index represents a scroll key for the given direction
		direction is 0 for row and 1 for column
		'''
		keyLength = len(self.rowKeys) if direction == 0 else len(self.columnKeys)
		return keyIdx == 0 or keyIdx == keyLength - 1

	def speakScrollKey(self, keyIdx, direction):
		'''
		Announces the scroll key controls if the given key index is a scroll key and scrolling is available
		for the given direction
		direction is 0 for row and 1 for column
		'''
		if direction == 0 and ((keyIdx == 0 and self.table.hasPreviousRows()) or (keyIdx != 0 and self.table.hasNextRows())):
			# Translators: message presented when the scroll key is double pressed and more rows are available for scroll
			ui.message(_('double press to explore more rows'))
		elif direction == 1 and ((keyIdx == 0 and self.table.hasPreviousColumns()) or (keyIdx != 0 and self.table.hasNextColumns())):
			# Translators: message presented when the scroll key is double pressed and more columns are available for scroll
			ui.message(_('double press to explore more columns'))
	
	def scroll(self, keyIdx, direction):
		'''
		Scrolls the table at the given direction based on which scroll key is pressed
		key is 0 if it is the scroll key for previous, otherwise it is the scroll key for next
		direction is 0 for row and 1 for column
		'''
		previousOrNext = 'previous' if keyIdx == 0 else 'next'
		rowOrColumn = 'rows' if direction == 0 else 'columns'

		if not self.table.scroll(direction, keyIdx):
			# Translators: message presented when the scroll is not available
			ui.message(_(f'no {previousOrNext} set of {rowOrColumn} available'))
		else:
			# Translators: message presented when the scroll is successfully performed
			ui.message(_(f'{previousOrNext} set of {rowOrColumn} loaded'))
			self.speakMapping()

	def isDoublePress(self, key):
		'''
		Returns true if the given key has been double-pressed, false otherwise
		'''
		currTime = time.time()
		diff = currTime - self.lastKeyPressTime
		result = self.lastKey == key and diff < 0.5 and diff > 0.1
		self.lastKeyPressTime = currTime
		self.lastKey = key
		return result

	# ===== Search related functions ===== #
	def script_spritesSearchOn(self, gesture):
		'''
		Pops the sprites search window
		'''
		def run():
			gui.mainFrame.prePopup()
			keyword = '' if not self.table.searchActive() else self.table.getSearchTerm()
			dialog = SearchDialog(gui.mainFrame, self, keyword)
			dialog.ShowModal()
			gui.mainFrame.postPopup()
		# TODO: add a way to cancel current search?
		try:
			if not self.searching:
				self.searchID = int(config.conf['sprites']['searchID']) + 1
				config.conf['sprites']['searchID'] = self.searchID
				self.logHelper.logSearchToggle(self.spritesID, self.searchID, 'on')
				wx.CallAfter(run)
			else:
				ui.message(_('Searching. Wait for current search to finish.'))
				self.logHelper.logErrorSearching(self.spritesID, self.searchID)
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def onSearch(self, keyword, caseSensitive, filterRows, filterColumns):
		'''
		Validates the search term and initiates search on a different thread
		'''
		try:
			if keyword == '':
				wx.CallAfter(gui.messageBox,_('Please enter a search term'),_("Find Error"),wx.OK|wx.ICON_ERROR)
			else:
				x = threading.Thread(target=self.table.searchTable, args=(keyword, caseSensitive, filterRows, filterColumns, self.onSearchComplete))
				self.logHelper.logSearchConfig(self.spritesID, self.searchID, caseSensitive, filterRows, filterColumns)
				self.searchStartTime = time.time()
				x.daemon = True
				x.start()
				self.searching = True
				ui.message(_('Searching'))
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def onSearchComplete(self, found, keyword):
		'''
		Pops the search result window
		'''
		self.searching = False
		if not found:
			wx.CallAfter(gui.messageBox,_(f'{keyword} not found'),_("Find Error"),wx.OK|wx.ICON_ERROR)
		else:
			numResults = len(self.table.getSearchResults())
			self.logHelper.logSearchResult(self.spritesID, self.searchID, self.table.getSearchResults(), time.time() - self.searchStartTime)
			self.popResults(numResults)

	def onJump(self, jump):
		'''
		If jump is True, align the table to the first search result and announce the mapping
		Also announces the search controls
		'''
		try:
			self.table.checkAndApplyFilters()
			if self.table.isFiltered():
				if self.table.isRowFiltered():
					ui.message('Row filter applied')
				if self.table.isColumnFiltered():
					ui.message('Column filter applied')
			if jump:
				self.table.alignTable()
				ui.message(f'result {self.table.getResultIndex()} of {len(self.table.getSearchResults())}')
				self.speakCell(0, 0)
				self.speakMapping()
			ui.message(_('Use up or down arrow to explore search results'))
			ui.message(_('Press escape to exit search mode'))
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def popResults(self, occurrences):
		'''
		Pops the search result window with the given number of occurrences
		'''
		def run():
			gui.mainFrame.prePopup()
			dialog = SearchResultDialog(gui.mainFrame, self, occurrences, self.table.isFiltered())
			dialog.ShowModal()
			gui.mainFrame.postPopup()
		wx.CallAfter(run)

	def clearSearch(self):
		'''
		Clears the search in the table, effectively exits the search mode
		'''
		self.table.clearSearch()
		ui.message(_('Sprites search mode off'))
		self.logHelper.logSearchToggle(self.spritesID, self.searchID, 'off')
		self.searchID = None
		self.speakMapping()

	def script_toNextResult(self, gesture):
		'''
		Jumps to the next search result if available
		'''
		try:
			if not self.table.searchActive():
				ui.message(_('not in search mode'))
			else:
				if self.table.nextResult():
					ui.message(f'result {self.table.getResultIndex()} of {len(self.table.getSearchResults())}')
					self.speakCell(0, 0)
					self.logHelper.logSearchNav(self.spritesID, self.searchID, 'next', self.table.getResultIndex())
					ui.message(_('Use up or down arrow to explore other search results'))
					self.speakMapping()
				else:
					ui.message(_('no more available search results'))
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	def script_toPrevResult(self, gesture):
		'''
		Jumps to the previous search result if available
		'''
		try:
			if not self.table.searchActive():
				ui.message(_('not in search mode'))
			else:
				if self.table.prevResult():
					ui.message(f'result {self.table.getResultIndex()} of {len(self.table.getSearchResults())}')
					self.speakCell(0, 0)
					self.logHelper.logSearchNav(self.spritesID, self.searchID, 'prev', self.table.getResultIndex())
					ui.message(_('Use up or down arrow to explore other search results'))
					self.speakMapping()
				else:
					ui.message(_('no more available search results'))
		except Exception:
			self.logHelper.logErrorException(None, None, traceback.format_exc())

	# ===== End of search related functions ===== #

	__gestures = {
		"kb:NVDA+SHIFT+T": "spritesOn",
	}
