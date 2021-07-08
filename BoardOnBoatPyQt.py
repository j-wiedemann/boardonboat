# coding: utf-8

import sys
from datetime import datetime
import serial
import serial.tools.list_ports
from statistics import mean


from PyQt5 import uic, QtSerialPort
from PyQt5.QtWidgets import QApplication, QPushButton, QTextEdit, QDial, QLabel, QProgressBar
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

DEBUG = True
DEBUG_ARDUINO_LOGS = False
DEBUG_WINDOW = False

def print_debug(msg):
    if DEBUG == True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(current_time,msg)
        
def print_arduino_log(msg):
    if DEBUG_ARDUINO_LOGS == True:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(current_time,msg)

class Dashboard(QObject):
    def __init__(self, ui_file, parent=None):
        super(Dashboard, self).__init__(parent)

        # get ui file and load it
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.window = uic.loadUi(ui_file)
        ui_file.close()

        if DEBUG_WINDOW:
            self.window.setGeometry(0, 0, 512, 600)
        else:
            self.window.showMaximized()

        # GAUGES
        self.temperatureGauge = self.window.findChild(QTextEdit, "textEdit_Temperature")
        self.pressureGauge = self.window.findChild(QTextEdit, "textEdit_Pressure")
        self.rpmGauge = self.window.findChild(QTextEdit, "textEdit_RPM")
        self.batteryGauge = self.window.findChild(QTextEdit, "textEdit_Battery")
        
        # RUDDER ANGLE INDICATOR
        self.rudderAngleGauge = self.window.findChild(QDial, "rudderAngle")
        self.rudderAngleLabel = self.window.findChild(QLabel, "label_rudderAngle")

        self.barGO = self.window.findChild(QProgressBar, "progressBar_gasoil")

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

        # value list
        self.temperatures = [0] * 15
        self.pressures = [0] * 15
        self.voltages = [0] * 1

        # Serial connecxion to  arduino
        self.portDevice = u"NON CONNECTÉ"
        self.serialTimer = QTimer()
        self.serialTimer.setInterval(2000)
        self.serialTimer.timeout.connect(self.getArduinoSerial)
        self.serialTimer.start()

        # Timer for logconsole
        self.logReceive = ""
        self.logSend = ""
        self.consoleTimer = QTimer()
        self.consoleTimer.setInterval(100)
        self.consoleTimer.timeout.connect(self.updateLogConsole)
        self.consoleTimer.start()

        # Timer for alarm
        #self.logReceive = ""
        self.alarmsManagerTimer = QTimer()
        self.alarmsManagerTimer.setInterval(1000)
        self.alarmsManagerTimer.timeout.connect(self.alarmsManager)
        
        # Show window
        self.window.show()

    def getArduinoSerial(self):
        print_debug(u"getArduinoSerial")
        ports = serial.tools.list_ports.comports(include_links=False)
        if len(ports) > 0:
            device = False
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
                        device = True
                        print_debug(u"Device founded : {}".format(self.portDevice))
                        self.alarmsManagerTimer.start()
                        break
            if not device:
                self.portDevice = u"NON CONNECTÉ"
                print_debug("No device found :(")
        else:
            self.portDevice = u"NON CONNECTÉ"
            print_debug(u"len(ports) < 1 :(")

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
                print_debug(u"cant decode : {}".format(data))
                pass
        else:
            #print_debug(u"cant Read Line")
        #    print_debug(u"serialTimer.start()")
        #    self.serialTimer.start()
            pass

    @pyqtSlot()
    def updateGauges(self, data: str):
        print_arduino_log(data)
        # TEMP
        if data[0] == "T" and len(data) > 1:
            self.temperatures.append(int(float(data[1:])))
            self.temperatures.pop(0)
            temp = int(mean(self.temperatures))
            txt = gaugeHtml.format(gaugeName=u"Température", value=temp, unity=u" °C")
            self.temperatureGauge.setHtml(txt)
            if temp > 100:
                self.alarms["temp"] = True
            else:
                self.alarms["temp"] = False
        
        # Pressure
        elif data[0] == "P" and len(data) > 1:
            self.pressures.append(float(data[1:]))
            self.pressures.pop(0)
            pressure = round(mean(self.pressures), 2)
            txt = gaugeHtml.format(gaugeName=u"Pression", value=pressure, unity=u" BAR")
            self.pressureGauge.setText(txt)
            if pressure < 2.4:
                self.alarms["pressure"] = True
            else:
                self.alarms["pressure"] = False

        
        # RPM
        elif data[0] == "R" and len(data) > 1:
            txt = gaugeHtml.format(
                gaugeName=u"Vitesse de rotation", value=data[1:], unity=u" RPM"
            )
            self.rpmGauge.setText(txt)
        
        # VOLATGE
        elif data[0] == "V" and len(data) > 1:
            #if data[1:].isnumeric():
            self.voltages.append(float(data[1:]))
            self.voltages.pop(0)
            volt = round(mean(self.voltages), 1)
            txt = gaugeHtml.format(gaugeName=u"Voltage", value=volt, unity=u" V")
            self.batteryGauge.setText(txt)
            if volt < 23.5:
                self.alarms['lowBattery'] = True
            else:
                self.alarms['lowBattery'] = False
        
        # RUDDER ANGLE
        elif data[0] == "A" and len(data) > 1:
            self.rudderAngleGauge.setValue(int(float(data[1:])*-1))
            label = "Angle de barre : "
            if float(data[1:]) > 5:
                label += "Tribord {}°".format(int(float(data[1:])))
            elif float(data[1:]) < -5:
                label += "Babord {}°".format(int(float(data[1:])))
            else:
                label += "À l'Axe {}°".format(int(float(data[1:])))
            self.rudderAngleLabel.setText(label)
        
        # ALARME
        elif data[0] == "W" and len(data) > 1:
            state = int(data[1])
            alarm = str(data[2:])
            if alarm == "BOW":
                if state == 0:
                    self.alarms["bowLight"] = False
                else:
                    self.alarms["bowLight"] = True
            if alarm == "PORT":
                if state == 0:
                    self.alarms["portLight"] = False
                else:
                    self.alarms["portLight"] = True
            if alarm == "STAR":
                if state == 0:
                    self.alarms["starbordLight"] = False
                else:
                    self.alarms["starbordLight"] = True
            if alarm == "STERN":
                if state == 0:
                    self.alarms["sternLight"] = False
                else:
                    self.alarms["sternLight"] = True
        
        # CARBURANT
        elif data[0] == "C" and len(data) > 1:
            self.barGO.setValue(int(float(data[1:])))
        
        # OTHER
        else:
            text = "UNKNOW DATA : " + str(data)
            self.logReceive = text

    def ligthsButtonsClicked(self):
        lightsState = [0, 0, 0, 0]
        if self.bowLightButton.isChecked():
            lightsState[0] = 1
            #self.bowLightButton.setStyleSheet(stylesheet[2])
            self.arduino.write("1".encode("utf-8"))
            self.logSend = "1"
            self.updateLogConsole()
        else:
            self.arduino.write("2".encode("utf-8"))
            #self.bowLightButton.setStyleSheet("")
            self.logSend = "2"
            self.updateLogConsole()
        if self.bordLightButton.isChecked():
            lightsState[1] = 1
            self.arduino.write("3".encode("utf-8"))
            #self.bordLightButton.setStyleSheet(stylesheet[2])
            self.logSend = "3"
            self.updateLogConsole()
        else:
            self.arduino.write("4".encode("utf-8"))
            #self.bordLightButton.setStyleSheet("")
            self.logSend = "4"
            self.updateLogConsole()
        if self.starbordLightButton.isChecked():
            lightsState[2] = 1
            self.arduino.write("5".encode("utf-8"))
            #self.starbordLightButton.setStyleSheet(stylesheet[2])
            self.logSend = "5"
            self.updateLogConsole()
        else:
            self.arduino.write("6".encode("utf-8"))
            #self.starbordLightButton.setStyleSheet("")
            self.logSend = "6"
            self.updateLogConsole()
        if self.sternLightButton.isChecked():
            lightsState[3] = 1
            self.arduino.write("7".encode("utf-8"))
            #self.sternLightButton.setStyleSheet(stylesheet[2])
            self.logSend = "7"
            self.updateLogConsole()
        else:
            self.arduino.write("8".encode("utf-8"))
            #self.sternLightButton.setStyleSheet("")
            self.logSend = "8"
            self.updateLogConsole()
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
        self.logSend = "C"
        self.updateLogConsole()

    def shortHornButtonPressed(self):
        QTimer.singleShot(1000, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))
        self.logSend = "D"
        self.updateLogConsole()

    def longHornButtonPressed(self):
        QTimer.singleShot(4000, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))
        self.logSend = "D"
        self.updateLogConsole()

    def veryshortHornButtonPressed(self):
        QTimer.singleShot(500, self.horn_stop)
        self.arduino.write("D".encode("utf-8"))
        self.logSend = "D"
        self.updateLogConsole()

    def horn_stop(self):
        self.arduino.write("E".encode("utf-8"))
        self.logSend = "E"
        self.updateLogConsole()

    def alarmTestButtonClicked(self):
        if self.alarms["test"] == False:
            self.alarms["test"] = True
        else:
            self.alarms["test"] = False

    def alarmsManager(self):
        if all(value == False for value in self.alarms.values()):
            self.arduino.write("A".encode("utf-8"))
            self.logSend = "A"
            self.updateLogConsole()
        else:
            self.arduino.write("B".encode("utf-8"))
            self.logSend = "B"
            self.updateLogConsole()
        if self.alarms["temp"] == True:
            self.temperatureGauge.setStyleSheet(stylesheet[1])
        else:
            self.temperatureGauge.setStyleSheet(stylesheet[3])
        if self.alarms["pressure"] == True:
            self.pressureGauge.setStyleSheet(stylesheet[1])
        else:
            self.pressureGauge.setStyleSheet(stylesheet[3])

        if self.alarms['lowBattery'] == False:
            self.batteryGauge.setStyleSheet(stylesheet[3])
        else:
            self.batteryGauge.setStyleSheet(stylesheet[1])
        if self.alarms["bowLight"] == False:
            self.bowLightButton.setStyleSheet(stylesheet[3])
        else:
            self.bowLightButton.setStyleSheet(stylesheet[1])
        if self.alarms["portLight"] == False:
            self.bordLightButton.setStyleSheet(stylesheet[3])
        else:
            self.bordLightButton.setStyleSheet(stylesheet[1])
        if self.alarms["starbordLight"] == False:
            self.starbordLightButton.setStyleSheet(stylesheet[3])
        else:
            self.starbordLightButton.setStyleSheet(stylesheet[1])
        if self.alarms["sternLight"] == False:
            self.sternLightButton.setStyleSheet(stylesheet[3])
        else:
            self.sternLightButton.setStyleSheet(stylesheet[1])


        """    
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
            print_debug("Alarm is OFF and have to be ON")
            print_debug(str(self.alarms))
            self.arduino.write("B".encode("utf-8"))
        elif (wasTrue == True) and (not True in self.alarms.values()):
            print_debug("Alarm is ON and have to be OFF")
            print_debug(str(self.alarms))
            self.arduino.write("A".encode("utf-8"))
        else:
            #print("No changes for ALARM")
            pass
        """

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
                msg += "<li>TEST</li>"
            if self.alarms["temp"]:
                msg += "<li>TEMPÉRATURE</li>"
            if self.alarms["pressure"]:
                msg += "<li>PRESSION HUILE</li>"
            if self.alarms["alternator"]:
                msg += "<li>ALTERNATEUR</li>"
            if self.alarms["lowBattery"]:
                msg += "<li>BATTERIE FAIBLE</li>"
            if self.alarms["bowLight"]:
                msg += "<li>FEUX NAVIGATION PROUE</li>"
            if self.alarms["portLight"]:
                msg += "<li>FEUX NAVIGATION BABORD</li>"
            if self.alarms["starbordLight"]:
                msg += "<li>FEUX NAVIGATION TRIBORD</li>"
            if self.alarms["sternLight"]:
                msg += "<li>FEUX NAVIGATION POUPE</li>"
        msg += "</ul></p>"
        msg += """<p><span style=" font-size:12pt;">Logs : <ul><li>RX : {rx}</li><li>TX : {tx}</li></ul></span></p></body></html>""".format(rx = self.logReceive, tx = self.logSend)

        self.logConsole.setText(msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    board = Dashboard("BoardOnBoat.ui")
    sys.exit(app.exec_())
