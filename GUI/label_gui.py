import time
import sys
import os

from PyQt4 import QtGui, QtCore
from PyQt4.phonon import Phonon

from win32api import GetSystemMetrics

# File store location
path = os.path.expanduser("~/.HBLog")
def get_filename(name,ext):
    # Create different data file for different sessions
    fname = name+"."+ext
    extnum = 0;
    try:
        os.makedirs(path)
    except OSError:
        pass
    while os.path.isfile(os.path.join(path, fname)):
        extnum += 1
        fname = name+'_'+str(extnum)+'.'+ext
    return fname

class PollTimeThread(QtCore.QThread):
    """
    This thread works as a timer.
    """
    update = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(PollTimeThread, self).__init__(parent)

    def run(self):
        while True:
            time.sleep(1)
            if self.isRunning():
                # emit signal
                self.update.emit()
            else:
                return

class Window(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.screen_width = GetSystemMetrics(0)
        self.screen_height = GetSystemMetrics(1)
        self.setGeometry(20,20,self.screen_width-80,self.screen_height-80)
        self.last_survey = False
        self.video_name = app.arguments()

        self.central_widget = QtGui.QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.VideoWidget = VideoWidget(self,self.video_name)
        self.SurveyWidget = SurveyWidget(self)
        self.ExitWidget = ExitWidget(self)

        self.central_widget.addWidget(self.VideoWidget)
        self.central_widget.addWidget(self.SurveyWidget)
        self.central_widget.addWidget(self.ExitWidget)
        self.central_widget.setCurrentWidget(self.VideoWidget)

        self.data_labels = [] # Variable used to store labels for data
        self.time = 0

        # signal-slot, for time lapse
        self.thread = PollTimeThread(self)
        self.thread.update.connect(self.update)

    def update(self):
        # slot
        lapse = self.VideoWidget.media.currentTime()/1000.0
        mins,secs = divmod(int(lapse),60) # (math.floor(a/b),a%b)
        timeformat = '%d:%d'%(mins,secs)
        # stop when 1 min is reached
        if (int(lapse) % 30 == 0 and int(lapse) >= 30):
            self.switchToSurveyPage()

    def startTimer(self):
        self.thread = PollTimeThread(self)
        self.thread.update.connect(self.update)
        self.thread.start()

    def switchToSurveyPage(self):
        self.setGeometry(20,20,640-80,400-80)
        self.thread.terminate()
        self.VideoWidget.media.pause()
        self.VideoWidget.screen.pause()
        self.central_widget.setCurrentWidget(self.SurveyWidget)
        self.time += 1

    def switchToVideoPage(self):
        if (self.last_survey):
            self.central_widget.setCurrentWidget(self.ExitWidget)
        else:
            self.setGeometry(20,20,self.screen_width-80,self.screen_height-80)
            self.central_widget.setCurrentWidget(self.VideoWidget)
            self.VideoWidget.media.play()
            self.VideoWidget.screen.play()
            self.startTimer()

class VideoWidget(QtGui.QWidget):
    def __init__ (self, parent, video_name):
        super(VideoWidget, self).__init__(parent)
        self.parent = parent
        self.video_name = video_name
        # media
        self.screen = Phonon.MediaObject(self)
        self.video_screen = Phonon.VideoWidget(self)
        self.video_screen.setMinimumSize(self.parent.screen_width, self.parent.screen_height)
        self.screen.finished.connect(self.onFinished)
        # media
        self.media = Phonon.MediaObject(self)
        self.video = Phonon.VideoWidget(self)
        self.video.setMinimumSize(640, 480)
        Phonon.createPath(self.media, self.video)
        Phonon.createPath(self.screen, self.video_screen)
        self.video_screen.move(0,0)
        point = parent.rect().bottomRight()
        global_point = parent.mapToGlobal(point)
        self.video.move(global_point - QtCore.QPoint(self.video.width(),self.video.height()))

    def startPlay(self):
        self.path = self.video_name[2]
        self.screen_path = self.video_name[3]
        if self.path and self.screen_path:
            self.media.setCurrentSource(Phonon.MediaSource(self.path))
            self.screen.setCurrentSource(Phonon.MediaSource(self.screen_path))
            # use a thread as a timer
            self.media.play()
            self.screen.play()
            self.parent.startTimer()

    def onFinished(self):
        self.parent.last_survey = True
        self.parent.switchToSurveyPage()

class SurveyWidget(QtGui.QWidget):
    def __init__ (self,parent):
        super(SurveyWidget, self).__init__(parent)
        self.parent = parent
        self.font = QtGui.QFont("Times",15)
        self.warning_font = QtGui.QFont("Times", 15, QtGui.QFont.Bold)
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
        self.layout = QtGui.QGridLayout(self)

        self.info = QtGui.QLabel(self)
        self.info.setText("How do you feel when programming in the 1min period that we show you just now.")
        self.info.setFont(self.font)

        self.warning = QtGui.QLabel(self)
        self.warning.setFont(self.warning_font)
        self.warning.setPalette(self.palette)

        self.layout.addWidget(self.info,1,1,1,3)
        self.layout.addWidget(self.warning,2,1,1,3)
        self.layout.setRowStretch(0,1)
        self.moods = QtGui.QButtonGroup(self)
        self.mood_buttons = []
        moods = ["Frustration: I can't solve it...",\
                 "Confusion: What is this? What should I do? Why is it not working?",\
                 "Boredom: This question is not interesting.",\
                 "Neutral: I feel neither good nor bad.",\
                 "Flow/Engagement: I know how to do it. I've got an idea!"]
        for idx,mood in enumerate(moods):
            mood_button = QtGui.QRadioButton(mood, self)
            mood_button.setFont(self.font)
            self.mood_buttons.append(mood_button)
            self.moods.addButton(mood_button)
            self.layout.addWidget(mood_button, idx+3, 1, 1,3)
        # control button
        self.button = QtGui.QPushButton('Continue', self)
        self.button.clicked.connect(self.handleButton)
        self.button.setFont(self.font)
        self.layout.setRowStretch(8,1)
        self.layout.addWidget(self.button,9,2,1,1)

    def handleButton(self):
        checked = False
        checked_value = ""
        for mood_button in self.mood_buttons:
            if (mood_button.isChecked()):
                checked = True
                checked_value = mood_button.text().split(":")[0]
                self.parent.data_labels.append([checked_value, str(self.parent.time- 1) + "~" + str(self.parent.time)])
                self.moods.setExclusive(False)
                mood_button.setChecked(False)
                self.moods.setExclusive(True)
        if (checked):
            self.warning.setText("")
            self.parent.switchToVideoPage()
        else:
            self.warning.setText("Please choose one option")
                

class ExitWidget(QtGui.QWidget):
    def __init__ (self,parent):
        super(ExitWidget, self).__init__(parent)
        self.parent = parent
        self.font = QtGui.QFont("Times",15)
        self.layout = QtGui.QGridLayout(self)
        self.info = QtGui.QLabel(self)
        self.info.setText("Thank you for your patience. You may now exit program.")
        self.info.setFont(self.font)
        self.layout.addWidget(self.info,0,2,1,1)
        self.layout.setColumnStretch(1,1)
        self.layout.setColumnStretch(3,1)
        # control button
        self.button = QtGui.QPushButton('Exit Program', self)
        self.button.clicked.connect(self.handleButton)
        self.button.setFont(self.font)
        self.layout.addWidget(self.button,1,2,1,1)

    def handleButton(self):
        self.info.setText("Storing data, please wait...")
        fname = get_filename("label","csv")
        label_file = open(os.path.join(path, fname), "w")
        for labels in self.parent.data_labels:
            label_file.write(str(labels[0])+","+str(labels[1])+"\n")
        label_file.close()
        QtCore.QCoreApplication.quit()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('VideoPlayer')
    window = Window()
    window.setWindowTitle("Label GUI")
    window.show()
    window.VideoWidget.startPlay()
    sys.exit(app.exec_())
