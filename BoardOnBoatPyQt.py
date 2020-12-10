# coding: utf-8

import sys
import serial
import serial.tools.list_ports


from PyQt5 import uic, QtSerialPort
from PyQt5.QtWidgets import QApplication, QPushButton, QTextEdit, QDial
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

        # LOG CONSOLE
        self.logConsole = self.window.findChild(QTextEdit, "textEdit_Logs")

        # GAUGES
        self.temperatureGauge = self.window.findChild(QTextEdit, "textEdit_Temperature")
        self.pressureGauge = self.window.findChild(QTextEdit, "textEdit_Pressure")
        self.rpmGauge = self.window.findChild(QTextEdit, "textEdit_RPM")

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
        
        # RUDDER ANGLE INDICATOR
        self.rubberAngleGauge = self.window.findChild(QDial, "rudderAngle")

        ## ALARM CONTROL
        self.alarmButton = self.window.findChild(QPushButton, "pushButton_Alarm")
        self.alarmButton.clicked.connect(self.alarmButtonClicked)

        self.alarmState = False
        self.tempAlarm = False
        self.pressureAlarm = False
        self.alternatorAlarm = False
        self.lowBatteryAlarm = False
        self.bowAlarm = False
        self.portAlarm = False
        self.starbordAlarm = False
        self.sternAlarm = False

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
                if 'ACM' in port:
                    self.arduino = QtSerialPort.QSerialPort(
                        port.device,
                        baudRate=QtSerialPort.QSerialPort.Baud4800,
                        readyRead=self.receive,
                    )
                    self.arduino.open(QIODevice.ReadWrite)
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
            text = self.arduino.readLine().data().decode()
            text = text.rstrip("\r\n")
            self.logReceive = text
            #self.logConsole.append(text)
            if text:
                self.updateGauges(text)
        else:
            self.serialTimer.start()

    def updateGauges(self, data: str):
        if data[0] == "T":
            temp = float(data[1:])
            txt = gaugeHtml.format(gaugeName=u"Température", value=temp, unity=u" °C")
            self.temperatureGauge.setHtml(txt)
        elif data[0] == "P":
            pressure = float(data[1:])
            txt = gaugeHtml.format(gaugeName=u"Pression", value=pressure, unity=u" BAR")
            self.pressureGauge.setText(txt)
        elif data[0] == "R":
            txt = gaugeHtml.format(
                gaugeName=u"Vitesse de rotation", value=data[1:], unity=u" RPM"
            )
            self.rpmGauge.setText(txt)
        elif data[0] == "A":
            self.rubberAngleGauge.setValue(int(data[1:]))
        elif data[0] == "W":
            self.alarmsManager(data[1:])
        else:
            text = "UNKNOW DATA : " + str(data)
            self.logReceive = text

    def ligthsButtonsClicked(self):
        if self.bowLightButton.isChecked():
            self.arduino.write("1".encode("utf-8"))
            self.bowLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("2".encode("utf-8"))
            self.bowLightButton.setStyleSheet("")
        if self.bordLightButton.isChecked():
            self.arduino.write("3".encode("utf-8"))
            self.bordLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("4".encode("utf-8"))
            self.bordLightButton.setStyleSheet("")
        if self.starbordLightButton.isChecked():
            self.arduino.write("5".encode("utf-8"))
            self.starbordLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("6".encode("utf-8"))
            self.starbordLightButton.setStyleSheet("")
        if self.sternLightButton.isChecked():
            self.arduino.write("7".encode("utf-8"))
            self.sternLightButton.setStyleSheet(stylesheet[2])
        else:
            self.arduino.write("8".encode("utf-8"))
            self.sternLightButton.setStyleSheet("")

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

    def alarmButtonClicked(self):
        if self.alarmState == True:
            self.arduino.write("A".encode("utf-8"))
            self.alarmState = False
            self.logConsole.setStyleSheet(stylesheet[3])
            self.alarmButton.setText(u"Tester\nAlarme")
        else:
            self.arduino.write("B".encode("utf-8"))
            self.alarmButton.setText(u"Effacer\nAlarme")
            self.logConsole.setStyleSheet(stylesheet[1])

    def alarmsManager(self, alarm: str):
        alarmState = int(alarm[0])
        alarmId = int(alarm[1:])
        print(alarmState,alarmId)
        if alarmId == 0:
            if alarmState:
                pass
                #self.logConsole.append(u"ALARME 0")
            else:
                pass
                #self.logConsole.append(u"PAS D'ALARME")
            #if alarmState:
            #    self.logConsole.setStyleSheet(stylesheet[3])
            #    self.alarmButton.setText(u"Tester\nAlarme")
        elif alarmId == 1:
            if alarmState:
                self.tempAlarm = True
                self.temperatureGauge.setStyleSheet(stylesheet[1])
            else:
                self.tempAlarm = False
                self.temperatureGauge.setStyleSheet(stylesheet[3])
        elif alarmId == 2:
            if alarmState:
                self.pressureAlarm = True
                self.pressureGauge.setStyleSheet(stylesheet[1])
            else:
                self.pressureAlarm = False
                self.pressureGauge.setStyleSheet(stylesheet[3])
        elif alarmId == 3:
            if alarmState:
                self.alternatorAlarm = True
                self.textEdit_Battery.setStyleSheet(stylesheet[1])
            else:
                self.alternatorAlarm = False
                self.textEdit_Battery.setStyleSheet(stylesheet[3])
        elif alarmId == 4:
            if alarmState:
                self.lowBatteryAlarm = True
                self.textEdit_Battery.setStyleSheet(stylesheet[1])
            else:
                self.lowBatteryAlarm = False
                self.textEdit_Battery.setStyleSheet(stylesheet[3])
        elif alarmId == 5:
            if alarmState:
                self.bowAlarm = True
                self.bowLightButton.setStyleSheet(stylesheet[1])
            else:
                self.bowAlarm = False
                self.bowLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 6:
            if alarmState:
                self.portAlarm = True
                self.bordLightButton.setStyleSheet(stylesheet[1])
            else:
                self.portAlarm = False
                self.bordLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 7:
            if alarmState:
                self.starbordAlarm = True
                self.starbordLightButton.setStyleSheet(stylesheet[1])
            else:
                self.starbordAlarm = False
                self.starbordLightButton.setStyleSheet(stylesheet[3])
        elif alarmId == 8:
            if alarmState:
                self.sternAlarm = True
                self.sternLightButton.setStyleSheet(stylesheet[1])
            else:
                self.sternAlarm = False
                self.sternLightButton.setStyleSheet(stylesheet[3])
        else:
            pass

        alarmList = [
            0,
            self.tempAlarm,
            self.pressureAlarm,
            self.alternatorAlarm,
            self.lowBatteryAlarm,
            self.bowAlarm,
            self.portAlarm,
            self.starbordAlarm,
            self.sternAlarm,
            ]
        if True in alarmList:
            #print("there is at least ONE alarm active")
            self.alarmState = True
            #self.arduino.write("B".encode("utf-8"))
            self.logConsole.setStyleSheet(stylesheet[1])
        else:
            #print("there is NO alarm active")
            self.alarmState = False
            self.arduino.write("A".encode("utf-8"))
            self.logConsole.setStyleSheet(stylesheet[3])

    def updateLogConsole(self):
        msg = """<html><head/><body>
    <p><span style=" font-size:12pt;">Connection série : """
        
        msg += self.portDevice
        msg += "</span></p>"

        msg += """<p><span style=" font-size:12pt;">Alarmes en cours :</span><ul>"""
        if self.alarmState == False:
            msg += "<li>Pas d'alarmes en cours</li>"
        else:
            if self.tempAlarm:
                msg += "<li>ALARME TEMPÉRATURE</li>"
            if self.pressureAlarm:
                msg += "<li>ALARME PRESSION HUILE</li>"
            if self.alternatorAlarm:
                msg += "<li>ALARME ALTERNATEUR</li>"
            if self.lowBatteryAlarm:
                msg += "<li>ALARME BATTERIE FAIBLE</li>"
            if self.bowAlarm:
                msg += "<li>ALARME FEUX NAVIGATION PROUE</li>"
            if self.portAlarm:
                msg += "<li>ALARME FEUX NAVIGATION BABORD</li>"
            if self.starbordAlarm:
                msg += "<li>ALARME FEUX NAVIGATION TRIBORD</li>"
            if self.sternAlarm:
                msg += "<li>ALARME FEUX NAVIGATION POUPE</li>"
        msg += "</ul></p>"
        msg += """<p><span style=" font-size:12pt;">Logs : {log}</span></p></body></html>""".format(log = self.logReceive)

        #<p><span style=" font-size:18pt;">{alarm}</span></p>
        self.logConsole.setText(msg)

        #<p><span style=" font-size:12pt;">Logs : {log}</span></p>


if __name__ == "__main__":
    app = QApplication(sys.argv)
    board = Dashboard("BoardOnBoat.ui")
    sys.exit(app.exec_())
