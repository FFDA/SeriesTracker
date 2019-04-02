#! /usr/bin/python3




from PyQt5.QtSql import QSqlQuery

settings = QSettings("SeriesTracker", "SeriesTracker")

class ShowCovers:
	
	def __init__(self, IMDB_id, image):
		super(ShowCovers, self).__init__()
		self.IMDB_id = IMDB_id
		self.image = image
			

