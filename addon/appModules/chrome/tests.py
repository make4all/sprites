import unittest
from spritesTable import SpritesTable

class TestSpritesTable(unittest.TestCase):
	def testInit(self):
		t = SpritesTable(1, 3, 4, 5, 13, True)
		self.assertEqual(t.tableID, 1)
		self.assertEqual(t.rowCount, 3)
		self.assertEqual(t.columnCount, 4)
		self.assertEqual(t.allRows, [1, 2, 3])
		self.assertEqual(t.allColumns, [1, 2, 3, 4])
		self.assertEqual(t.rows, [1, 2, 3])
		self.assertEqual(t.columns, [1, 2, 3, 4])
		self.assertEqual(t.currRow, 1)
		self.assertEqual(t.currColumn, 1)
		self.assertEqual(t.rowOffset, 0)
		self.assertEqual(t.columnOffset, 0)
		self.assertEqual(t.rowKeyCount, 5)
		self.assertEqual(t.columnKeyCount, 13)
		self.assertIsNone(t.searchTerm)
		self.assertIsNone(t.searchResults)
		self.assertEqual(t.resultIdx, 0)
		self.assertFalse(t.onSearchResult)
		self.assertFalse(t.filterRows)
		self.assertFalse(t.filterColumns)

	def testChangeRowOffset(self):
		t = SpritesTable(1, 3, 4, 5, 13, True)
		t.changeRowOffset(2)
		self.assertEqual(t.currRow, 3)
		t.changeRowOffset(-1)
		self.assertEqual(t.currRow, 2)
		# snap to first row if delta > available rows
		t.changeRowOffset(-3)
		self.assertEqual(t.currRow, 1)
	
	def testChangeColumnOffset(self):
		t = SpritesTable(1, 3, 4, 5, 13, True)
		t.changeColumnOffset(3)
		self.assertEqual(t.currColumn, 4)
		t.changeColumnOffset(-1)
		self.assertEqual(t.currColumn, 3)
		# snap to first column if delta > available columns
		t.changeColumnOffset(-3)
		self.assertEqual(t.currColumn, 1)
	
	def testScrollRowsRegular(self):
		t = SpritesTable(1, 6, 4, 5, 13, True)
		# cannot scroll to previous at start
		self.assertFalse(t.scroll(direction=0, keyIdx=0))
		self.assertTrue(t.scroll(direction=0, keyIdx=4))
		self.assertEqual(t.currRow, 6)
		# out of rows to scroll
		self.assertFalse(t.scroll(direction=0, keyIdx=4))
		# scroll back
		self.assertTrue(t.scroll(direction=0, keyIdx=0))
		self.assertEqual(t.currRow, 1)
		self.assertFalse(t.scroll(direction=0, keyIdx=0))
	
	def testScrollRowsEdge(self):
		# test table with 10 rows
		t = SpritesTable(1, 10, 4, 5, 13, True)
		# cannot scroll to previous at start
		self.assertFalse(t.scroll(direction=0, keyIdx=0))
		self.assertTrue(t.scroll(direction=0, keyIdx=4))
		self.assertEqual(t.currRow, 6)
		# out of rows to scroll
		self.assertFalse(t.scroll(direction=0, keyIdx=4))
		# scroll back
		self.assertTrue(t.scroll(direction=0, keyIdx=0))
		self.assertEqual(t.currRow, 1)
		self.assertFalse(t.scroll(direction=0, keyIdx=0))
	
	def testScrollColumnsRegular(self):
		# assume 3 keys for navigate columns
		t = SpritesTable(1, 6, 4, 5, 3, True)
		# cannot scroll to previous at start
		self.assertFalse(t.scroll(direction=1, keyIdx=0))
		self.assertTrue(t.scroll(direction=1, keyIdx=2))
		self.assertEqual(t.currColumn, 4)
		# out of columns to scroll
		self.assertFalse(t.scroll(direction=1, keyIdx=2))
		# scroll back
		self.assertTrue(t.scroll(direction=1, keyIdx=0))
		self.assertEqual(t.currColumn, 1)
		self.assertFalse(t.scroll(direction=1, keyIdx=0))
	
	def testScrollColumnsEdge(self):
		# test table with 6 columns
		t = SpritesTable(1, 6, 6, 5, 3, True)
		# cannot scroll to previous at start
		self.assertFalse(t.scroll(direction=1, keyIdx=0))
		self.assertTrue(t.scroll(direction=1, keyIdx=2))
		self.assertEqual(t.currColumn, 4)
		# out of columns to scroll
		self.assertFalse(t.scroll(direction=1, keyIdx=2))
		# scroll back
		self.assertTrue(t.scroll(direction=1, keyIdx=0))
		self.assertEqual(t.currColumn, 1)
		self.assertFalse(t.scroll(direction=1, keyIdx=0))

	def testNextResult(self):
		t = SpritesTable(1, 4, 5, 5, 13, True)
		t.searchResults = [(1, 1), (2, 3), (3, 3), (3, 4), (3, 5)]
		# go through all results using next
		self.assertTrue(t.nextResult())
		self.assertEqual(t.getCurrPosition(), (1, 1))
		self.assertEqual(t.getMappedRows(), [1, 2, 3, 4])
		self.assertEqual(t.getMappedColumns(), [1, 2, 3, 4, 5])

		self.assertTrue(t.nextResult())
		self.assertTrue(t.nextResult())
		self.assertEqual(t.getCurrPosition(), (3, 3))
		self.assertEqual(t.getMappedRows(), [3, 4])
		self.assertEqual(t.getMappedColumns(), [3, 4, 5])
		self.assertTrue(t.nextResult())
		self.assertTrue(t.nextResult())
		# end of all results
		self.assertFalse(t.nextResult())
		self.assertEqual(t.getCurrPosition(), (3, 5))
		self.assertEqual(t.getMappedRows(), [3, 4])
		self.assertEqual(t.getMappedColumns(), [5])

	def testPrevResult(self):
		t = SpritesTable(1, 4, 5, 5, 13, True)
		t.searchResults = [(1, 1), (2, 3), (3, 3), (3, 4), (3, 5)]
		t.resultIdx = 4
		t.onSearchResult = True
		t.alignTable()
		self.assertEqual(t.getCurrPosition(), (3, 5))
		self.assertEqual(t.getMappedRows(), [3, 4])
		self.assertEqual(t.getMappedColumns(), [5])

		self.assertTrue(t.prevResult())
		self.assertEqual(t.getCurrPosition(), (3, 4))
		self.assertEqual(t.getMappedRows(), [3, 4])
		self.assertEqual(t.getMappedColumns(), [4, 5])

		self.assertTrue(t.prevResult())
		self.assertTrue(t.prevResult())
		self.assertEqual(t.getCurrPosition(), (2, 3))
		self.assertEqual(t.getMappedRows(), [2, 3, 4])
		self.assertEqual(t.getMappedColumns(), [3, 4, 5])
		self.assertTrue(t.prevResult())
		# no prev
		self.assertFalse(t.prevResult())
		self.assertEqual(t.getCurrPosition(), (1, 1))

	def testGetOccurrences(self):
		t = SpritesTable(1, 4, 5, 5, 13, True)
		t.searchResults = [(1, 1), (2, 3), (3, 3), (3, 4), (3, 5)]
		# start off at (1, 1)
		self.assertEqual(t.getOccurrences(), (0, 0))
		# at (1, 3)
		t.currRow = 3
		self.assertEqual(t.getOccurrences(), (3, 1))
		# at (3, 3)
		t.currColumn = 3
		self.assertEqual(t.getOccurrences(), (2, 1))
		# at (4, 3)
		t.currRow = 4
		self.assertEqual(t.getOccurrences(), (0, 2))
		# at (4, 2)
		t.currColumn = 2
		self.assertEqual(t.getOccurrences(), (0, 0))
	
	def testFilters(self):
		t = SpritesTable(1, 4, 5, 5, 13, True)
		t.searchResults = [(1, 1), (2, 3), (3, 3), (3, 4), (3, 5)]
		t.filterRows = True
		t.checkAndApplyFilters()
		self.assertEqual(t.rows, [1, 2, 3])
		self.assertEqual(t.columns, [1, 2, 3, 4, 5])

		t.filterColumns = True
		t.checkAndApplyFilters()
		self.assertEqual(t.rows, [1, 2, 3])
		self.assertEqual(t.columns, [1, 3, 4, 5])

		t.filterRows = False
		t.checkAndApplyFilters()
		self.assertEqual(t.rows, [1, 2, 3, 4])
		self.assertEqual(t.columns, [1, 3, 4, 5])

		t.filterColumns = False
		t.checkAndApplyFilters()
		self.assertEqual(t.rows, [1, 2, 3, 4])
		self.assertEqual(t.columns, [1, 2, 3, 4, 5])

	def testExpandTable(self):
		t = SpritesTable(1, 8, 10, 5, 4, True)
		t.searchResults = [(2, 2), (4, 7), (6, 3)]
		t.filterRows = True
		t.resultIdx = 0
		t.checkAndApplyFilters()
		t.alignTable()
		self.assertEqual(t.getMappedRows(), [2, 4, 6], t.getCurrPosition())
		self.assertEqual(t.getMappedColumns(), [2, 3, 4, 5])
		self.assertEqual(t.getCurrPosition(), (2, 2))
		t.expandTable()
		self.assertEqual(t.getMappedRows(), [2, 3, 4, 5, 6])

		t.filterRows = False
		t.filterColumns = True
		t.resultIdx = 1
		t.checkAndApplyFilters()
		t.alignTable()
		self.assertEqual(t.getMappedRows(), [4, 5, 6, 7, 8])
		self.assertEqual(t.getMappedColumns(), [7])
		self.assertEqual(t.getCurrPosition(), (4, 7))
		t.expandTable()
		self.assertEqual(t.getMappedColumns(), [7, 8, 9, 10])

		t.filterColumns = True
		t.filterRows = True
		t.resultIdx = 2
		t.checkAndApplyFilters()
		t.alignTable()
		self.assertEqual(t.getMappedRows(), [6])
		self.assertEqual(t.getMappedColumns(), [3, 7])
		self.assertEqual(t.getCurrPosition(), (6, 3))
		t.expandTable()
		self.assertEqual(t.getMappedColumns(), [3, 4, 5, 6])
		self.assertEqual(t.getMappedRows(), [6, 7, 8])


if __name__ == '__main__':
	unittest.main()