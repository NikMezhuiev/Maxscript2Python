import os
import re
from typing import List, Set, Dict
from data import WORD_CHARS

from typing_extensions import Tuple


def read_existing_names(file_path: str) -> list[str]:
	with open(file_path, 'r', encoding='utf-8') as file:
		names = [line.strip() for line in file.readlines()]
	return names


def extract_function_names(file_path: str) -> list[str]:
	with open(file_path, 'r', encoding='utf-8') as file:
		content = file.read()
	return re.findall(r'def\s+(\w+)\s*\(', content)


def write_function_names_to_file(function_names: list[str], output_file: str) -> None:
	with open(output_file, 'w', encoding='utf-8') as file:
		for name in function_names:
			file.write(name + '\n')


def extract_names():
	file_path = r"G:\My Drive\Programming\Python Qt\stubs\pymxs\runtime\__init__.pyi"
	existing_file = "C:\\Users\\" + os.getlogin() + "\\Documents\\M2P\\maxscript_functions.txt"
	
	existing_names = read_existing_names(existing_file)
	extracted_names = extract_function_names(file_path)
	
	extracted_names = [name for name in extracted_names if not name.startswith('_')]
	extracted_names_lowered = [name.lower() for name in extracted_names]
	existing_names = [existing_name for existing_name in existing_names if existing_name not in extracted_names_lowered]
	existing_names = existing_names + extracted_names
	names = sorted(set(existing_names))
	
	write_function_names_to_file(names, existing_file)


def process_by_line(text: str, replace_starts: List[Tuple[str]], replace_ends: List[Tuple[str]]) -> str:
	lines = text.split('\n')
	filtered_lines = []
	
	for line in lines:
		
		if '--' in line:
			quotes = 0
			for index, char in enumerate(line):
				if char == '\'':	quotes += 1
				elif char == '-' and line[index+1] == '-':	break
			if quotes % 2 == 0: line = line.split('--')[0]
		
		strip = line.strip()
		to_remove = False
		if strip.startswith('--'):			to_remove = True
		
		for old, new in replace_starts:
			if strip.startswith(old):	line = line.replace(old, new)
		
		for old, new in replace_ends:
			if strip.endswith(old):		line = line.replace(old, new)
		
		strip = line.strip()
		
		if not to_remove and strip in ['(', ')', '),', '],', ']']:	to_remove = True
		
		if not to_remove:
			filtered_lines.append(line)
			
	text = '\n'.join(filtered_lines)
	return replace_tags(text)


def split_to_blocks(text: str) -> List[List[str]]:
	blocks = []

	for row in text.split('\n'):
		block_row = []
		i = 0
		while i < len(row):
			
			if row[i] in WORD_CHARS:
				start = i
				while i < len(row) and row[i] in WORD_CHARS:	i += 1
				block_row.append(row[start:i])
				
			elif row[i] in '\'\"':
				quote_char = row[i]
				i += 1
				start = i
				while i < len(row) and not (row[i] == quote_char and row[i-1] != '\\'):
					i += 1
				block_row.append(row[start-1:i+1])
				i += 1
			
			else:
				block_row.append(row[i])
				i += 1
				
		blocks.append(block_row)
	
	return blocks


def is_word(text: str) -> bool:
	for char in text:
		if char not in WORD_CHARS:
			return False
	return True


def is_string(text: str) -> bool:
	return '\'' in text

	
def replace_blocks(blocks: List[List[str]], user_functions: Set, max_functions: Set) -> List[List[str]]:

	for row in blocks:
		i = 0
		while i < len(row) - 1:
			if row[i] in user_functions | max_functions and i < len(row) - 2 and row[i + 1] == ' ' and row[i + 2] != '(':
				row[i + 1] = '('
				i += 2
				started = False
				cont = True
				while i < len(row) and cont:
					
					if is_word(row[i]):     # Skip word
						started = True
						i += 1
						continue
					
					if is_string(row[i]):   # Skip string
						started = True
						i += 1
						continue
					
					if row[i] == '(':       # Skip brackets
						started = True
						i += 1
						
						nested_brackets = 1
						while i < len(row) and nested_brackets > 0:
							if row[i] == '(':	nested_brackets += 1
							elif row[i] == ')':	nested_brackets -= 1
							i += 1
						
						continue
					
					if row[i] == ' ' and row[i-1] != ',':    # Add comma
						if i < len(row) - 1 and (is_word(row[i + 1]) or is_string(row[i + 1]) or row[i + 1] == '('):
							row.insert(i, ',')
							started = True
							i += 1
							continue
					
					if row[i] in ',:;)!><+-*/%':
						cont = False
						continue
					
					if row[i] == '=' and i < len(row) - 1 and row[i+1] == '=':
						cont = False
						continue

					i += 1

				if started:
					if i == len(row):	row.append(')')
					else:			row.insert(i, ')')

			else: i += 1
	return blocks


def merge_spaces(text: str) -> str:
	return re.sub(r' +', ' ', text)


def trim_right_spaces(text: str) -> str:
	return re.sub(r' +\n', '\n', text)


def merge_blocks(blocks: List[List[str]]) -> str:
	result = ''
	
	for row in blocks:
		for char in row:
			result = result + char
		result += '\n'
	
	return result


def extract_words(input_string: str) -> Set[str]:
	return set(re.findall(r'\b\w+\b', input_string))


def replace_variables(text: str, found_words: Set, variables: Dict) -> str:
	def replace_words(input_string: str, target_word: str, replacement_word: str) -> str:
		return re.sub(r'\b' + re.escape(target_word) + r'\b', replacement_word, input_string)
	
	for word in found_words:
		if word.lower() in variables:
			text = replace_words(text, word, variables[word.lower()])
	return text


def count_to_len(input_string: str) -> str:		return re.sub(r'(\w+)\.count',			r'len(\1)',	input_string)
def replace_colon(input_string: str) -> str:	return re.sub(r'(?<=\w):',				'=',			input_string)


def replace_as_type(input_string: str) -> str:
	conversion_map = {
		" as String": "str",
		" as Integer": "int",
		" as Float": "float",
		" as Boolean": "bool",
		" as string": "str",
		" as integer": "int",
		" as float": "float",
		" as boolean": "bool"
	}

	for maxscript_type, python_type in conversion_map.items():
		input_string = re.sub(r'(\w+)' + re.escape(maxscript_type), python_type + r'(\1)', input_string)
	return input_string


def remove_redundant_parentheses(code):
	def remove_outer_parentheses(expr):
		while re.fullmatch(r'\(([^()]+)\)', expr):
			expr = expr[1:-1]
		return expr

	def remove_redundant_from_expr(expr):
		return re.sub(r'\(([^()]+)\)', lambda m: remove_outer_parentheses(m.group(0)), expr)

	pattern = re.compile(r'\(([^()]+)\)')
	while pattern.search(code):
		code = pattern.sub(lambda m: remove_redundant_from_expr(m.group(0)), code)

	return code


def replace_tags(text: str) -> str:
	def replacement(match: re.Match) -> str:
		return f"rt.Name('{match.group(1)}')"
		
	return re.sub(r'#(\b\w+)', replacement, text)


def convert_arrays(text: str) -> str:
	opened = 0
	skip = 0
	
	i = 0
	while i < (len(text) - 1):
		if text[i] == '#' and text[i+1] == '(':
			opened += 1
			i += 2
			continue
		if text[i] == '(':
			skip += 1
			i += 1
			continue
		if text[i] == ')':
			if skip > 0:
				skip -= 1
				i += 1
				continue
			else:
				text = text[:i] + ']' + text[i+1:]
		i += 1
	
	return text


def find_this_functions(text: str) -> Set[str]:
	functions = re.findall(r'fn\s+(\w+)', text)
	functions += re.findall(r'function\s+(\w+)', text)
	return set(functions)