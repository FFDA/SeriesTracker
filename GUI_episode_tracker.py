#! /usr/bin/python3

from PyQt5.QtCore import Qt, QCoreApplication
import PyQt5.QtSql as QtSql
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import sqlite3





class mainWindow(QMainWindow):

    # Opening a database.
    database = QtSql.QSqlDatabase().addDatabase("QSQLITE3", "./shows.db")
    database.open()

    uzklausa = QtSql.QSqlQuery("SELECT * FROM shows WHERE IMDB_id='tt3766376'")



    def __init__(self):
        super().__init__()

        self.top = 200
        self.left = 500
        self.height = 700
        self.width = 1000
        self.initUI()


    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowTitle("Series Episode Tracker")
        self.tab_widget = TabWidget(self)
        self.setCentralWidget(self.tab_widget)
        self.show()

class TabWidget(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        # Initializeing layout for the widget of the main Window?
        self.layout = QVBoxLayout(self)
        
        # Initializing tab screen by setting QTabWidget and than adding tabs with QWidget as a main function.
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()

        # Adding tabs to the tabs (QTabWidget) widget and setttig names for it.
        self.tabs.addTab(self.tab1, "Currently Watching")
        self.tabs.addTab(self.tab2, "Plan To Watch")
        self.tabs.addTab(self.tab3, "Finished Watching")
        
        # Telling to look for a function that will set information in the widget.
        self.tab1UI()

        # Adding tabs to the widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        
    # Defining first tab UI.
    def tab1UI(self):
        
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel())
        # layout.addWidget(QPushButton("Spausk"))
        self.tab1.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = mainWindow()
    sys.exit(app.exec_())
