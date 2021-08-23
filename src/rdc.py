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
		self.localizationDict    = dictionary

		self._f.seek(0)
		self.metaMV = memoryview(self._f.read(Datasheet.metaSize)).cast("i")
		self.headerMV = memoryview(self._f.read(self.columnSize)).cast("i")
		self.cellMV = memoryview(self._f.read(self.cellSectionSize)).cast("i")
		self.stringRaw = self._f.read(self.stringSectionSize)

		self.rows = []
		self.headers = []
		self.PrepareHeaders()

	def __len__(self):
		return

	def PrepareHeaders(self):
		for index in range(len(self.headerMV)):
			if index % 3 != 1:
				continue
			val = self.GetStringFromOffset(self.headerMV[index])
			self.headers.append(val)

	def PrepareRows(self):
		for row in range(self.rowCount):
			strideStart = row * (self.columnCount*2)
			entry = Entry(self, self.cellMV[strideStart: strideStart + (self.columnCount*2)])
			self.rows.append(entry)

	def ParseSection(self, start, count, skipearly, skiplate, localize = True):
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
			value = self.GetStringFromOffset(offset)
			if localize == True:
				value = self.XMLCrossReference(value)
			result.append(value)
		return result

	def GetStringFromOffset(self, offset):
		if offset > self.stringSectionSize:
			return ""
		sliceEnd = offset
		while not self.stringRaw[sliceEnd:sliceEnd+1] == b'\x00':
			sliceEnd += 1
		return self.stringRaw[offset:sliceEnd].decode('utf-8')

	def WriteToFile(self, path):
		dirname = os.path.dirname(__file__)
		if os.path.isdir(path) == False:
			os.mkdir(path)
		with open(os.path.join(path, os.path.basename(self._f.name) + '.csv'), 'w', newline='\n') as csvfile:
			writer = csv.writer(csvfile, delimiter=';', quotechar='\'')
			writer.writerow(self.headers)
			for x in self.rows:
				writer.writerow(x.values)
				pass

	def XMLCrossReference(self, string):
		key = string.lower()
		if key is None:
			return string
		try:
			val = int(key)
			return string
		except ValueError:
			try:
				val = float(key)
				return string
			except ValueError:
				if len(key) <= 2:
					return string
				try:
					ref = self.localizationDict[key]
					return ref
				except KeyError:
					return string
		return string
				#ref = next((key for key in self.localizationDict.keys() if key.startswith(string)), None)
				#if ref is None:
				#	return string
				#else:
				#	return self.localizationDict[ref]

def XMLListParse(xmlfile):
	tree = ET.parse(xmlfile)
	root = tree.getroot()

	dictionary = {}

	for resource in root.findall('string'):
		key = resource.get("key").lower()
		if "_description" in key:
			continue
		if "_main" in key:
			continue
		if "_groupdesc" in key:
			continue
		key = key.removesuffix("_mastername")
		key = key.removesuffix("_groupname")
		key = key.removesuffix("_categoryname")
		if key is None:
			continue
		if key not in dictionary.keys():
			dictionary[key] = resource.text

	return dictionary

#Move to different file for more structured parsing
class Entry:
	"Collection of decoded row information"
	def __init__(self, datasheet: Datasheet, data: memoryview):
		self.datasheet = datasheet
		self.dataraw = data
		self.values = []
		self.columncount = len(self.datasheet.headers)
		self.ParseData(data)

	def __len__(self):
		return len(self.values)

	def __getitem__(self, key: int):
		return self.values[key]
        
	def ParseData(self, data: memoryview):
		for index in range(len(data)):
			if index % 2 != 0:
				continue
			offset = data[index]
			if offset < 2:
				offset = self.datasheet.stringSectionSize+1
			val = self.datasheet.GetStringFromOffset(offset)
			val = self.datasheet.XMLCrossReference(val)
			self.values.append(val)

	def ToCSV(self):
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