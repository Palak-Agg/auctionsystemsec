from colorama import init, Fore, Back, Style
import time
from datetime import datetime
import os
import inspect

def info(msg, new_line=True):
	print("{0}{1}{2}[INFO]> {3}{4}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.GREEN,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

def warning(msg, new_line=True):
	print("{0}{1}{2}[WARN]> {3}{4}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.YELLOW,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

def error(msg, new_line=True):
	print("{0}{1}{2}[ERROR]> {3}{4}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.RED,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

# def debug(msg, new_line=True):
# 	print("{}{}{}[DEBUG] {}[{}]> {}".format(
# 		Fore.WHITE,
# 		time.strftime('[%H:%M:%S]'),
# 		Fore.WHITE,
# 		Fore.RESET,
# 		__getCallerInfo(),
# 		msg), end=("\n" if new_line else ""), flush=(not new_line))
def debug(msg, new_line=True):
	print("{}{}{}[DEBUG]{}> {}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.CYAN,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

def high_debug(msg, new_line=True):
	print("{}{}{}[HIGH_DEBUG]{}> {}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.CYAN,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

def log(msg, new_line):
		print("{0}{1}{2}[INFO]> {3}{4}".format(
		Fore.WHITE,
		time.strftime('[%H:%M:%S]'),
		Fore.GREEN,
		Fore.RESET,
		msg), end=("\n" if new_line else ""), flush=(not new_line))

def __getCallerInfo():
	frm = inspect.stack()[1]
	mod = inspect.getmodule(frm[0])
	return mod.__name__
	# print '[%s] %s' % (mod.__name__, msg)

def unescape(text):
	regex = re.compile(b'\\\\(\\\\|[0-7]{1,3}|x.[0-9a-f]?|[\'"abfnrt]|.|$)')

	 