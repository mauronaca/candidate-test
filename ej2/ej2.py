import sys
import re

def main(args):
	if len(args) != 2:
		sys.exit('Ingresar nombre de archivo')
	try:
		verilog = open(args[1], 'r')
	except FileNotFoundError:
		sys.exit('Archivo no encontrado')

	generar_dump(verilog)
	crear_archivo(verilog)

	verilog.close()

def generar_dump(verilog):
	f = open('memdump0.mem', 'w+')
	text = verilog.read()

	matches = re.findall(r'  reg \[(.*)\] (\S*) \[(.*)\];\n  initial begin\n((    \S*\[\S*\] = \S*;\n)*)  end\n', text)
	matches = matches[0][3] # Validar esto
	matches = matches.split('\n')
	for match in matches:
		try:
			match = re.search(r'\'(.*);', match).group(1)
			f.write(match+'\n')
		except AttributeError:
			pass
	f.close()
	
def crear_archivo(verilog):
	f = open('test_modificado.v', 'w+')
	print(f)

if __name__ == '__main__':
	main(sys.argv)