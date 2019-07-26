import datetime
import glob
import os
import sys
import re

if len(sys.argv) < 4:
	print('Usage: python dater.py <iMovie Library Path> <Output Files Path> <Max Year of Tapes>')
	print('Example: python dater.py ~/Movies/iMovie\ Library.imovielibrary Upload/ 2016')
	exit()

def getYear(input):
	maxYear = int(sys.argv[3])-2000
	yearInput = int(input)
	if yearInput < maxYear:
		return 2000 + yearInput
	elif yearInput >= maxYear and yearInput < 100:
		return 1900 + yearInput
	else:
		return yearInput
		
def fixDate(input, output, date):
	print('Remuxing', input.split('/')[-1], 'with date', date)

def fixLibrary():
	for folder in glob.glob(sys.argv[1]+"/*/"):
		
		# Confirm labeled dates are acceptable
		folderNums = re.findall(r'\d+', folder.split('/')[-2])
		if not (len(folderNums) == 3 or len(folderNums) == 6):
			break
		d1 = datetime.datetime(getYear(folderNums[2]), int(folderNums[0]), int(folderNums[1]), hour=0, minute=0, second=0)
		d2 = datetime.datetime(getYear(folderNums[-1]), int(folderNums[-3]), int(folderNums[-2]), hour=23, minute=59, second=59)
		if d1 > d2:
			break

		# Fix folder date range if it disagrees with files inside
		fileDates = []
		maxDate = datetime.datetime(int(sys.argv[3]), 12, 31, hour=23, minute=59, second=59)
		for file in sorted(glob.glob(folder+"*.mov"), key=os.path.getmtime):
			fDate = datetime.datetime.fromtimestamp(os.stat(file).st_birthtime)
			if fDate < maxDate:
				fDate = datetime.datetime.fromtimestamp(os.stat(file).st_birthtime)
				if (fDate < d1):
					d1 = datetime.datetime(fDate.year, fDate.month, fDate.day, hour=0, minute=0, second=0)
				if (fDate > d2):
					d1 = datetime.datetime(fDate.year, fDate.month, fDate.day, hour=23, minute=59, second=59)
				fileDates.append(fDate)
			else:
				fileDates.append(None)
		fileDates.insert(0, d1)
		fileDates.append(d2)
		
		# Remux each file with proper date if needed
		fileCounter = 1;
		for file in sorted(glob.glob(folder+"*.mov"), key=os.path.getmtime):
			outPath = sys.argv[2]+'/'+folder.split('/')[-2]+'/'+file.split('/')[-1]
			if not os.path.isfile(outPath):
				
				# If file has proper date, just use that
				fDate = datetime.datetime.fromtimestamp(os.stat(file).st_birthtime)
				if fDate < maxDate:
					fixDate(file, outPath, fDate)
				
				# Extrapolate date from other dates in folder
				else:
					latestDate = None
					for i in range(fileDates):
						if fileDates[i] is not None and i < fileCounter:
							earliestDate = i
						if fileDates[i] is not None and latestDate is None and i > fileCounter:
							latestDate = i
					timeGuess = fileDates[earliestDate] + (((fileDates[latestDate]-fileDates[earliestDate]) / (latestDate-earliestDate)) * (fileCounter-earliestDate))
					fixDate(file, outPath, timeGuess)
					
			fileCounter += 1
	
if __name__ == "__main__":
	fixLibrary()