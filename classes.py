from __future__ import annotations

import math
import re
from typing_extensions import List, Any, Optional

from data import *

LOG = False


def find_matching_bracket(index: int, tokens: List[str]) -> int:
	opened = 0
	c_opened = 0
	c_closed = 0
	while index < len(tokens):
		token = tokens[index]
		if token == '(':
			opened += 1
			c_opened += 1
		elif token == ')':
			opened -= 1
			c_closed += 1
		if opened == 0:	break
		index += 1
		
	if index == len(tokens):
		index -= 1
	return index


def find_condition_end(index: int, tokens: List[str]) -> int:
	opened	= 0
	ifs		= 0
	while tokens[index] not in ['then', 'do']:
		if tokens[index] == '(':	opened += 1
		elif tokens[index] == ')':	opened -= 1
		elif tokens[index] == 'if':	ifs += 1
		elif tokens[index] in ['then', 'do']:
			if ifs > 0:	ifs -= 1
			else:
				if opened == 0:	break
		index += 1
	return index - 1


def find_then_end(index: int, tokens: List[str]) -> int:
	if tokens[index] == '\n' and tokens[index+1] != '(':  # if next 1 line
		index += 1
		while tokens[index] != '\n':	index += 1
		
	elif tokens[index+1] == '(':  # if block
		index = find_matching_bracket(index + 1, tokens)
		
	else:  # if 1 line
		index += 1
		while index < len(tokens) and tokens[index] != '\n':	index += 1
	
	return index


def process_dots(tokens: List[str]) -> List[str]:
	index = 0
	while index+1 < len(tokens):
		if tokens[index] == '.' and tokens[index-1] != ')':
			i = 2
			end = index + 1
			while index + i < len(tokens) and tokens[index + i] == '.':
				i += 2
				end = index
			
			tokens[index-1:end+1] = [''.join(tokens[index-1:end+1])]
			
			word = tokens[index - 1]
			if word.endswith('count'):
				tokens[index-1] = f'len({word[:-6]})'
				
		index += 1
	return tokens


class Piece:
	def __init__(self, name: str, parent: Optional[Piece] = None, indent: int = 0):
		self.name	= name
		self.parent = parent
		self.indent = indent


class Root(Piece):
	def __init__(self):
		super().__init__('Root')
	
	def __repr__(self):
		return f'Root'


class Variable(Piece):
	def __init__(self, name: str, value=None):
		super().__init__('Variable')
		self.name = name
		self.value = value
	
	def __repr__(self):
		return f'{self.name} =\t{self.value}'


class Statement(Piece):
	def __init__(self, parent: Piece, tokens: List[str]):
		super().__init__('Statement', parent)
		self.tokens = tokens
	
	def __repr__(self):
		text = ' '.join([str(token) for token in self.tokens])
		return text
	
	


TYPE_DICT = {
	'string':		'str',
	'stringstream':	'stringstream',
	'integer':		'int',
	'float':		'float',
	'name':			'rt.Name',
}

functions_set = user_functions | max_functions


def is_function(token: str) -> bool:
	return any(token.lower() == item.lower() for item in functions_set)


class Block(Piece):
	def __init__(self, parent: Piece, tokens: List[str], indent: int = 0, name: str = 'Block'):
		super().__init__(name, parent, indent)
		self.tokens = tokens
		
		cont = True
		while cont:
			cont = False
			while len(tokens) > 0 and tokens[0] == '\n':						tokens = tokens[1:];	cont = True
			while len(tokens) > 1 and tokens[-1] == '\n':						tokens = tokens[:-1];	cont = True
			while len(tokens) > 0 and tokens[0] == ',':							tokens = tokens[1:];	cont = True
			while len(tokens) > 1 and tokens[-1] == ',':						tokens = tokens[:-1];	cont = True

			while len(tokens) > 1 and tokens[0] == '(' and tokens[-1] == ')':	tokens = tokens[1:-1];	cont = True
		
		index = 0
		while index < len(tokens) and tokens[index] != ')':
			if tokens[index] == 'struct':
				end = find_matching_bracket(index + 1, tokens)
				tokens[index:end+1] = [Struct(self, tokens[index + 1:end])]
				
			elif tokens[index] in {'fn', 'function'}:
				start = index + 3
				while tokens[start] != '(':	start += 1
				end = find_matching_bracket(start, tokens)
				tokens[index:end+1] = [Function_def(self, tokens[index + 1:end])]
				
			elif tokens[index] == 'if':
				if_else = If_else(self, tokens, index, max(indent, 0))
				tokens[index:if_else.end+1] = [if_else]
			
			elif tokens[index] == 'try':
				try_except = Try_except(self, tokens, index, indent)
				tokens[index:try_except.end] = [try_except]
			
			elif is_function(tokens[index]) or is_function(tokens[index].split('.')[-1]):
				function_call = Function_call(self, tokens, index)
				tokens[index:function_call.end] = [function_call]
			
			elif tokens[index] == 'as' and 0 < index < len(tokens) - 1:

				if 0 < index < len(tokens) - 2 and tokens[index-2] in LIGATURES:
					tokens[index-3:index+2] = [f'{TYPE_DICT[tokens[index+1].lower()]}({tokens[index-3: index-1]})']
				else:
					tokens[index-1:index+2] = [f'{TYPE_DICT[tokens[index+1].lower()]}({tokens[index-1]})']
			
			elif tokens[index] == '[':
				array_call = Array_call(self, tokens, index)
				tokens[index-1:array_call.end] = [array_call]
				index -= 1
			
			elif tokens[index] == '#':
				if tokens[index+1] == '(':
					array = Array(self, tokens, index)
					tokens[index:array.end] = [array]
				else:
					tokens[index:index+2] = [f"rt.Name('{tokens[index+1]}')"]
			
			elif tokens[index] == '(':
				end = find_matching_bracket(index, tokens)
				block = Block(self, tokens[index:end+1])
				tokens[index:end+1] = [block]
			
			elif tokens[index] == 'for':
				for_loop = For_loop(self, tokens, index, indent)
				tokens[index:for_loop.end+1] = [for_loop]
			
			elif tokens[index] in {'*', '/', '%'}:
				tokens[index-1:index+2] = [Statement(self, tokens[index-1:index+2])]
				index -= 1
			
			elif tokens[index] == ',': tokens.pop(index)
			
			elif tokens[index] == '.':
				if tokens[index-1] == ')':
					tokens[index-3:index+2] = [''.join(tokens[index-3:index+2])]
					index -= 2
				else:
					ind = index + 2
					while ind < len(tokens) and tokens[ind] == '.':
						ind += 2
					
					new = ''.join(tokens[index-1:ind])
					tokens[index-1:ind] = [new]
					index -= 1
			
			index += 1
		
		self.tokens = tokens
		

	def __repr__(self):
		indent = '\t'*self.indent
		
		text = indent
		index = 0
		while index < len(self.tokens):
			token = self.tokens[index]
			if token == '\n':
				text += '\n' + indent
			else:
				text += str(token) + ' '
				
			index += 1
		text = text[:-1]
		
		return f'{text}'


class Array_call(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index):
		super().__init__(tokens[index-1], parent)
		self.index = []
		self.end = 0
		
		index += 1
		while index < len(tokens) and tokens[index] != ']':
			token = tokens[index]
			
			if is_function(token) or is_function(token.split('.')[-1]):
				function_call = Function_call(self, tokens, index)
				tokens[index:function_call.end] = [function_call]
				self.index.append(function_call)
			
			elif token == '[':
				array_call = Array_call(self, tokens, index)
				tokens[index:array_call.end] = [array_call]
			
			else:
				self.index.append(token)

			index += 1

		self.end = index + 1

		if LOG: print(f'New array call:\t{str(self.name):<20}Indent: {self.indent:2}  Parent: {self.parent.name:<20}\n')

	def __repr__(self):
		index = self.index[0] if len(self.index) == 1 else ''
		text = f'{self.name}[{index}]'
		return text


class Array(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index):
		super().__init__('Array', parent)
		self.elements = []
		self.end = 0

		index += 2
		while index < len(tokens) and tokens[index] != ')':
			token = tokens[index]

			if is_function(token) or is_function(token.split('.')[-1]):
				function_call = Function_call(self, tokens, index)
				tokens[index:function_call.end] = [function_call]
				self.elements.append(function_call)

			elif token == '[':
				array_call = Array_call(self, tokens, index)
				tokens[index:array_call.end] = [array_call]
			
			elif token == '#':
				if tokens[index+1] == '(':
					array = Array(self, tokens, index)
					tokens[index:array.end] = [array]
					self.elements.append(array)
				else:
					tokens[index:index+2] = [f"rt.Name('{tokens[index+1]}')"]
					self.elements.append(tokens[index])
					
					
					
			elif token == ',': pass
			
			elif tokens[index+1] == 'as':
				tokens[index:index+3] = [f'{TYPE_DICT[tokens[index+2].lower()]}({tokens[index]})']
				self.elements.append(tokens[index])
			
			else:
				self.elements.append(token)

			index += 1

		self.end = index + 1

		if LOG: print(f'New array:\t{self.name:<20}Indent: {self.indent:2}  Parent: {self.parent.name:<20}\n')

	def __repr__(self):
		elements = ''
		for element in self.elements:
			elements += f'{element}, '

		text = f'[{elements[:-2]}]'
		return text


class Function_def(Piece):
	def __init__(self, parent: Piece, tokens: List[str], indent: int = 0):
		super().__init__(tokens[0], parent, indent)
		self.args:		List[Variable]	= []
		self.kwargs:	List[Variable]	= []
		self.body: Block	= Block(self, [])
		
		index = 1
		
		while index < len(tokens) and tokens[index] != '=':
			if index+1 < len(tokens) and tokens[index+1] == ':':
				self.kwargs.append(Variable(tokens[index], tokens[index+2]))
				index += 3
			else:
				self.args.append(Variable(tokens[index]))
				index += 1
		
		self.body = Block(self, tokens[index+3:], indent=self.indent + 1)
		
		if LOG: print(f'New function:\t{self.name:<20}Indent: {self.indent:2}  Parent: {self.parent.name:<20}')
			
	
	def __repr__(self):
		indent = '\t'*self.indent
		
		args = ''
		for arg in self.args:
			args += f'{arg.name}, '
		
		for kwarg in self.kwargs:
			args += f'{kwarg.name}={kwarg.value}, '
		
		return f'{indent}def {self.name}({args[:-2]}):\n{self.body}'


class Function_call(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index):
		super().__init__(tokens[index], parent)
		self.args = []
		index += 1
		
		while index < len(tokens):
			if tokens[index] == '(':  # block
				br_start = index
				index = find_matching_bracket(index, tokens)
				if index == br_start + 1: break  # no arguments
				else: self.args.append(Block(self, tokens[br_start+1:index]))
			
			elif tokens[index] == '[':
				array_call = Array_call(self, tokens, index)
				tokens[index-1:array_call.end-1] = [array_call]
				self.args.append(array_call)
					
			elif tokens[index] in {'\n', ')', ']', 'and', 'or'} | LIGATURES | OPERATORS:	break
			
			elif tokens[index] == '#':
				if tokens[index+1] == '(':
					array = Array(self, tokens, index)
					tokens[index:array.end] = [array]
					self.args.append(array)
				else:
					tokens[index:index+2] = [f"rt.Name('{tokens[index+1]}')"]
					self.args.append(tokens[index])
				
			
			elif index+1 < len(tokens) and tokens[index+1] != '[':
				if tokens[index+1] == '.':
					
					tokens[index:index+3] = [''.join(tokens[index:index+3])]
				
				if index+1 < len(tokens) and tokens[index+1] == ':':
					self.args.append(tokens[index] + '=' + tokens[index+2])
					index += 2
				else:
					self.args.append(tokens[index])
			elif index < len(tokens):
				self.args.append(tokens[index])
			
				
			index += 1
		
		tokens.insert(index, ')')
		
		self.end = index + 1
		
		if LOG: print(f'New function call:\t{self.name:<20}Indent: {self.indent:2}  Parent: {self.parent.name:<20}\n')

	def __repr__(self):
		args = ''
		for arg in self.args:
			args += f'{arg}, '
		
		def is_function(token: str) -> bool:
			return any(token.lower() == item.lower() for item in max_functions)
		
		
		is_ms_function = is_function(self.name) or is_function(self.name.split('.')[-1])
		
		if is_ms_function:	return f'rt.{self.name}({args[:-2]})'
		else:				return f'{self.name}({args[:-2]})'


class Struct(Piece):
	def __init__(self, parent: Piece, tokens: List[Any], indent=0):
		super().__init__(tokens[0], parent, indent)
		
		self.properties: List[Variable]	= []
		self.methods: List[Function_def]	= []
		
		index = 3
		while index < len(tokens):
			token = tokens[index]
			if token not in [',', '\n']:
				if index < len(tokens) and token in ['fn', 'function']:
					end = find_matching_bracket(tokens.index(token), tokens)
					self.methods.append(Function_def(self, tokens[tokens.index(token) + 1:end]))
					tokens[tokens.index(token):end+1] = []
					
				else:
					# variable
					
					self.properties.append(Variable(token))
					if tokens[index+1] == '=':
						opened_r = 0
						opened_s = 0
						opened_c = 0
						start = index + 2
						while index < len(tokens):
							token = tokens[index]
							if token == '(':	opened_r += 1
							elif token == ')':	opened_r -= 1
							elif token == '[':	opened_s += 1
							elif token == ']':	opened_s -= 1
							elif token == '{':	opened_c += 1
							elif token == '}':	opened_c -= 1
							if opened_r == 0 and opened_s == 0 and opened_c == 0 and token in [',', '\n']:
								break
							index += 1
						
						self.properties[-1].value = Block(self, tokens[start:index])
						
				
			index += 1
		
		print(f'New struct: \t\t{self.name:<20} Indent: {self.indent:2}  Parent: {self.parent.name:<20}')
		
	def __repr__(self):
		
		indent = '\t'*(self.indent+1)
		
		init = f'\n{indent}def __init__(self):'
		
		indent += '\t'
		
		
		longest_property		= max(len(s_property.name) for s_property in self.properties) + 6
		longest_property_tabs	= math.ceil(longest_property/4) + 1
		
		properties = ''
		for s_property in self.properties:
			current_amount		= len(s_property.name) + 6
			current_amount_tabs	= math.ceil(current_amount/4)
			tab_amount			= longest_property_tabs - current_amount_tabs
			space				= '\t'*tab_amount
			properties += f'\n{indent}self.{s_property.name}{space}= {s_property.value}'
			
		methods = ''
		for method in self.methods:
			methods += f'\n{indent}{method}'
		
		return f'\n\nclass {self.name}:{init}{properties} {methods}'


class If_else(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index, indent: int = 0):
		super().__init__('If_else', parent, indent)
		self.end: int = 0
		
		condition_start	= index + 1
		
		condition_end	= find_condition_end(condition_start, tokens)
		
		then_end		= find_then_end(condition_end+2, tokens)
		
		index = then_end
		
		if index+2 < len(tokens):
			if tokens[index+2] == 'else':
				then_end = index + 1
				index += 1
			
			if tokens[index+1] == 'else':

				if tokens[index+3] == 'if':
					
					if_else = If_else(self, tokens, index+3, self.indent+1)
					tokens[index-15:if_else.end] = [if_else]
	
				elif tokens[index+2] == '\n':  # else next line
					
					if tokens[index+3] == '(':  # else block
						index = find_matching_bracket(index + 3, tokens)
						
					else:  # else next 1 line
						index += 3
						while index < len(tokens) and tokens[index] != '\n':	index += 1
					
				elif tokens[index+2] == '(':  # else block
					index = find_matching_bracket(index + 2, tokens)
					
				else:  # else same line
					index += 2
					while index < len(tokens) and tokens[index] != '\n':	index += 1
		
		else_end = index
		
		if_condition	= tokens[condition_start:	condition_end+1]
		then_statement	= tokens[condition_end + 2:	then_end+1]
		else_statement	= tokens[then_end + 2:		else_end+1] if then_end != else_end else []
		
		
		self.if_condition	= Block(self, if_condition,						name='If condition')
		self.then_statement	= Block(self, then_statement,	indent+1,	name='Then statement')
		self.else_statement	= Block(self, else_statement,	indent+1,	name='Else statement') if then_end != else_end else None
		
		self.end: int		= else_end or then_end
		
		if LOG: print(f'New if:\t\t\t{len(if_condition) + len(then_statement) + len(else_statement):<20}Indent: {self.indent:2}  Parent: {self.parent.name}')
	
	def __repr__(self):
		indent = '\t'*self.indent
		
		condition		= self.if_condition
		then_statement	= self.then_statement
		else_statement	= self.else_statement
		
		
		result = f'if {condition}:\n{then_statement}'
		
		if else_statement:
			result += f'\n{indent}else:\n{else_statement}'
		
		return result


class Try_except(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index, indent: int = 0):
		super().__init__('Try_except', parent, indent)
		
		try_start		= index + (2 if tokens[index+1] == '\n' else 1)
		
		try_end			= find_matching_bracket(try_start, tokens)
		index			= try_end
		
		while index < len(tokens) and tokens[index] != '(':	index += 1
		
		except_start	= index
		
		except_end		= find_matching_bracket(except_start, tokens)
		
		
		try_statement		= tokens[try_start+1:try_end]
		except_statement	= tokens[except_start:except_end+1]
		
		self.try_statement		= Block(self, try_statement,		indent+1, name='Try statement')
		self.except_statement	= Block(self, except_statement,	indent+1, name='Except statement') if except_statement != ['(', ')'] else 'pass'
		
		self.end: int = except_end+1
		
		if LOG: print(f'New try:\t\t{len(try_statement) + len(except_statement):<20}Indent: {self.indent:2}  Parent: {self.parent.name}')
	
	def __repr__(self):
		indent = '\t'*self.indent
		
		try_statement		= str(self.try_statement)
		except_statement	= str(self.except_statement)
		
		if '\n' in try_statement:
			result = f'try:\n{try_statement}'
		else:
			index = 0
			while index < len(try_statement) and try_statement[index] == '\t':
				index += 1
			try_statement = try_statement[index:]
			
			result = f'try: {try_statement}'
		
		if '\n' in except_statement:
			result = result + f'\n{indent}except:\n{except_statement}'
		else:
			index = 0
			while index < len(except_statement) and except_statement[index] == '\t':
				index += 1
			except_statement = except_statement[index:]
			result = result + f'\n{indent}except: {except_statement}'
		
		return result


class For_loop(Piece):
	def __init__(self, parent: Piece, tokens: List[str], index, indent: int = 0):
		super().__init__('For_loop', parent, indent)
		
		def_start = index + 1
		
		self.is_collect = False
		
		while index < len(tokens) and tokens[index] not in ['\n', 'do']:
			if tokens[index] == 'collect':	self.is_collect = True
			index += 1
		
		def_end = index
		
		body_start = index + (-1 if self.is_collect else 2)
		body_end = find_matching_bracket(body_start, tokens)
		
		self.def_statement	= Block(parent, tokens[def_start:def_end])
		self.body			= Block(parent, tokens[body_start+1:body_end-1], indent+1)
		
		self.end: int = body_end
		
		if LOG: print(f'New for:\t\t{len(tokens):<20}Indent: {indent:2}  Parent: {parent.name}')
		
	def __repr__(self):
		if self.is_collect:	text = f'for {self.def_statement}'
		else:				text = f'for {self.def_statement}:\n{self.body}'
		return text
		

def tokenize(text: str) -> list[str]:
	text = '\n'.join(line for line in text.splitlines() if line.strip())
	tokens = re.findall(r'''('[^']*'|"[^"]*"|\w+|[^\s\w]|\n)''', text)
	tokens = [token for token in tokens if token.strip(' \t\r\f\v') != '']
	return tokens


def remove_comments_from_tokens(tokens: List[str]) -> List[str]:
	index = 0
	while index < len(tokens):
		if tokens[index] == '-' and tokens[index + 1] == '-':
			start = index
			while tokens[index] != '\n':
				index += 1
			tokens[start:index] = []
			index = start+1

		index += 1
		
	return tokens


def remove_comments_from_string(text: str) -> str:
	lines = text.split('\n')
	cleaned_lines = []
	for line in lines:
		in_string = False
		new_line = []
		i = 0
		while i < len(line):
			if line[i] == '"':
				in_string = not in_string
			if not in_string and line[i:i+2] == '--':
				break
			new_line.append(line[i])
			i += 1
		cleaned_lines.append(''.join(new_line).rstrip())
	return '\n'.join(cleaned_lines)


def merge_sequence(tokens: List[str], sequence: str) -> List[str]:
	sequence = list(sequence)
	index = 0
	while index < len(tokens):
		if tokens[index:index+len(sequence)] == sequence:
			tokens[index:index+len(sequence)] = [''.join(tokens[index:index+len(sequence)])]
		index += 1
	return tokens


def parse_tokens(tokens: List[Any]) -> str:
	return str(Block(Root(), tokens, -1))
