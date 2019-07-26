import datetime
import glob
import os
import sys
import re
import shutil
from threading import Timer

if len(sys.argv) < 4:
	print('Usage: python dater.py <iMovie Library Path> <Output Files Path> <Max Year of Tapes> [--repeat [hour to repeat daily, default: 3am]]')
	print('Example: python dater.py ~/Movies/iMovie\ Library.imovielibrary Upload/ 2016 --repeat 5')
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
	tempName = 'output.mov'
	os.system('ffmpeg -y -i '+input.replace('//','/').replace(' ','\ ')+' -c copy -map 0 -metadata creation_time="'+str(date)+'" '+tempName)
	fileDir = '/'.join(output.split('/')[:-1])
	print(fileDir)
	if not os.path.exists(fileDir):
		os.makedirs(fileDir)
	shutil.move(tempName, output)
	

def fixLibrary():
	print('Fixing dates...')
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
		for file in sorted(glob.glob(folder+"/Original Media/*.mov"), key=os.path.getmtime):
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
		for file in sorted(glob.glob(folder+"/Original Media/*.mov"), key=os.path.getmtime):
			outPath = sys.argv[2]+'/'+folder.split('/')[-2]+'/'+file.split('/')[-1]
			if not os.path.isfile(outPath):
				
				# If file has proper date, just use that
				fDate = datetime.datetime.fromtimestamp(os.stat(file).st_birthtime)
				if fDate < maxDate:
					fixDate(file, outPath, fDate)
				
				# Extrapolate date from other dates in folder
				else:
					latestDate = None
					for i in range(len(fileDates)):
						if fileDates[i] is not None and i < fileCounter:
							earliestDate = i
						if fileDates[i] is not None and latestDate is None and i > fileCounter:
							latestDate = i
					timeGuess = fileDates[earliestDate] + (((fileDates[latestDate]-fileDates[earliestDate]) / (latestDate-earliestDate)) * (fileCounter-earliestDate))
					fixDate(file, outPath, timeGuess)
					
			fileCounter += 1
	
	# Restart at 3am the next day if --repeat is enabled
	if len(sys.argv) >= 5 and sys.argv[4] == '--repeat':
		if len(sys.argv) == 6:
			repeatHour = int(sys.argv[5])
		else:
			repeatHour = 3
		x = datetime.datetime.today()
		y = x.replace(day=x.day+1, hour=repeatHour, minute=0, second=0, microsecond=0)
		delta_t = y-x
		secs = delta_t.seconds+1
		t = Timer(secs, fixLibrary)
		print('Done fixing dates, starting again tomorrow at', str(repeatHour))
		t.start()
	
fixLibrary()