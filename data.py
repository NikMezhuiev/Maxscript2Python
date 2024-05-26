import os

from PySide6.QtWidgets import QInputDialog, QWidget
from typing_extensions import Set, Dict, cast

from PySide6.QtGui import QColor

import wordsegment as ws  # type: ignore


# region STYLES
text_editor_style = '''	QTextEdit {
							border: 1px solid rgb(160, 160, 160);
							background-color: rgb(0, 0, 0);
							font: 13px "Fira Code";
							font-weight: 'Regular';
							color: rgb(188, 190, 196);
						}
						QTextEdit:focus {
							border: 1px solid rgb(160, 160, 160);
							background-color: rgb(0, 0, 0);
							font: 13px "Fira Code";
							font-weight: 'Regular';
							color: rgb(188, 190, 196);
						}
}'''

scr_stylesheet = """
			QScrollBar {
				background: #383838;
			}
		
			QScrollBar:vertical {
				border: 1px #383838;
				border-radius: 4px;
				background: #383838;
				width: 8px;
				margin: 0px 0 0px 0;  /* top, right, bottom, left */
			}
		
			QScrollBar::handle:vertical {
				border-radius: 3px;
				background: #383838;
				background: #525252;
				min-height: 30px;
			}
		
			QScrollBar::add-line:vertical {
				border: 2px solid grey;
				background: #383838;
				height: 15px;
				subcontrol-position: bottom;
				subcontrol-origin: margin;
			}
		
			QScrollBar::sub-line:vertical {
				border: 2px solid grey;
				background: #383838;
				height: 15px;
				subcontrol-position: top;
				subcontrol-origin: margin;
			}
		
			QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
				border: 2px solid grey;
				width: 3px;
				height: 3px;
				background: #383838;
			}
		
			QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
				background: #383838;
			}
			
			
			
			
			QScrollBar:horizontal {
				border: 1px #383838;
				border-radius: 4px;
				background: #383838;
				height: 10px;
				margin: 0px 0px 0px 0px;  /* top, right, bottom, left */
			}
		
			QScrollBar::handle:horizontal {
				border-radius: 3px;
				background: rgb(130, 130, 130);
				min-width: 30px;
			}
		
			QScrollBar::add-line:horizontal {
				border: 2px solid grey;
				background: #383838;
				width: 15px;
				subcontrol-position: bottom;
				subcontrol-origin: margin;
			}
		
			QScrollBar::sub-line:horizontal {
				border: 2px solid grey;
				background: #383838;
				width: 15px;
				subcontrol-position: top;
				subcontrol-origin: margin;
			}
		
			QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {
				border: 2px solid grey;
				width: 3px;
				height: 3px;
				background: #383838;
			}
		
			QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
				background: #383838;
			}
"""

qmenu_style = '''
			QMenu {
			    color: rgb(188, 190, 196);
			    background-color: rgb(60, 60, 60);
			}
			
			QMenu::item:selected {
			    color: rgb(255, 255, 255);
			    background-color: rgb(80, 80, 80);
			}
'''
# endregion


# region COLORS

red		= QColor(255,	105,	105)
orange	= QColor(207, 	142,	109)
pink	= QColor(178,	0,		178)
purple	= QColor(136, 	136,	198)
blue	= QColor(118,	167,	255)
green	= QColor(106, 	171,	115)
jade	= QColor(80, 	210,	42)
cyan	= QColor(42, 	172,	184)
gray	= QColor(80, 	80,		80)

# endregion


username = os.getlogin()

M2P_FOLDER		= 'C:\\Users\\'+username+'\\Documents\\M2P\\'
MAX_FUN_PATH	= M2P_FOLDER + 'maxscript_functions.txt'
VARIABLES_PATH	= M2P_FOLDER + 'variables.txt'
DICTIONARY_PATH	= M2P_FOLDER + 'dictionary.txt'
CUSTOM_FUN_PATH	= M2P_FOLDER + 'custom_functions.txt'
CUSTOM_VAR_PATH	= M2P_FOLDER + 'custom_variables.txt'


def read_words_from_file(path: str) -> Set[str]:
	words: Set = set()
	if os.path.exists(path):
		with open(path, 'r') as file:
			words = set(file.readlines())
		words = {word.strip() for word in words}
	
	return words


def words_to_dict(words: Set) -> Dict[str, str]:
	result = {}
	for word in words:
		key, target = word.split('=')
		result[key] = target
	return result


def rebuild_variables() -> None:
	
	global variables, ms_variables, py_variables
	ms_variables, py_variables = variables.keys(), variables.values()
	ms_variables = {word for word in ms_variables if word.lower() in variables}


def add_word_to_file(word: str, var: Set[str], path: str) -> None:
	if word not in var:
		var.add(word)
	if not os.path.exists(path):
		os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, 'w') as file:
		for function in var:
			file.write(function + '\n')


def add_max_function_to_file(word: str) -> None:	add_word_to_file(word,	max_functions,	MAX_FUN_PATH)
def add_custom_function_to_file(word: str) -> None:	add_word_to_file(word,	user_functions,	CUSTOM_FUN_PATH)
def add_custom_variable_to_file(word: str) -> None:	add_word_to_file(word,	user_variables,	CUSTOM_VAR_PATH)


def add_variable_to_file(old_var: str) -> None:
	
	def to_snake_case(text: str) -> str:
		ws.load()
		words = ws.segment(text)
		return '_'.join(words)

	lower = old_var.lower()
	new_var = to_snake_case(lower)
	
	new_var, ok = QInputDialog.getText(cast(QWidget, None), "Input Dialog", "Enter your text:", text=new_var)
	
	variables[lower] = new_var
	with open(VARIABLES_PATH, 'w') as file:
		for key, value in variables.items():
			file.write(f'{key}={value}\n')
			
	rebuild_variables()


ms_variables:	Set		= set()
py_variables:	Set		= set()
found_words:	Set		= set()
this_functions:	Set		= set()
max_functions:	Set		= read_words_from_file(MAX_FUN_PATH)
user_functions:	Set		= read_words_from_file(CUSTOM_FUN_PATH)
user_variables:	Set		= read_words_from_file(CUSTOM_VAR_PATH)
dictionary:		Set		= read_words_from_file(DICTIONARY_PATH)
variables:		Dict	= words_to_dict(read_words_from_file(VARIABLES_PATH))

WORD_CHARS				= set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
SPECIAL_CHARS			= set(' \t()[]{}.,:;+-*/&|<>=~^\'\"\\')
PY_KEYWORDS				= {
			'def', 'class', 'for', 'while', 'if', 'elif', 'else', 'try', 'except', 'finally', 'with', 'in', 'as', 'is', 'and', 'or',
			'not', 'from', 'import', 'return', 'break', 'continue', 'pass', 'lambda', 'global', 'del', 'True', 'False', 'None'
}

C_DICT = {
	'#()':			'[]',
	'#{}':			'{}',
	'true':			'True',
	'false':		'False',
	'function ':	'def ',
	'local ':		'',
	'struct ':		'class ',
	'rollout ':		'class ',
	'!= undefined':	'is not None',
	'== undefined':	'is None',
	'!=undefined':	'is not None',
	'==undefined':	'is None',
	'==true':		'',
	'== true':		'',
	'undefined':	'None',
	'catch':		'except:',
	'try':			'try:',
	'\"':			'\''
	# ' (':			'('
}

C_DICT_WORDS = {
	'true':			'True',
	'false':		'False',
	'function':		'def',
	'struct':		'class',
	'rollout':		'class',
	'undefined':	'None',
	'catch':		'except:',
	'try':			'try:'
}

REPLACE_STARTS = [
	(') else (',	'else: '),
	(') else(',		'else: '),
	(')else(',		'else: '),
	('else (',		'else: '),
	('else(',		'else: '),
	(') else',		'else: '),
	(')else',		'else: '),
	('else ',		'else: '),
	('else',		'else: '),
	('try: (',		'try:'),
	('try:(',		'try:'),
	(')except',		'except'),
	(') except',	'except'),
	(' do',			':'),
	(' do (',		':'),
	(' do(',		':'),
	(' then',		':'),
	(' then (',		':'),
	(' then(',		':'),
	(' = (',		':'),
	(' =(',			':'),
	('=(',			':'),
	('fn ',			'def '),
	('function ',	'def '),
]

REPLACE_ENDS = [
	(' do',			':'),
	(' do (',		':'),
	(' do(',		':'),
	(' then',		':'),
	(' then (',		':'),
	(' then(',		':'),
	(':()',			': pass'),
	(': ()',		': pass'),
	(' = (',		':'),
	('= (',			':'),
	(' =(',			':'),
	('=(',			':'),
	(' =',			':'),
	('=',			':'),
]

REPLACE_ALL = [
	('#(',		'['),
	(' do ',	': '),
	(' then ',	': '),
	('  ',		' '),
	(') )',		'))'),
	('( (',		'(('),
]

OPERATORS = {'+', '-', '*', '/', '%', '^', '&', '|', '<', '>', '=', '!', '~'}


LIGATURES = {'#()', '#{}', '==', '!=', '>=', '<=', '+=', '-=', '*=', '/=', '%=', '::', '**', '//', '**=', '&=', '|=', '^=', '>>=', '<<=', ':=', '<<', '>>', '/*', '*/'}

SINGLE_REPLACEMENTS = {
	'true':			'True',
	'false':		'False',
	'undefined':	'None',
	'#()':			'[]',
	'#{}':			'rt.BitArray()',
	'unsupplied':	'rt.unsupplied',
	'ok':			'rt.OK'
}


rebuild_variables()
