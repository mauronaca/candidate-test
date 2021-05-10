import sys
from os import remove
import re

MEM_FILE_NAME = 'memdump0.mem' # por consola(?)
NEW_FILE_NAME = 'newtestcase.v'

def main(args):
	if len(args) != 2:
		sys.exit('Ingresar nombre de archivo')
	try:
		verilog_f = open(args[1], 'r')
	except FileNotFoundError:
		sys.exit('Archivo no encontrado')

	generar_dump(verilog_f)
	generar_nueva_sintaxis(verilog_f)

	verilog_f.close()

def generar_dump(verilog_f):
	f = open(MEM_FILE_NAME, 'w+')
	verilog_f.seek(0)
	verilog_txt = verilog_f.read()

	matches = re.findall(r'  reg \[(.*)\] (\S*) \[(.*)\];\n  initial begin\n((    \S*\[\S*\] = \S*;\n)*)  end\n', verilog_txt)
	try: 
		matches = matches[0][3] # Validarlo
	except IndexError:
		f.close()
		remove(MEM_FILE_NAME)
		verilog_f.close()
		sys.exit('Error en el archivo verilog')

	matches = matches.split('\n')
	for match in matches:
		try:
			match = re.search(r'\'\S(.*);', match).group(1)
			f.write(match+'\n')
		except AttributeError:
			continue
	f.close()
	
def generar_nueva_sintaxis(verilog_f):
	f = open(NEW_FILE_NAME, 'w+')
	verilog_f.seek(0)
	verilog_txt = verilog_f.read().split('\n')
	rplcmnt = '  $readmemh("%s", mem);\n'%MEM_FILE_NAME

	mem_block = False
	for line in verilog_txt:
		if re.match(r'  reg \[(.*)\] (\S*) \[(.*)\];', line) or mem_block:
			mem_block = True
			if re.match(r'  initial begin', line) or re.match(r'    \S*\[\S*\] = \S*;', line):
				continue
			if re.match(r'  end', line):
				mem_block = False
				continue
			else:
				f.write(line + '\n' + rplcmnt)
		else:
			f.write(line + '\n')

	f.close()

if __name__ == '__main__':
	main(sys.argv)