try:
	import api
	import re
	import textInfos
	from logHandler import log
except ModuleNotFoundError:
	pass


class SpritesTable():
	'''
	A class keeping track of the states of the sprites table
	'''
	def __init__(self, tableObj, tableID, rowKeyCount, columnKeyCount, test=False):
		self.tableID = tableID
		if not test:
			self.interceptor = api.getFocusObject().treeInterceptor

		# stores the initial row and column count for the table object
		self.rowCount = tableObj.rowCount
		self.columnCount = tableObj.columnCount
		# list of row and column index including all rows and columns
		self.allRows = [r + 1 for r in range(self.rowCount)]
		self.allColumns = [c + 1 for c in range(self.columnCount)]
		# list of explorable row and column index
		self.rows = list(self.allRows)
		self.columns = list(self.allColumns)
		self.currRow = self.rows[0]
		self.currColumn = self.columns[0]
		# initialize offset indices for keeping track of scrolling state
		self.rowOffset = 0
		self.columnOffset = 0

		# stores the key counts
		self.rowKeyCount = rowKeyCount
		self.columnKeyCount = columnKeyCount

		# stores the search state
		self.searchTerm = None
		self.searchResults = None
		self.resultIdx = 0

		# whether the current cursor is on a search result or not
		self.onSearchResult = False
		self.filterRows = False
		self.filterColumns = False

	def expandTable(self):
		'''
		Expand the state of the table from filter mode when exit search
		'''
		rowDelta = self.rows.index(self.currRow) - self.rowOffset
		columnDelta = self.columns.index(self.currColumn) - self.columnOffset
		self.rowOffset = self.allRows.index(self.currRow) - rowDelta
		self.columnOffset = self.allColumns.index(self.currColumn) - columnDelta
		self.rows = list(self.allRows)
		self.columns = list(self.allColumns)

	def getCellAt(self, row=None, column=None):
		'''
		Returns the TextInfo associated with the cell at the given row and column and sets the
		browse mode cursor to that text info
		Assumes the given row and column are valid
		'''
		if row is not None:
			self.currRow = self.rows[self.rowOffset + row]
		if column is not None:
			self.currColumn = self.columns[self.columnOffset + column]
		selection = self.interceptor.selection
		info = self.interceptor._getTableCellAt(self.tableID, selection, self.currRow, self.currColumn)
		# move browse mode selection
		self.interceptor.selection = info
		log.info(f'switch to row {self.currRow} column {self.currColumn}')
		return info

	def changeRowOffset(self, delta):
		'''
		Modifies the row offset by the given delta or set to 0 if the result will be negative
		Also aligns current row to the offset
		'''
		self.rowOffset = max(0, self.rowOffset + delta)
		self.currRow = self.rows[self.rowOffset]

	def changeColumnOffset(self, delta):
		'''
		Modifies the column offset by the given delta or set to 0 if the result will be negative
		Also aligns current column to the offset
		'''
		self.columnOffset = max(0, self.columnOffset + delta)
		self.currColumn = self.columns[self.columnOffset]

	def scroll(self, direction, keyIdx):
		'''
		Performs the scroll action based on the given direction, return True if the specified
		scroll is possible, False otherwise
		direction is 0 for row and 1 for column
		'''
		if direction == 0:
			if keyIdx != 0 and self.hasNextRows():
				self.changeRowOffset(self.rowKeyCount)
				return True
			elif keyIdx == 0 and self.hasPreviousRows():
				self.changeRowOffset(-self.rowKeyCount)
				return True
			else:
				return False
		else:
			if keyIdx != 0 and self.hasNextColumns():
				self.changeColumnOffset(self.columnKeyCount)
				return True
			elif keyIdx == 0 and self.hasPreviousColumns():
				self.changeColumnOffset(-self.columnKeyCount)
				return True
			else:
				return False

	def hasNextRows(self):
		'''
		Returns true if the next set of rows is available to load, false otherwise
		'''
		return self.rowOffset + self.rowKeyCount < len(self.rows)

	def hasNextColumns(self):
		'''
		Returns true if the next set of columns is available to load, false otherwise
		'''
		return self.columnOffset + self.columnKeyCount < len(self.columns)

	def hasPreviousRows(self):
		'''
		Returns true if the previous set of rows is available to load, false otherwise
		'''
		return self.rowOffset > 0

	def hasPreviousColumns(self):
		'''
		Returns true if the previous set of columns is available to load, false otherwise
		'''
		return self.columnOffset > 0

	def getMappedRows(self):
		'''
		Returns a list of row indices currently mapped to the keyboard
		'''
		return self.rows[self.rowOffset:min(self.rowOffset + self.rowKeyCount, len(self.rows))]

	def getMappedColumns(self):
		'''
		Returns a list of column indices currently mapped to the keyboard
		'''
		return self.columns[self.columnOffset:min(self.columnOffset + self.columnKeyCount, len(self.columns))]

	def searchTable(self, keyword, caseSensitive, filterRows, filterColumns, onCompleteHandler):
		'''
		Search the whole table with the given keyword and log the location
		'''
		startPos = self.interceptor.selection
		if keyword != '':
			foundCells = list()
			for r in self.allRows:
				for c in self.allColumns:
					info = self.interceptor._getTableCellAt(self.tableID, startPos, r, c)
					info.expand(textInfos.UNIT_PARAGRAPH)
					text = info._get_text()
					m = re.search(re.escape(keyword), text, (re.UNICODE if caseSensitive else re.IGNORECASE))
					if m:
						foundCells.append((r, c))
					startPos = info
			log.info('logging found rows and columns')
			log.info(foundCells)
			if foundCells:
				self.searchResults = foundCells
				self.searchTerm = keyword
				self.resultIdx = 0
				self.onSearchResult = False
				self.filterRows = filterRows
				self.filterColumns = filterColumns
				onCompleteHandler(True, keyword)
				return
		onCompleteHandler(False, keyword)

	def isFiltered(self):
		return self.filterRows or self.filterColumns

	def isRowFiltered(self):
		return self.filterRows

	def isColumnFiltered(self):
		return self.filterColumns

	def checkAndApplyFilters(self):
		'''
		Checks if any of the filters are applied and set the range of explorable rows and columns accordingly
		'''
		if not self.filterRows and not self.filterColumns:
			self.rows = list(self.allRows)
			self.columns = list(self.allColumns)
		else:
			resultRows = set()
			resultColumns = set()
			if self.filterRows or self.filterColumns:
				for r, c in self.searchResults:
					resultRows.add(r)
					resultColumns.add(c)
				self.rows = sorted(list(resultRows)) if self.filterRows else list(self.allRows)
				self.columns = sorted(list(resultColumns)) if self.filterColumns else list(self.allColumns)

	def searchActive(self):
		'''
		Returns true if currently in search mode, false otherwise
		'''
		return self.searchTerm != None

	def getSearchTerm(self):
		return self.searchTerm

	def getResultIndex(self):
		'''
		Returns the current search result index that the table is last aligned to,
		None if the table has not yet align to any search result
		'''
		if not self.onSearchResult:
			return None
		return self.resultIdx + 1

	def getSearchResults(self):
		return self.searchResults

	def nextResult(self):
		'''
		Jumps to the next search result if available and triggers announcements
		'''
		if self.onSearchResult:
			self.resultIdx += 1
		if self.resultIdx < len(self.searchResults):
			self.alignTable()
			r, c = self.searchResults[self.resultIdx]
			return True
		else:
			self.resultIdx -= 1
			return False

	def prevResult(self):
		'''
		Jumps to the previous search result if available and triggers announcements
		'''
		self.resultIdx -= 1
		if self.resultIdx >= 0:
			self.alignTable()
			r, c = self.searchResults[self.resultIdx]
			return True
		else:
			self.resultIdx += 1
			return False

	def alignTable(self):
		'''
		Align the table such that the current search result is mapped to the top left
		corner of the keyboard layout
		'''
		self.onSearchResult = True
		r, c = self.searchResults[self.resultIdx]
		self.rowOffset = self.rows.index(r)
		self.columnOffset = self.columns.index(c)
		self.currRow = r
		self.currColumn = c

	def clearSearch(self):
		'''
		Clears the search state within the table
		'''
		self.searchTerm = None
		self.searchResults = None
		if self.isFiltered():
			self.expandTable()
			self.filterRows = False
			self.filterColumns = False

	def hasResultAt(self, row, column):
		'''
		Returns true if a search result is found in the given row and column, false otherwise
		'''
		return self.searchResults and (row, column) in self.searchResults

	def getCurrPosition(self):
		'''
		Returns the row, column position of the current selected cell
		'''
		return self.currRow, self.currColumn

	def getOccurrences(self):
		'''
		Calculates and returns how many more occrrences of the current search term
		is found in the current row and column as (num in row, num in column)
		Note: this excludes the current cell if the search term is found
		'''
		numInRow = 0
		numInColumn = 0
		for (r, c) in self.searchResults:
			if r == self.currRow:
				numInRow += 1
			if c == self.currColumn:
				numInColumn += 1
		if (self.currRow, self.currColumn) in self.searchResults:
			numInRow -= 1
			numInColumn -= 1
		return (numInRow, numInColumn)

	def getRow(self, keyIdx):
		'''
		Returns the actual row index corresponds with the given key index, taking
		into account the row offset.
		'''
		index = self.rowOffset + keyIdx
		if index >= len(self.rows):
			return None
		return self.rows[self.rowOffset + keyIdx]

	def getColumn(self, keyIdx):
		'''
		Returns the actual column index corresponds with the given key index, taking
		into account the column offset.
		'''
		index = self.columnOffset + keyIdx
		if index >= len(self.columns):
			return None
		return self.columns[self.columnOffset + keyIdx]