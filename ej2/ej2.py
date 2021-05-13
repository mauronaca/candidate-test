import sys
import argparse
import os
import re

MEM_FILE_NAME = 'memdump0.mem' # por consola(?)
NEW_FILE_NAME = 'newtestcase.v'

def generar_dump(verilog_f):
	f = open(MEM_FILE_NAME, 'w+')
	verilog_f.seek(0)
	verilog_txt = verilog_f.read()

	# Busca en el archivo original y devuelve los aciertos. El tercer grupo es el bloque donde se inicializa la memoria.
	# Si no hubo acierto, error de indice, entonces cierra el archivo. 
	matches = re.findall(r'  reg \[(.*)\] (\S*) \[(.*)\];\n  initial begin\n((    \S*\[\S*\] = \S*;\n)*)  end\n', verilog_txt)
	try: 
		matches = matches[0][3] 
	except IndexError:
		f.close()
		os.remove(MEM_FILE_NAME)
		verilog_f.close()
		sys.exit('Error en el archivo verilog')

	# Copia solo los valores al nuevo archivo.
	matches = matches.split('\n')
	for match in matches:
		try:
			match = re.search(r'\'\S(.*);', match).group(1)
			f.write(match+'\n')
		except AttributeError:
			continue
	f.close()
	
def generar_nueva_sintaxis(verilog_f):
	# Abro el nuevo archivo a generar y guardo cada linea de texto del original
	f = open(NEW_FILE_NAME, 'w+') 
	verilog_f.seek(0)
	verilog_txt = verilog_f.read().split('\n')
	rplcmnt = '  $readmemh("%s", mem);\n'%MEM_FILE_NAME

	# Itero sobre cada linea del texto original y va copiandolas al nuevo archivo; Si encuentra la sentencia tipo reg [] mem [], 
	# entonces entra en el bloque de codigo de iniciacion de memoria. Lo primero que hace es copiar la nueva sentencia
	# y luego se saltea todo el bloque desde initial begin hasta end. 
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

def expected():
	# Valida si los nuevos archivos generados son iguales a los esperados en la carpeta expected.
	#with open(os.path.join(os.getcwd(), 'expected/expected.v')) as exp_f:
	with open('expected/expected.v') as exp_f, open(NEW_FILE_NAME) as f, open('expected/memdump0.mem') as expm_f, open(MEM_FILE_NAME) as fm:
		if f.read() == exp_f.read() and fm.read() == expm_f.read():
			return True
		else:
			#os.remove(MEM_FILE_NAME)
			#os.remove(NEW_FILE_NAME)
			return False

def main(file):
	try:
		verilog_f = open(file, 'r')
	except FileNotFoundError:
		sys.exit('Archivo no encontrado')

	generar_dump(verilog_f)
	generar_nueva_sintaxis(verilog_f)

	#assert expected()

	verilog_f.close()

if __name__ == '__main__':
	args_parser =  argparse.ArgumentParser()
	args_parser.add_argument('file', metavar = 'Nombre del archivo verilog a modificar')
	args = args_parser.parse_args()

	main(args.file)