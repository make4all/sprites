import api
from core import callLater
import wx
import wx.html as html
from gui import guiHelper, SettingsPanel
import config
import os
import webbrowser
from .firstUseMessage import firstUseMessage


class SpritesSettingsPanel(SettingsPanel):

	title = 'Sprites'

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		label = 'Open log file directory'
		feedbackInstructionLabel = 'To submit feedback or report a bug, you can submit a GitHub issue by pressing the button below:'
		self.feedbackInstruction = sHelper.addItem(wx.StaticText(self, label=feedbackInstructionLabel))
		self.submitFeedbackButton = sHelper.addItem(wx.Button(self, label='Submit Feedback'))
		self.submitFeedbackButton.Bind(wx.EVT_BUTTON, self.onSubmitFeedback)
		self.openLogFileButton = sHelper.addItem(wx.Button(self, label=label))
		self.openLogFileButton.Bind(wx.EVT_BUTTON, self.onOpenLogFileDir)
		self.openTutorialButton = sHelper.addItem(wx.Button(self, label='Open Tutorial'))
		self.openTutorialButton.Bind(wx.EVT_BUTTON, self.onOpenTutorial)

	def onOpenLogFileDir(self, evt):
		path = config.conf['sprites']['logPath']
		os.startfile(path)
	
	def onOpenTutorial(self, evt):
		webbrowser.open('https://make4all.github.io/sprites/tutorial/tutorial.html')

	def onSubmitFeedback(self, evt):
		webbrowser.open('https://github.com/make4all/sprites/issues/new?assignees=venkateshpotluri%2C+LuckyQXW&labels=bug&template=bug_report.md&title=%5Bbug%5D%3A+sprites+does+not+%3Cconcise+title+here%3E')

	def onSave(self):
		pass


class SearchDialog(wx.Dialog):
	'''
	The GUI for the sprites search dialog
	'''
	def __init__(self, parent, addOn, keyword=''):
		super().__init__(parent, title=_('SPRITEs Search'))
		self.addOn = addOn
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		findLabelText = _('Enter a search term:')
		self.findTextField = sHelper.addLabeledControl(findLabelText, wx.TextCtrl, value=keyword)

		self.caseCheckBox = wx.CheckBox(self, wx.ID_ANY, label=_('Case Sensitive'))
		sHelper.addItem(self.caseCheckBox)

		self.advancedCheckBox = wx.CheckBox(self, wx.ID_ANY, label=_('Advanced'))
		sHelper.addItem(self.advancedCheckBox)
		# Bind advanced toggle actions
		self.advancedCheckBox.Bind(wx.EVT_CHECKBOX, self.onEnableAdvanced)

		self.filterRowCheckBox = wx.CheckBox(self, wx.ID_ANY, label=_('Filter to relevant rows'))
		self.filterColumnCheckBox = wx.CheckBox(self, wx.ID_ANY, label=_('Filter to relevant columns'))
		self.filterRowCheckBox.Enable(False)
		self.filterColumnCheckBox.Enable(False)
		sHelper.addItem(self.filterRowCheckBox)
		sHelper.addItem(self.filterColumnCheckBox)

		btnHelper = guiHelper.ButtonHelper(orientation=wx.VERTICAL)
		self.searchBtn = btnHelper.addButton(self, label=_('Search'))
		self.searchBtn.Bind(wx.EVT_BUTTON, self.onSearch)
		self.cancelBtn = btnHelper.addButton(self, wx.ID_CLOSE, label=_('Cancel'))
		self.cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)
		self.clearBtn = btnHelper.addButton(self, label=_('Clear Search'))
		self.clearBtn.Bind(wx.EVT_BUTTON, self.onClear)

		self.EscapeId = wx.ID_CLOSE
		sHelper.addDialogDismissButtons(btnHelper)
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.CentreOnScreen()
		self.findTextField.SetFocus()

	def onEnableAdvanced(self, event):
		'''
		Toggle states of the filter check box depending on the state of the
		advanced checkbox
		'''
		api.processPendingEvents()
		self.filterRowCheckBox.Enable(event.IsChecked())
		self.filterColumnCheckBox.Enable(event.IsChecked())

	def onSearch(self, event):
		'''
		Initiates a search with the given term in the text field and settings
		'''
		text = self.findTextField.GetValue()
		caseSensitive = self.caseCheckBox.GetValue()
		filterRows = self.advancedCheckBox.GetValue() and self.filterRowCheckBox.GetValue()
		filterColumns = self.advancedCheckBox.GetValue() and self.filterColumnCheckBox.GetValue()
		# TODO: pass these values after figuring out shrink table
		callLater(100, self.addOn.onSearch, text, caseSensitive, filterRows, filterColumns)
		self.Destroy()

	def onCancel(self, event):
		self.Destroy()

	def onClear(self, event):
		callLater(100, self.addOn.clearSearch)
		self.Destroy()


class SearchResultDialog(wx.Dialog):
	'''
	The GUI for displaying search result, shows search occurrence and option
	to skip to first result
	'''
	def __init__(self, parent, addOn, ocurrences, isFiltered):
		super().__init__(parent, title=_('Search results'))
		self.addOn = addOn
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.resultCheckBox = wx.CheckBox(self, wx.ID_ANY, label=_('Jump to the first search result'))
		sHelper.addItem(self.resultCheckBox)
		resultLabel = wx.StaticText(self, label=f'{ocurrences} occurrences found')
		sHelper.addItem(resultLabel)
		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK))
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
		self.EscapeId = wx.ID_OK
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.CentreOnScreen()
		self.resultCheckBox.SetValue(True)
		if not isFiltered:
			self.resultCheckBox.SetFocus()
		else:
			self.resultCheckBox.Enable(False)

	def onOk(self, event):
		callLater(100, self.addOn.onJump, self.resultCheckBox.GetValue())
		self.Destroy()


class FirstUseMessageDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent, title=_('SPRITEs initial screen with info about logging'))
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		self.html = html.HtmlWindow(self)
		self.html.setPage(firstUseMessage)
		self.SetSizer(mainSizer)
		mainSizer.Add(self.html, 1, wx.ALL|wx.EXPAND, 0)
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
		self.EscapeId = wx.ID_OK
		mainSizer.Fit(self)
		self.CentreOnScreen()

	def onOk(self, event):
		self.Destroy()