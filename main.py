import json
import sys
import traceback

from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QTextOption, QTextCursor, \
	QTextBlockFormat, QCursor
from PySide6.QtWidgets import QApplication, QTextEdit, QSplitter, QMainWindow, QMenu

from classes import *
from data import *
from functions import split_to_blocks, replace_blocks, extract_words, replace_colon, merge_spaces, trim_right_spaces, convert_arrays, count_to_len, replace_as_type, replace_variables, merge_blocks, process_by_line, find_this_functions

r = 1
app: QApplication | None = None
to_print = True

initial_text2 = ''
initial_text = ''


def process_code(text: str) -> str:
	this_functions = find_this_functions(text)
	
	found_words = extract_words(text)
	rebuild_variables()

	text = replace_colon(text)

	for key, value in C_DICT.items():
		text = text.replace(key, value)

	text = process_by_line(text, REPLACE_STARTS, REPLACE_ENDS)

	for old, new in REPLACE_ALL:
		text = text.replace(old, new)
		
	text = convert_arrays(text)
	text = count_to_len(text)
	text = replace_as_type(text)

	for word in max_functions:
		text = re.sub(r'\b' + re.escape(word) + r'\b', 'rt.'+word, text)

	text = replace_variables(text, found_words, variables)
	
	text = merge_spaces(text)
	text = trim_right_spaces(text)
	
	blocks = split_to_blocks(text)
	blocks = replace_blocks(blocks, user_functions.union(this_functions), max_functions)
	text = merge_blocks(blocks)
	return text


class PythonHighlighter(QSyntaxHighlighter):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.active = True
	
		self.stringFormat	= QTextCharFormat();	self.stringFormat.setForeground(green)
		self.commentFormat	= QTextCharFormat();	self.commentFormat.setForeground(gray)
		self.functionFormat	= QTextCharFormat();	self.functionFormat.setForeground(blue)
		self.numberFormat	= QTextCharFormat();	self.numberFormat.setForeground(cyan)
		
		self.keywords_red = ['self']
		self.keywords_orange = {
			'def', 'class', 'for', 'while', 'if', 'elif', 'else', 'try', 'except', 'finally', 'with', 'in', 'as', 'is', 'and', 'or',
			'not', 'from', 'import', 'return', 'break', 'continue', 'pass', 'lambda', 'global', 'del', 'True', 'False', 'None'
		}
		self.keywords_pink = ['__init__']
		self.keywords_purple = {'super', 'int', 'float', 'bool', 'str', 'list', 'set', 'open', 'print', 'len', 'range', 'type', 'tuple', 'dict'}
		
		self.rules = []
		
		function_pattern = QRegularExpression(r'^\s*def\s+(\w+)')
		self.rules.append((function_pattern, self.functionFormat))
		
		self.add_rule_by_keywords(self.keywords_red,		red)
		self.add_rule_by_keywords(PY_KEYWORDS, 			orange)
		self.add_rule_by_keywords(self.keywords_pink,		pink)
		self.add_rule_by_keywords(self.keywords_purple,	purple)
		self.add_rule_by_keywords(max_functions,			blue)
		self.add_rule_by_keywords(py_variables,			jade)
		
		excluded_keywords = '|'.join(list(PY_KEYWORDS) + self.keywords_pink)
		function_call_pattern = QRegularExpression(r'\b(?<!def\s)(?!(' + excluded_keywords + r')\b)(\w+)\s*(?=\()')
		self.rules.append((function_call_pattern, self.functionFormat))
		
		number_pattern = QRegularExpression(r'\b\d+\b')
		self.rules.append((number_pattern, self.numberFormat))
		
		# string_pattern_single = QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
		# string_pattern_double = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"')
		
		string_pattern_single = QRegularExpression(r"'([^'\\]*(\\.[^'\\]*)*|\\\")*'")
		string_pattern_double = QRegularExpression(r'"([^"\\]*(\\.[^"\\]*)*|\\\')*"')

		self.rules.append((string_pattern_single, self.stringFormat))
		self.rules.append((string_pattern_double, self.stringFormat))
		
		self.rules.append((QRegularExpression(r'(?<!["\'])\b#.*'), self.commentFormat))
		
	def add_rule_by_keywords(self, keywords, color):
		if not self.active: return
		keyword_format = QTextCharFormat()
		keyword_format.setForeground(color)
		
		for keyword in keywords:
			pattern = f'\\b{keyword}\\b'
			rule = (QRegularExpression(pattern), keyword_format)
			self.rules.append(rule)
	
	def highlightBlock(self, text):
		if not self.active: return
		for pattern, t_format in self.rules:
			expression = QRegularExpression(pattern)
			match_iterator = expression.globalMatch(text)
			while match_iterator.hasNext():
				match = match_iterator.next()
				start = match.capturedStart()
				length = match.capturedLength()
				if t_format == self.functionFormat and self.isKeyword(start):
					continue
				self.setFormat(start, length, t_format)
		
		function_name_pattern = QRegularExpression(r'\bdef\s+(\w+)\s*(?=\()')
		match_iterator = function_name_pattern.globalMatch(text)
		while match_iterator.hasNext():
			match = match_iterator.next()
			start = match.capturedStart(1)
			length = match.capturedLength(1)
			self.setFormat(start, length, self.functionFormat)

	def isKeyword(self, start):
		return self.format(start).foreground() in [orange, pink]


class MaxScriptHighlighter(QSyntaxHighlighter):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.active = True
		
		self.stringFormat = QTextCharFormat()
		self.stringFormat.setForeground(green)

		self.commentFormat = QTextCharFormat()
		self.commentFormat.setForeground(gray)
		
		self.keywords_orange = {
			'struct', 'case', 'of', 'function', ' fn ', 'rollout', 'for', 'while', 'if', 'else', 'try', 'catch', 'finally', 'with', 'in',
			'as', 'is', 'and', 'AND', 'or', 'OR', 'do', 'to', 'not', 'from', 'import', 'return', 'break', 'continue', 'pass', 'exit', 'lambda', 'global',
			'local', 'persistent', 'del', 'true', 'false', 'then', 'on', 'open', '\tfn '
		}
		
		self.keywords_purple = {'super', 'int', 'float', 'bool', 'str', 'string', 'list', 'undefined'}
		
		self.rules = []
		
		self.functionFormat = QTextCharFormat()
		self.functionFormat.setForeground(blue)
		
		self.add_rule_by_keywords(self.keywords_orange,	orange)
		self.add_rule_by_keywords(self.keywords_purple,	purple)
		self.add_rule_by_keywords(max_functions, blue)
		self.add_rule_by_keywords(user_functions, blue)
		self.add_rule_by_keywords(ms_variables, jade)

		self.rules.append((QRegularExpression('".*"'), self.stringFormat))
		self.rules.append((QRegularExpression("'.*'"), self.stringFormat))

		self.triSingleQuoteFormat = QTextCharFormat(self.stringFormat)
		self.triDoubleQuoteFormat = QTextCharFormat(self.stringFormat)
		self.rules.append((QRegularExpression("'''(.*?)'''", QRegularExpression.DotMatchesEverythingOption), self.triSingleQuoteFormat))
		self.rules.append((QRegularExpression('"""(.*?)"""', QRegularExpression.DotMatchesEverythingOption), self.triDoubleQuoteFormat))

		self.rules.append((QRegularExpression(r'--.*'), self.commentFormat))
		
		self.functionFormat = QTextCharFormat()
		self.functionFormat.setForeground(blue)
		
		self.number_format = QTextCharFormat()
		self.number_format.setForeground(cyan)
		
		function_pattern = QRegularExpression(r'\bfunction\b\s+(\w+)\s*(?=\()')
		self.rules.append((function_pattern, self.functionFormat))
		
		number_pattern = QRegularExpression(r'\b\d+\b')
		self.rules.append((number_pattern, self.number_format))
	
	def add_rule_by_keywords(self, keywords, color, bold=False):
		if not self.active: return
		keyword_format = QTextCharFormat()
		keyword_format.setForeground(color)
		if bold:
			keyword_format.setFontWeight(QFont.Bold)
		
		for keyword in keywords:
			pattern = f'\\b{keyword}\\b'
			rule = (QRegularExpression(pattern), keyword_format)
			self.rules.append(rule)
	
	def highlightBlock(self, text):
		if not self.active: return
		for pattern, t_format in self.rules:
			expression = QRegularExpression(pattern)
			match_iterator = expression.globalMatch(text)
			while match_iterator.hasNext():
				match = match_iterator.next()
				# if format == self.functionFormat:
				# 	self.setFormat(match.capturedStart(1), match.capturedLength(1), t_format)
				# else:
				self.setFormat(match.capturedStart(), match.capturedLength(), t_format)
				
	def refresh_function_keywords(self, new_keywords):
		if not self.active: return
		self.add_rule_by_keywords(new_keywords, blue)


class PlainTextEditor(QTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setTabWidth(32)
		self.setWordWrapMode(QTextOption.NoWrap)

	def insertFromMimeData(self, source):
		if source.hasText():
			self.insertPlainText(source.text())
		else:
			super().insertFromMimeData(source)

	def setTabWidth(self, width):
		# fm = QFontMetricsF(self.font())
		# space_width = fm.horizontalAdvance(' ')
		self.setTabStopDistance(width)
		
	def setLineSpacing(self, height):
		cursor = QTextCursor(self.document())
		block_format = QTextBlockFormat()
		block_format.setLineHeight(height, 1)  # Using FixedHeight type
		cursor.select(QTextCursor.Document)
		cursor.mergeBlockFormat(block_format)
	

class MaxScript2Python(QMainWindow):
	def __init__(self):
		super().__init__()
		
		self.setStyleSheet('''QWidget { background-color: rgb(60, 60, 60);}''')
		
		self.edt_input = PlainTextEditor(self)
		self.edt_input.setStyleSheet(text_editor_style + scr_stylesheet)
		self.edt_input.setContextMenuPolicy(Qt.CustomContextMenu)
		self.edt_input.customContextMenuRequested.connect(self.popup_input)
		self.ms_highlighter = MaxScriptHighlighter(self.edt_input.document())
		
		
		self.edt_output = PlainTextEditor(self)
		self.edt_output.setStyleSheet(text_editor_style + scr_stylesheet)
		self.edt_output.setContextMenuPolicy(Qt.CustomContextMenu)
		self.edt_output.customContextMenuRequested.connect(self.popup_output)
		self.py_highlighter = PythonHighlighter(self.edt_output.document())
		
		self.edt_input.textChanged.connect(self.convert_to_python)
		
		# self.edt_list =
		
		q_splitter = QSplitter()
		q_splitter.setHandleWidth(20)
		q_splitter.addWidget(self.edt_input)
		q_splitter.addWidget(self.edt_output)
		q_splitter.setContentsMargins(10, 14, 10, 14)
		
		self.setCentralWidget(q_splitter)
		
		self.setWindowTitle('MaxScript to Python converter')
		self.setAttribute(Qt.WA_DeleteOnClose)  # noqa
		
	def closeEvent(self, event):
		with open('C:\\Users\\'+username+'\\Documents\\M2P\\last_text.txt', 'w') as file:
			file.write(self.edt_input.toPlainText())
		event.accept()
		
		data = {
			'x': self.x(),
			'y': self.y(),
			'width': self.width(),
			'height': self.height(),
		}
		with open('C:\\Users\\'+username+'\\Documents\\M2P\\window.json', 'w') as file:
			json.dump(data, file)
		event.accept()
	
	def restore_state(self):
		if os.path.exists('C:\\Users\\'+username+'\\Documents\\M2P\\window.json'):
			with open('C:\\Users\\'+username+'\\Documents\\M2P\\window.json', 'r') as file:
				data = json.load(file)
				self.move(max(data['x'], 0), max(data['y'], 0))
				width, height = data['width'], data['height']
				size = app.primaryScreen().size()
				s_width, s_height = size.width(), size.height()
				if width == s_width or height == s_height:
					self.resize(1500*r, 800*r)
					self.showMaximized()
				else:
					self.resize(width, height)
		else:
			self.resize(1500*r, 800*r)
		
		if os.path.exists('C:\\Users\\'+username+'\\Documents\\M2P\\last_text.txt'):
			with open('C:\\Users\\'+username+'\\Documents\\M2P\\last_text.txt', 'r') as file:
				initial_text = file.read()
			self.edt_input.setText(initial_text)
		
	def convert_to_python(self) -> None:
		QApplication.processEvents()
		self.edt_input.blockSignals(True)
		self.edt_input.setLineSpacing(120.0)
		self.py_highlighter.active = True
		
		text = self.edt_input.toPlainText()
		
		# text = process_code(text)
		
		text = remove_comments_from_string(text)
		tokens = tokenize(text)
		
		
		#replace sequences of tokens
		for sequence in LIGATURES:
			tokens = merge_sequence(tokens, sequence)
		
		
		#remove multiline comments
		index = 0
		while index < len(tokens):
			if tokens[index] == '/*':
				end = index
				while end < len(tokens) and tokens[end] != '*/': end += 1
				tokens[index:end+1] = []

			index += 1
		
		
		#remove single tokens
		tokens = [token for token in tokens if token not in ['local', 'global', 'persistent', '::']]
		
		
		#replace single tokens
		for token in tokens:
			l_token = token.lower()
			if l_token in SINGLE_REPLACEMENTS:
				index = tokens.index(token)
				tokens[index] = SINGLE_REPLACEMENTS[l_token]

		
		# tokens = process_dots(tokens)
		
		
		try:
			text = parse_tokens(tokens)
		except Exception as e:
			self.py_highlighter.active = False
			text = str(e) + traceback.format_exc()
		
		self.edt_output.setText(text)
		self.edt_output.setLineSpacing(120.0)
		self.edt_input.blockSignals(False)
		
	def popup_menu(self, widget) -> None:
		
		def mark_as(words, function, text) -> None:
			if text and text not in words:
				function(text)
				if widget == self.edt_output:
					scroll = widget.verticalScrollBar().value()
					self.update_highlighter()
					widget.verticalScrollBar().setValue(scroll)
				else:
					self.update_highlighter()
				
				self.convert_to_python()
		
		selected = widget.textCursor().selectedText().lower()
		ct = QMenu(self)
		ct.setStyleSheet(qmenu_style)
		
		actions = {
			'Mark as MS function':		(max_functions,		add_max_function_to_file),
			'Mark as variable':			(variables,			add_variable_to_file),
			'Mark as custom function':	(user_functions,	add_custom_function_to_file),
			'Mark as custom variable':	(user_variables,	add_custom_variable_to_file)
		}
		
		if selected:
			for text, (words, func) in actions.items():
				if 'variable' in text:
					ct.addSeparator()
				ct.addAction(text, lambda w=words, f=func: mark_as(w, f, selected))
		ct.exec(QCursor.pos())
		self.setDisabled(False)
	
	def popup_input(self) -> None:	self.popup_menu(self.edt_input)
	def popup_output(self) -> None:	self.popup_menu(self.edt_output)
	
	def update_highlighter(self) -> None:
		self.ms_highlighter.add_rule_by_keywords(max_functions,	blue)
		self.ms_highlighter.add_rule_by_keywords(user_functions,	blue)
		self.ms_highlighter.add_rule_by_keywords(user_variables,	jade)
		self.ms_highlighter.rehighlight()
		self.py_highlighter.add_rule_by_keywords(max_functions,	blue)
		self.py_highlighter.add_rule_by_keywords(user_functions,	blue)
		self.py_highlighter.add_rule_by_keywords(user_variables,	jade)
		self.py_highlighter.rehighlight()
		self.edt_input.repaint()
		self.edt_output.repaint()
	

def main():
	global r, app
	
	app = QApplication(sys.argv)
	
	r = app.primaryScreen().logicalDotsPerInch() / 96.0
	
	m2p = MaxScript2Python()
	m2p.show()
	m2p.restore_state()
	
	sys.exit(app.exec())


if __name__ == '__main__': main()
