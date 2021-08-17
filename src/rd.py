import os, sys, getopt
import configparser
import glob
from rdc import *

def main(argv):
	inputfile = ''
	outputfile = ''
	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
		print( 'test.py -i <inputfile> -o <outputfile>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print( 'test.py -i <inputfile> -o <outputfile>')
			sys.exit()
		elif opt in ("-i", "--ifile"):
			inputfile = arg
		elif opt in ("-o", "--ofile"):
			outputfile = arg

	locDir = config['SETTINGS']['localizationdir']

	localizeDict = {}
	print("Creating Localization List...")
	for xmlpath in glob.glob(os.path.join(locDir, '*.xml')):
		localizeDict.update(XMLListParse(xmlpath))
	pass

	inDir = config['SETTINGS']['InputDir']

	for filepath in glob.glob(os.path.join(inDir, '*.datasheet')):
		datasheet = Datasheet(filepath, localizeDict)

		datasheet.PrepareRows()
		datasheet.WriteToFile(config['SETTINGS']['OutputDir'])
	pass

def InitializeConfig():
	if os.path.isfile("settings.ini") == True:
		config = configparser.ConfigParser()
		config.read('settings.ini')
		config['SETTINGS']['InputDir']
		pass
	else:
		config = configparser.ConfigParser()
		config['SETTINGS'] = {'InputDir':'..\\input\\datatable\\','LocalizationDir':'..\\input\\localization\\','OutputDir':'..\\output\\' }
		with open('settings.ini', 'w') as configfile:
			config.write(configfile)
	return config

def SaveConfig():
	with open('settings.ini', 'w') as configfile:
			config.write(configfile)
	pass

def SetConfigInput(path):
	config['SETTINGS']['inputdir'] = path
	SaveConfig()
	pass

def SetConfigOutput(path):
	config['SETTINGS']['outputdir'] = path
	SaveConfig()
	pass

config = InitializeConfig()

if __name__ == "__main__":
	main(sys.argv[1:])