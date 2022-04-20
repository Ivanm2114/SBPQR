import sys
import os
import datetime
from threading import Thread
from PyQt5 import uic, QtCore
from PIL.ImageQt import ImageQt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QLabel, QFileDialog, QColorDialog
from PyQt5.QtGui import QPixmap, QFont, QIcon, QPainter, QColor
from PyQt5.QtCore import QTimer, Qt
from flask import Flask
from flask_restful import Api

settingsUI = os.path.abspath('UI/SettingsWindow.ui')
admin_panelUI = os.path.abspath('UI/AdminPanel.ui')
colors_config = os.path.abspath('UI/colors.cfg')
config = os.path.abspath('config.cfg')
showfile = os.path.abspath('show.txt')
icon = os.path.abspath('IMGs/monitor.ico')
main = ''
flaskThread = ''
admin_panel = ''
is_running = False


def startFlaskThread():
    import qr_api
    global flaskThread, main
    web_app = Flask(__name__)

    api = Api(web_app)
    web_app.config['SECRET_KEY'] = 'Econica'
    web_app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
        days=365)
    web_app.register_blueprint(qr_api.blueprint)

    kwargs = {'port': main.port, 'host': '127.0.0.1'}

    flaskThread = Thread(target=web_app.run, daemon=True, kwargs=kwargs).start()


class ShowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(icon))
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        f = open(config, encoding='utf-8').readlines()
        picpath = f[0].replace('\n', '')
        os.chdir(picpath)
        if 'picture.png' in os.listdir():
            os.remove('picture.png')
        self.port = int(f[1])
        self.font = QFont()
        self.mode = 'standBy'
        self.interval = int(f[2]) * 1000
        self.font.setPointSize(int(f[4]))

        self.pictures = []
        data = open(colors_config, encoding='utf-8').readlines()
        file = open(showfile, mode='w')
        file.write(str(False))
        file.close()
        self.screen_number = int(f[3]) - 1
        for element in os.listdir():
            if element[len(element) - 3:].lower() in ['png', 'gif', 'jpg']\
                    or element[len(element) - 4].lower() == 'jpeg':
                self.pictures.append(element)

        self.move(QDesktopWidget().screenGeometry(self.screen_number).x(),
                  QDesktopWidget().screenGeometry(self.screen_number).y())
        self.showFullScreen()
        self.setWindowTitle('Окно демонстрации')
        self.label = QLabel(self)
        self.label.setFont(self.font)
        r, g, b, a = list(map(int, data[1][1:-1].split(',')))
        self.label.setStyleSheet(f"color: rgba({r}, {g}, {b},{a})")
        self.count = 0
        self.label.move(200, 100)
        self.timer = QTimer()
        self.check = QTimer()
        self.check.timeout.connect(self.checkFile)
        self.check.setInterval(500)
        self.check.start()
        self.w = self.screen().size().width()
        self.h = self.screen().size().height()
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.changePicture)
        self.timer.start()
        if self.pictures:
            self.current = self.pictures[0]
            self.a = ImageQt(self.current)
            self.image = QLabel(self)
            self.pixmap = QPixmap.fromImage(self.a)
            self.pixmap = self.pixmap.scaled(self.w, self.h,
                                             Qt.KeepAspectRatio)
            self.image.resize(self.pixmap.size())
            self.image.move(self.w // 2 - self.pixmap.size().width() // 2,
                            self.h // 2 - self.pixmap.size().height() // 2)
            self.image.setPixmap(self.pixmap)
            self.image.setVisible(True)
        else:
            self.error_no_pictures()
        data = open(colors_config, encoding='utf-8').readlines()
        r, g, b, a = list(map(int, data[0][1:-2].split(',')))
        self.setStyleSheet(f"background-color: rgba({r},{g},{b},{a})")

    def error_no_pictures(self):
        self.label.setText('В папке нет подходящих картинок.')
        self.label.adjustSize()

    def checkFile(self):
        f = open(showfile)
        if f.readline().strip() == 'True':
            self.takePayment(f.readline().strip())
        else:
            self.standbyMode()

    def takePayment(self, text=''):
        global admin_panel
        self.mode = 'takePayment'
        with_text = (text != '')
        if with_text:
            self.label.setVisible(True)
            self.label.setText(text)
            self.label.adjustSize()
        else:
            self.label.setText('')
        if self.showQR(with_text):
            self.label.move(self.w // 2 - self.label.width() // 2, 5)
            admin_panel.changeText('Демонстарция QR кода')
            self.image.setVisible(True)
        else:
            self.label.move(self.w // 2 - self.label.width() // 2,
                            self.h // 2 - self.label.height() // 2)
            admin_panel.changeText('Демонстарция сообщения')
            self.image.setVisible(False)

    def changePicture(self):
        if self.mode == 'standBy':
            self.image.setVisible(True)
            self.count = (self.count + 1) % len(self.pictures)
            self.current = self.pictures[self.count]
            self.a = ImageQt(self.current)
            self.pixmap = QPixmap.fromImage(self.a)
            self.pixmap = self.pixmap.scaled(self.w, self.h,
                                             Qt.KeepAspectRatio)
            self.image.resize(self.pixmap.size())
            self.image.move(self.w // 2 - self.pixmap.size().width() // 2,
                            self.h // 2 - self.pixmap.size().height() // 2)
            self.image.setPixmap(self.pixmap)

    def showQR(self, with_text):
        if 'picture.png' in os.listdir():
            self.current = 'picture.png'
            self.a = ImageQt(self.current)
            self.pixmap = QPixmap.fromImage(self.a)
            if with_text:
                self.pixmap = self.pixmap.scaled(self.h - self.label.rect().height() - 10,
                                                 self.h - self.label.rect().height() - 10,
                                                 Qt.KeepAspectRatio)
                self.image.resize(self.pixmap.size())
                self.image.move(self.w // 2 - self.pixmap.size().width() // 2,
                                self.label.height() + 10)
                self.image.setPixmap(self.pixmap)
            else:
                self.pixmap = self.pixmap.scaled(self.screen().size().height() - 10,
                                                 self.screen().size().height() - 10,
                                                 Qt.KeepAspectRatio)
                self.image.resize(self.pixmap.size())
                self.image.move(self.w // 2 - self.pixmap.size().width() // 2,
                                0)
                self.image.setPixmap(self.pixmap)
            return True
        return False

    def standbyMode(self):
        if self.mode == 'takePayment':
            self.mode = 'standBy'
            admin_panel.changeText('Ожидание запроса')
            self.label.setText('')
            self.changePicture()
            if 'picture.png' in os.listdir():
                os.remove('picture.png')


class SettingsWindow(QMainWindow):
    def __init__(self):
        super(SettingsWindow, self).__init__()
        uic.loadUi(settingsUI, self)
        self.fileButton.clicked.connect(self.choseFile)
        self.Monitor_spinBox.setMaximum(QDesktopWidget().screenCount())
        self.pushButton.clicked.connect(self.start)
        self.pushButton_2.clicked.connect(self.setBackColor)
        self.pushButton_5.clicked.connect(self.setFontColor)
        try:
            file = open(colors_config, encoding='utf-8', mode='r')
            f = file.readlines()
            file.close()
            if len(f) == 0:
                file = open(colors_config, encoding='utf-8', mode='w')
                file.write('4293980400\n4278190080')
                file.close()
        except FileNotFoundError:
            file = open(colors_config, encoding='utf-8', mode='w')
            file.write('(240, 240, 240, 255)\n(0, 0 , 0, 255)')
            file.close()
        self.paintEvent(1)
        try:
            file = open(config, encoding='utf-8')
            f = file.readlines()
            for i in range(len(f)):
                f[i] = f[i].replace('\n', '')
                if f[i].isdigit():
                    f[i] = int(f[i])
            if f != [] and not is_running:
                self.start(True)
            elif f != [] and is_running:
                self.Monitor_spinBox.setValue(f[3])
                self.lineEdit.setText(f[0])
                self.Port_spinBox.setValue(f[1])
                self.Timing_spinBox.setValue(f[2])
                self.Font_spinBox.setValue(f[4])
            else:
                self.show()
            file.close()
        except FileNotFoundError:
            f = open(config, encoding='utf-8', mode='w')
            f.close()
            self.show()

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawRecs(qp)
        qp.end()

    def drawRecs(self, qp):
        data = open(colors_config, encoding='utf-8').readlines()
        r, g, b, a = list(map(int, data[0][1:-2].split(',')))
        qp.setBrush(QColor(r, g, b, a))
        qp.drawRect(150, 260, 75, 51)
        r, g, b, a = list(map(int, data[1][1:-1].split(',')))
        qp.setBrush(QColor(r, g, b, a))
        qp.drawRect(450, 260, 75, 51)

    def setBackColor(self):
        color = QColorDialog.getColor()
        data = open(colors_config, encoding='utf-8').readlines()
        data[0] = str(color.getRgb())
        for n in range(2):
            data[n] = data[n].replace('\n', '')
        f = open(colors_config, encoding='utf-8', mode='w')
        f.write(data[0] + '\n' + data[1])
        f.close()
        self.paintEvent(1)

    def setFontColor(self):
        color = QColorDialog.getColor()
        data = open(colors_config, encoding='utf-8').readlines()
        data[1] = str(color.getRgb())
        for n in range(2):
            data[n] = data[n].replace('\n', '')

        f = open(colors_config, encoding='utf-8', mode='w')
        f.write(data[0] + '\n' + data[1])
        f.close()
        self.paintEvent(1)

    def start(self, file_is_ready=False):
        global is_running
        if not file_is_ready:
            data = [self.lineEdit.text(), self.Port_spinBox.value(), self.Timing_spinBox.value(),
                    self.Monitor_spinBox.value(), self.Font_spinBox.value()]
        else:
            file = open(config, encoding='utf-8')
            f = file.readlines()
            for i in range(len(f)):
                f[i] = f[i].replace('\n', '')
                if f[i].isdigit():
                    f[i] = int(f[i])
            data = f
            file.close()
        if all(data):
            f = open(config, encoding='utf-8', mode='w')
            f.writelines(map(lambda x: str(x) + '\n', data))
            f.close()
            is_running = True
            try:
                os.chdir(data[0])
                self.start_main()
                self.close()
            except FileNotFoundError:
                self.label_6.setText('Папка с картинками не найдена')
                self.show()
        elif not file_is_ready:
            self.label_6.setText('Заполните все поля.')
        else:
            self.label_6.setText('С файлом произошла ошибка. Заполните поля снова.')

    def choseFile(self):
        fname = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        self.lineEdit.setText(fname)

    def start_main(self):
        global main, admin_panel
        admin_panel = AdminPanelWindow()
        main = ShowWindow()
        startFlaskThread()
        main.show()
        admin_panel.show()


class AdminPanelWindow(QMainWindow):
    def __init__(self):
        super(AdminPanelWindow, self).__init__()
        uic.loadUi(admin_panelUI, self)
        self.setWindowTitle('Окно администратора')
        self.pushButton.clicked.connect(self.returnToSettings)
        self.closeButton.clicked.connect(self.closeAll)
        self.changeText('Ожидание запроса')

    def closeEvent(self, e):
        e.ignore()

    def returnToSettings(self):
        global main, settings
        main.close()
        del main
        settings = SettingsWindow()
        settings.show()
        self.close()

    def closeAll(self):
        if 'picture.png' in os.listdir():
            os.remove('picture.png')
        sys.exit(0)

    def changeText(self, text):
        self.label_2.setText(text)


app = QApplication(sys.argv)
settings = SettingsWindow()
