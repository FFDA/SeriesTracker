#! /usr/bin/python3

from urllib import request

from PyQt5.QtCore import QSettings, QStandardPaths, QDir
from PyQt5.QtSql import QSqlQuery

settings = QSettings("SeriesTracker", "SeriesTracker")

class ShowCovers:
	
	def __init__(self, IMDB_id, image):
		super(ShowCovers, self).__init__()
		self.IMDB_id = IMDB_id
		self.image = image
		self.set_path()
	
	def set_path(self):
		cover_folder = QStandardPaths.standardLocations(QStandardPaths.GenericDataLocation)[0] + "/SeriesTracker/covers/"
		settings.setValue("coverDir", cover_folder)
		
		QDir().mkpath(settings.value("coverDir"))
		
		path_to_cover = settings.value("coverDir") + self.IMDB_id + ".jpg"
		
		with open(path_to_cover, "bw") as f:
			f.write(request.urlopen(self.image).read())
