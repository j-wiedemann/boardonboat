# coding: utf-8

import sys
import serial
import serial.tools.list_ports


from PyQt5 import uic, QtSerialPort
from PyQt5.QtWidgets import QApplication, QPushButton, QTextEdit, QDial, QLabel
from PyQt5.QtCore import QFile, QObject, QIODevice, QTimer, pyqtSlot


gaugeHtml = """<html><head/><body><p><span style="font-size:16pt;">
    {gaugeName}<br><span style="font-size:36pt;">
    {value} {unity}</span></p></body></html>"""

stylesheet = [
    "background-color: rgb(70, 100, 230);",  # blue
    "background-color: rgb(230, 70, 70);",  # red
    "background-color: rgb(20, 220, 20);",  # green
    "background-color: rgb(255, 255, 255);",  # white
]


class Dashboard(QObject):
    def __init__(self, ui_file, parent=None):
        super(Dashboard, self).__init__(parent)

        # get ui file and load it
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.window = uic.loadUi(ui_file)
        ui_file.close()

        self.window.showMaximized()

        # GAUGES
        self.temperatureGauge = self.window.findChild(QTextEdit, "textEdit_Temperature")
        self.pressureGauge = self.window.findChild(QTextEdit, "textEdit_Pressure")
        self.rpmGauge = self.window.findChild(QTextEdit, "textEdit_RPM")
        self.batteryGauge = self.window.findChild(QTextEdit, "textEdit_Battery")
        
        # RUDDER ANGLE INDICATOR
        self.rudderAngleGauge = self.window.findChild(QDial, "rudderAngle")

        ## ALARM CONTROL
        self.alarmTestButton = self.window.findChild(QPushButton, "pushButton_testAlarm")
        self.alarmTestButton.clicked.connect(self.alarmTestButtonClicked)

        # LOG CONSOLE
        self.logConsole = self.window.findChild(QTextEdit, "textEdit_Logs")
        
        # HORNS
        ## Horn button
        self.shortHornButton = self.window.findChild(QPushButton, "pushButton_shortHorn")
        self.shortHornButton.clicked.connect(self.shortHornButtonPressed)
        
        ## Horn button
        self.longHornButton = self.window.findChild(QPushButton, "pushButton_longHorn")
        self.longHornButton.clicked.connect(self.longHornButtonPressed)
        
        ## Horn button
        self.veryshortHornButton = self.window.findChild(QPushButton, "pushButton_veryshortHorn")
        self.veryshortHornButton.clicked.connect(self.veryshortHornButtonPressed)

        # LIGHTS BUTTONS
        ## Bow light
        self.bowLightButton = self.window.findChild(QPushButton, "pushButton_Bow")
        self.bowLightButton.clicked.connect(self.ligthsButtonsClicked)

        ## Bord light
        self.bordLightButton = self.window.findChild(QPushButton, "pushButton_Bord")
        self.bordLightButton.clicked.connect(self.ligthsButtonsClicked)

        ## Starbord light
        self.starbordLightButton = self.window.findChild(
            QPushButton, "pushButton_Starbord"
        )
        self.starbordLightButton.clicked.connect(self.ligthsButtonsClicked)

        ## Stern light
        self.sternLightButton = self.window.findChild(QPushButton, "pushButton_Stern")
        self.sternLightButton.clicked.connect(self.ligthsButtonsClicked)

        ## All lights
        self.allLightsButton = self.window.findChild(
            QPushButton, "pushButton_AllLights"
        )
        self.allLightsButton.clicked.connect(self.allLighsButtonClicked)

        ## LIGHTS TEST
        self.testLightsButton = self.window.findChild(
            QPushButton, "pushButton_lightsTest"
        )
        self.testLightsButton.clicked.connect(self.testLighsButtonClicked)

        self.alarms = dict()
        self.alarms["test"] = False
        self.alarms["temp"] = False
        self.alarms["pressure"] = False
        self.alarms["alternator"] = False
        self.alarms["lowBattery"] = False
        self.alarms["bowLight"] = False
        self.alarms["portLight"] = False
        self.alarms["starbordLight"] = False
        self.alarms["sternLight"] = False

        # Serial connecxion to  arduino
        self.portDevice = u"NON CONNECTÉ"
        self.serialTimer = QTimer()
        self.serialTimer.setInterval(2000)
        self.serialTimer.timeout.connect(self.getArduinoSerial)
        self.serialTimer.start()

        # Timer for logconsole
        self.logReceive = ""
        self.consoleTimer = QTimer()
        self.consoleTimer.setInterval(100)
        self.consoleTimer.timeout.connect(self.updateLogConsole)
        self.consoleTimer.start()
        
        # Show window
        self.window.show()

    def getArduinoSerial(self):
        ports = serial.tools.list_ports.comports(include_links=False)
        if len(ports) > 0:
            for port in ports:
                if 'ACM' in str(port):
                    self.arduino = QtSerialPort.QSerialPort(
                        port.device,
                        baudRate=QtSerialPort.QSerialPort.Baud9600,
                        readyRead=self.receive,
                    )
                    self.arduino.open(QIODevice.ReadWrite)
                    self.arduino.flush
                    if self.arduino.isOpen():
                        self.serialTimer.stop()
                        self.portDevice = port.device
                        break
        else:
            self.portDevice = u"NON CONNECTÉ"

    @pyqtSlot()
    def receive(self):
        """called when arduino send serial data"""
        while self.arduino.canReadLine():
            data = self.arduino.readLine().data()
            #print("ard read line",data)
            try:
                text = data.decode('utf-8').rstrip("\r\n")
                #print("ard decode rstrip",text)
                self.logReceive = text
                if text:
                    self.updateGauges(text)
            except:
                pass
        else:
            self.serialTimer.start()

    @pyqtSlot()
    def updateGauges(self, data: str):
        #print("data",data)
        # TEMP
        if data[0] == "T" and len(data) > 1:
            temp = float(data[1:])
            txt = gaugeHtml.format(gaugeName=u"Température", value=temp, unity=u" °C")
            self.temperatureGauge.setHtml(txt)
        
        # Pressure
        elif data[0] == "P" and len(data) > 1:
            pressure = float(data[1:])
            txt = gaugeHtml.format(gaugeName=u"Pression", value=pressure, unity=u" BAR")
            self.pressureGauge.setText(txt)
        
        # RPM
        elif data[0] == "R" and len(data) > 1:
            txt = gaugeHtml.format(
                gaugeName=u"Vitesse de rotation", value=data[1:], unity=u" RPM"
            )
            self.rpmGauge.setText(txt)
        
        # VOLATGE
        elif data[0] == "V" and len(data) > 1:
            #if data[1:].isnumeric():
            volt = float(data[1:])
            txt = gaugeHtml.format(gaugeName=u"Voltage", value=volt, unity=u" V")
            self.batteryGauge.setText(txt)
        
        # RUDDER ANGLE
        elif data[0] == "A" and len(data) > 1:
            self.rudderAngleGauge.setValue(int(float(data[1:])))
        
        # ALARME
        elif data[0] == "W" and len(data) > 1:
            self.alarmsManager(data[1:])
        
        # OTHER
        else:
            text = "UNKNOW DATA : " + str(data)
            self.logReceive = text

    def ligthsButtonsClicked(self):
        lightsState = [0, 0, 0, 0]
        if self.bowLightButton.isChecked():
            lightsState[0] = 1
            self.bowLightButton.setStyleSheet(stylesheet[2])
            self.arduino.write("1".encode("utf-8"))
        else:
            self.arduino.write("2".encode("utf-8"))
            self.bowLightButton.setStyleSheet("")
        if self.bordLightButton.isChecked():
            lightsState[1] = 1
            self.arduino.write("3".encode("utf-8"))
            self.bordLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("4".encode("utf-8"))
            self.bordLightButton.setStyleSheet("")
        if self.starbordLightButton.isChecked():
            lightsState[2] = 1
            self.arduino.write("5".encode("utf-8"))
            self.starbordLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("6".encode("utf-8"))
            self.starbordLightButton.setStyleSheet("")
        if self.sternLightButton.isChecked():
            lightsState[3] = 1
            self.arduino.write("7".encode("utf-8"))
            self.sternLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("8".encode("utf-8"))
            self.sternLightButton.setStyleSheet("")
        if not 0 in lightsState:
            self.allLightsButton.setChecked(True)
            self.allLightsButton.setText(u"TOUT ÉTEINDRE")
        elif not 1 in lightsState:
            self.allLightsButton.setChecked(False)
            self.allLightsButton.setText(u"TOUT ALLUMER")


    def allLighsButtonClicked(self):
        if self.allLightsButton.isChecked():
            self.bowLightButton.setChecked(True)
            self.bordLightButton.setChecked(True)
            self.starbordLightButton.setChecked(True)
            self.sternLightButton.setChecked(True)
            self.allLightsButton.setText(u"TOUT ÉTEINDRE")
        else:
            self.bowLightButton.setChecked(False)
            self.bordLightButton.setChecked(False)
            self.starbordLightButton.setChecked(False)
            self.sternLightButton.setChecked(False)
            self.allLightsButton.setText(u"TOUT ALLUMER")
        self.ligthsButtonsClicked()

    def testLighsButtonClicked(self):
        self.arduino.write("C".encode("utf-8"))

    def shortHornButtonPressed(self):
        QTimer.singleShot(1000, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))

    def longHornButtonPressed(self):
        QTimer.singleShot(4000, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))

    def veryshortHornButtonPressed(self):
        QTimer.singleShot(500, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))

    def horn_stop(self):
        self.arduino.write("E".encode("utf-8"))

    def alarmTestButtonClicked(self):
        if self.alarms["test"] == True:
            self.alarmsManager(str("00"))
        else:
            self.alarmsManager(str("10"))

    def alarmsManager(self, alarm: str):
        alarmState = int(alarm[0])
        alarmId = int(alarm[1:])
        #print(alarmState,alarmId)
        if True in self.alarms.values():
            wasTrue = True
        else:
            wasTrue = False
        if alarmId == 0:
            if alarmState:
                self.alarms["test"] = True
                self.alarmTestButton.setText(u"Effacer\nAlarme")
            else:
                self.alarms["test"] = False
                self.alarmTestButton.setText(u"Tester\nAlarme")
        elif alarmId == 1:
            if alarmState:
                self.alarms["temp"] = True
                self.temperatureGauge.setStyleSheet(stylesheet[1])
            else:
                self.alarms["temp"] = False
                self.temperatureGauge.setStyleSheet(stylesheet[3])
        elif alarmId == 2:
            if alarmState:
                self.alarms["pressure"] = True
                self.pressureGauge.setStyleSheet(stylesheet[1])
            else:
                self.alarms["pressure"] = False
                self.pressureGauge.setStyleSheet(stylesheet[3])
        elif alarmId == 3:
            if alarmState:
                self.alarms["alternator"] = True
                self.textEdit_Battery.setStyleSheet(stylesheet[1])
            else:
                self.alarms["alternator"] = False
                self.textEdit_Battery.setStyleSheet(stylesheet[3])
        elif alarmId == 4:
            if alarmState:
                self.alarms["lowBattery"] = True
                self.textEdit_Battery.setStyleSheet(stylesheet[1])
            else:
                self.alarms["lowBattery"] = False
                self.textEdit_Battery.setStyleSheet(stylesheet[3])
        elif alarmId == 5:
            if alarmState:
                self.alarms["bowLight"] = True
                self.bowLightButton.setStyleSheet(stylesheet[1])
            else:
                self.alarms["bowLight"] = False
                self.bowLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 6:
            if alarmState:
                self.alarms["portLight"] = True
                self.bordLightButton.setStyleSheet(stylesheet[1])
            else:
                self.alarms["portLight"] = False
                self.bordLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 7:
            if alarmState:
                self.alarms["starbordLight"] = True
                self.starbordLightButton.setStyleSheet(stylesheet[1])
            else:
                self.alarms["starbordLight"] = False
                self.starbordLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 8:
            if alarmState:
                self.alarms["sternLight"] = True
                self.sternLightButton.setStyleSheet(stylesheet[1])
            else:
                self.alarms["sternLight"] = False
                self.sternLightButton.setStyleSheet(stylesheet[3])
        else:
            pass

        if (wasTrue == False) and (True in self.alarms.values()):
            print("Alarm is OFF and have to be ON")
            self.arduino.write("B".encode("utf-8"))
        elif (wasTrue == True) and (not True in self.alarms.values()):
            print("Alarm is ON and have to be OFF")
            self.arduino.write("A".encode("utf-8"))
        else:
            #print("No changes for ALARM")
            pass

    def updateLogConsole(self):
        msg = """<html><head/><body>
    <p><span style=" font-size:12pt;">Connection série : """
        
        msg += self.portDevice
        msg += "</span></p>"

        msg += """<p><span style=" font-size:12pt;">Alarmes en cours :</span><ul>"""
        if not True in self.alarms.values():
            self.logConsole.setStyleSheet(stylesheet[3])
            msg += "<li>Pas d'alarmes en cours</li>"
        else:
            self.logConsole.setStyleSheet(stylesheet[1])
            if self.alarms["test"]:
                msg += "<li>ALARME TEST</li>"
            if self.alarms["temp"]:
                msg += "<li>ALARME TEMPÉRATURE</li>"
            if self.alarms["pressure"]:
                msg += "<li>ALARME PRESSION HUILE</li>"
            if self.alarms["alternator"]:
                msg += "<li>ALARME ALTERNATEUR</li>"
            if self.alarms["lowBattery"]:
                msg += "<li>ALARME BATTERIE FAIBLE</li>"
            if self.alarms["bowLight"]:
                msg += "<li>ALARME FEUX NAVIGATION PROUE</li>"
            if self.alarms["portLight"]:
                msg += "<li>ALARME FEUX NAVIGATION BABORD</li>"
            if self.alarms["starbordLight"]:
                msg += "<li>ALARME FEUX NAVIGATION TRIBORD</li>"
            if self.alarms["sternLight"]:
                msg += "<li>ALARME FEUX NAVIGATION POUPE</li>"
        msg += "</ul></p>"
        msg += """<p><span style=" font-size:12pt;">Logs : {log}</span></p></body></html>""".format(log = self.logReceive)

        self.logConsole.setText(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    board = Dashboard("BoardOnBoat.ui")
    sys.exit(app.exec_())
