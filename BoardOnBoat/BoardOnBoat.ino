// Board On Boat

// Init
const int baudRate = 9600; //constant integer to set the baud rate for serial monitor

// IN
// ANALOG
const char ThermistorPin = A0;
const char RudderAnglePin = A1;
const char PressurePin = A2;
// DIGITAL
const int BowLightPin = 8;
const int PortLightPin = 9;
const int StarbordLightPin = 10;
const int SternLightPin = 11;

// Out
const int RelayBowLight = 2; // Bow
const int RelayPortLight = 3; // Port
const int RelayStarbordLight = 4; // Starbord
const int RelaySternLight = 5; // Stern
const int RelayHorn = 6; // Horn
const int RelayAlarm = 7; // Alarm

//Regime moteur temps reel en tour par minute
int _rpm = 0;
//temperature of the engine coude d'echappement en degre celsius
float _temp;
//oil pressure of the engine
int _pressure = 0;
int _rudder = 0;

//Pour les temporisations
const unsigned long _periodWriting = 1000;
unsigned long _lastConsoWriting = 0;

const unsigned long _periodCheckTemp = 900;
unsigned long _lastCheckTemp = 0;

const unsigned long _periodCheckPressure = 800;
unsigned long _lastCheckPressure = 0;

const unsigned long _periodCheckRudder = 700;
unsigned long _lastCheckRudder = 0;

void alarmControl();
int readRPM();
float readTemperature();
int readPressure();
void lightsCheck();
int readRudderAngle();


// Alarm control
boolean alarmState = 0;
int alarmID = 0;
void alarmControl(boolean alarmState, int alarmID) {
    if (alarmState==1) {
        digitalWrite(RelayAlarm,HIGH);
    }
    else { 
        digitalWrite(RelayAlarm,LOW);
    }  
    Serial.print("W");
    Serial.print(alarmState);
    Serial.println(alarmID);
}

// RPM Control
//Cette fonction permet de retourner le regime moteur.
//0 si le moteur est eteint.
//Attention, cette fonction dure 100ms au moins ...
//Pin digitale num 2, donc il y  a la possibilite de gerer les impulsions par interruption si jamais on veut changer.
const int inpinrpm = 12;

//Constante empirique permettant de calculer les RPM en fonction de la frequence du rupteur :
//RPM = ALPHA_RPM * freq_rupteur
//Pour mon moteur Nanni N3.30, cette constante vaut 6.51
const float ALPHA_RPM = (float)6.51;


int readRPM(){
    float f = 0;
    float durationPulseLOW = 0;
    float durationPulseHIGH = 0;
    unsigned long beginning = millis();
    unsigned long nowMillis = millis();

    while(nowMillis - beginning < (unsigned long)100){
        durationPulseLOW += pulseIn(inpinrpm, LOW, (unsigned long)100000);
        durationPulseHIGH += pulseIn(inpinrpm, HIGH, (unsigned long)100000);
        f = f + (float)1;
        nowMillis = millis();
    }

    //Calcul de la duree moyenne d'une pulsation LOW et HIGH en seconde
    //Calcul de la duree moyenne d'une pulsation LOW et HIGH en seconde
    durationPulseLOW /= (f * (float)1000000);
    durationPulseHIGH /= (f * (float)1000000);


    if(durationPulseLOW == 0 || durationPulseHIGH == 0){
        return 0;
    }
    else{
        //Calcul de la frequence en Hz en faisant l'inverse de la periode egale a la somme des durees des pulsations HIGH et LOW
        f = (float)1/ (durationPulseLOW + durationPulseHIGH);
        //Le 6.51 a ete calcule de facon empirique.
        float rpm = (float)f * ALPHA_RPM;

        //En utilisant la formule trouver sur sonelec, nous aurions :
        //float rpm = f * (float)40
        //On arrondi a l'entier le plus proche
        return (int)(rpm + (float)0.5);
    }
}

// Temperature control
//int Vo;
float R1 = 10000;
float logR2, R2, T;
float c1 = 1.009249522e-03, c2 = 2.378405444e-04, c3 = 2.019202697e-07;
float readTemperature() {
    // Temperature
    int Vo = analogRead(ThermistorPin);
    R2 = R1 * (1023.0 / (float)Vo - 1.0);
    logR2 = log(R2);
    T = (1.0 / (c1 + c2*logR2 + c3*logR2*logR2*logR2));
    T = T - 273.15;
    return (float)(T);
}

// Pressure control
const float  Offset = 0.397 ;
float pressureV, pressureP;
int readPressure() {
    //pressureV = analogRead(PressurePin) * 5.00 / 1024;     //Sensor output voltage
    //pressureP = (pressureV - Offset) * 400;             //Calculate water pressure
    pressureP = analogRead(PressurePin);
    _pressure = pressureP;
    return _pressure;
}

//  Lights check control
void lightsCheck() {
    if (digitalRead(BowLightPin) == HIGH) {
        alarmControl(1, 5);
    }
    if (digitalRead(PortLightPin) == HIGH) {
        alarmControl(1, 6);
    }
    if (digitalRead(StarbordLightPin) == HIGH) {
        alarmControl(1, 7);
    }
    if (digitalRead(SternLightPin) == HIGH) {
        alarmControl(1, 8);
    }
}

// Rudder angle Control
int rudder;
int readRudderAngle() {
    rudder = analogRead(RudderAnglePin);
    return ((rudder / ( 1023 / 180)) - 90);
}


// Setup the programm
void setup() {
    //Initialisation of the serial port
    Serial.begin(baudRate);
    
    pinMode(RelayBowLight, OUTPUT);
    pinMode(RelayPortLight, OUTPUT);
    pinMode(RelayStarbordLight, OUTPUT);
    pinMode(RelaySternLight, OUTPUT);
    pinMode(RelayHorn, OUTPUT);
    pinMode(RelayAlarm, OUTPUT);

    //Initialisation of the digital pin
    pinMode(inpinrpm, INPUT);

      //Init of the synchro var
    _lastConsoWriting = millis();
    _lastCheckTemp = _lastConsoWriting;
    _lastCheckPressure = _lastConsoWriting;
    _lastCheckRudder = _lastConsoWriting;
}

// Setup loop
void loop() {
    // COMMANDS
    //Serial.println(Serial.available());
    if(Serial.available() > 0) {
        //byte command = 0;
		int command = Serial.read();
        Serial.print("COM");
        Serial.println(command);
        /**/

        switch (command)
        {
        case 49 :
            digitalWrite(RelayBowLight,HIGH);
            break;
        case 50 :
            digitalWrite(RelayBowLight,LOW);
            break;
        case 51 :
            digitalWrite(RelayPortLight,HIGH);
            break;
        case 52 :
            digitalWrite(RelayPortLight,LOW);
            break;
        case 53 :
            digitalWrite(RelayStarbordLight,HIGH);
            break;
        case 54 :
            digitalWrite(RelayStarbordLight,LOW);
            break;
        case 55 :
            digitalWrite(RelaySternLight,HIGH);
            break;
        case 56 :
            digitalWrite(RelaySternLight,LOW);
            break;
        case 65 : //"A" STOP ALARME
            alarmControl(0, 0);
            break;
        case 66 : //"B" TEST ALARME
            alarmControl(1, 9);
            break;
        case 67 : //"C" TEST LIGHT
            lightsCheck();
            break;
        case 68 : //D
            digitalWrite(RelayHorn,HIGH);
            break;
        case 69 : //E
            digitalWrite(RelayHorn,LOW);
            break;
        }
        /**/
    }
    if(millis() - _lastConsoWriting >= _periodWriting){
        _lastConsoWriting += _periodWriting;
        _rpm = readRPM();
    }

    if(millis() - _lastCheckTemp >= _periodCheckTemp){
        _lastCheckTemp += _periodCheckTemp;
        _temp = readTemperature();
    }

    if(millis() - _lastCheckRudder >= _periodCheckRudder){
        _lastCheckRudder += _periodCheckRudder;
        _rudder = readRudderAngle();
    }    

    if(millis() - _lastCheckPressure >= _periodCheckPressure){
        _lastCheckPressure += _periodCheckPressure;
        _pressure = readPressure();
    }

    Serial.print("R");
    Serial.println(_rpm);

    Serial.print("T");
    Serial.println(_temp);
    if (_temp > 23.0) {
        alarmControl(1, 1);
    }
    else {
        alarmControl(0, 1);
    }

    Serial.print("A");
    Serial.println(_rudder);

    Serial.print("P");
    Serial.println(_pressure);
    if (_pressure < 23.0 && _rpm > 0) {
        alarmControl(1, 2);
    }
    else {
        alarmControl(0, 2);
    }
}
