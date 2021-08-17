import os
import csv
import binascii
import xml.etree.ElementTree as ET
import re

from pathlib import Path
from ctypes import cdll, c_char_p, create_string_buffer

class Datasheet:
	metaSize          = 92
	columnCountOffset = 68
	rowCountOffset    = 72

	def __init__(self, path, dictionary):
		self.totalFileSize = Path(path).stat().st_size
		self._f = open(path, "rb")

		self._f.seek(Datasheet.columnCountOffset)
		self.columnCount = int.from_bytes(self._f.read(4), 'little')
		self._f.seek(Datasheet.rowCountOffset)
		self.rowCount = int.from_bytes(self._f.read(4), 'little')
		self.columnSize          = self.columnCount * 12
		self.rowSize             = self.columnCount * 8
		self.cellSectionSize     = self.rowSize * self.rowCount
		self.stringSectionSize   = self.totalFileSize - self.cellSectionSize - self.columnSize - Datasheet.metaSize
		self.headerOffset        = Datasheet.metaSize
		self.cellSectionOffset   = self.columnSize + Datasheet.metaSize
		self.stringSectionOffset = self.cellSectionOffset + self.cellSectionSize
		self.localizationDict = dictionary

		self.rows = []
		self.headers = []
		self.PrepareHeaders()

	def PrepareHeaders(self):
		self.headers = self.ParseSection(self.headerOffset, self.columnCount, 4, 4)

	def PrepareRows(self):
		for row in range(0, self.rowCount):
			DrawProgress("Processing row " + str(row+1) + " of " + str(self.rowCount))
			self.rows.append(self.ParseSection(self.cellSectionOffset + (row * self.rowSize), self.columnCount, 0, 4))
		return csv

	def ParseSection(self, start, count, skipearly, skiplate):
		self._f.seek(start)
		result = []
		offsetList = []
		for x in range(count):
			if skipearly > 0:
				self._f.seek(skipearly, 1)
			offset = self._f.read(4)
			if skiplate > 0 :
				self._f.seek(skiplate, 1)
			offset = int.from_bytes(offset, 'little')
			if offset >= 2:
				offsetList.append(offset)
			else:
				offsetList.append(stringSectionSize+1)
		for index in range(len(offsetList)):
			offset = offsetList[index]
			string = self.GetStringFromOffset(offset)
			string = self.XMLCrossReference(string)
			result.append(string)
		return result

	def GetStringFromOffset(self, offset):
		if offset > self.stringSectionSize:
			return ""
		self._f.seek(self.stringSectionOffset, 0)
		val = self._f.seek(offset, 1)
		val = self._f.read(1)
		stream = bytearray()
		while not val == b'\x00':
			stream.append(int.from_bytes(val, 'little'))
			val = self._f.read(1)
		return stream.decode()

	def WriteToFile(self, path):
		dirname = os.path.dirname(__file__)
		if os.path.isdir(path) == False:
			os.mkdir(path)
		with open(os.path.join(path, os.path.basename(self._f.name) + '.csv'), 'w', newline='\n') as csvfile:
			writer = csv.writer(csvfile, delimiter=';', quotechar='\'')
			writer.writerow(self.headers)
			for x in self.rows:
				writer.writerow(x)
				pass

	def XMLCrossReference(self, string):
		ref = next((key for key in self.localizationDict.keys() if key.startswith(string)), None)
		if ref is None:
			return string
		else:
			return ref

def XMLListParse(xmlfile):
	tree = ET.parse(xmlfile)
	root = tree.getroot()

	dictionary = {}

	for resource in root.findall('string'):
		dictionary[(resource.get("key").removesuffix("_RecipeName"))] = resource.text

	return dictionary

#Move to different file for more structured parsing
class Recipe:
	"Collection of decoded recipe information"
	def __init__(self, data, tableheadercount):
		self.dataraw = data
		self.columncount = tableheadercount
		self.parse_data(data, tableheadercount)
        
	def parse(self, data, tableheadercount):
		pass

def PrintRange(start, range):
	f.seek(start)
	value = f.read(range)
	print(value)

def DrawProgress(percent):
	os.system('cls' if os.name == 'nt' else 'clear')
	print("Progress: " + str(percent))

## Debug
def main():
	while True:
		inp = input("Offset: ")
		
		offset = int(inp)
		print(offset)
		print("Output: " + GetStringFromOffset(offset))

if __name__ == "__main__":
	main()