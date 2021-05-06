// Board On Boat

// Init
const int baudRate = 9600; //constant integer to set the baud rate for serial monitor

// IN
// ANALOG
const char ThermistorPin = A0;
const char RudderAnglePin = A1;
const char PressurePin = A2;
const char pin_capteur_volt = A3;
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
float _rudder = 0;
float _volt = 0;

//Pour les temporisations
const unsigned long _periodWriting = 1000;
unsigned long _lastConsoWriting = 0;

const unsigned long _periodCheckTemp = 1000;
unsigned long _lastCheckTemp = 0;

const unsigned long _periodCheckPressure = 1000;
unsigned long _lastCheckPressure = 0;

const unsigned long _periodCheckRudder = 250;
unsigned long _lastCheckRudder = 0;

const unsigned long _periodCheckLights = 1000;
unsigned long _lastCheckLights = 0;

const unsigned long _periodCheckVolt = 1000;
unsigned long _lastCheckVolt = 0;

// void alarmControl();
int readRPM();
float readTemperature();
int readPressure();
void lightsCheck();
float readRudderAngle();
void lightsCheckControl2();
float readVoltage();


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
        Serial.println("W1BOW");
    }
    else {
        Serial.println("W0BOW");
    }
    if (digitalRead(PortLightPin) == HIGH) {
        Serial.println("W1PORT");
    }
    else {
        Serial.println("W0PORT");
    }
    if (digitalRead(StarbordLightPin) == HIGH) {
        Serial.println("W1STAR");
    }
    else {
        Serial.println("W0STAR");
    }
    if (digitalRead(SternLightPin) == HIGH) {
        Serial.println("W1STERN");
    }
    else {
        Serial.println("W0STERN");
    }
}

void lightsCheckControl2() {
    if ((digitalRead(RelayBowLight) == HIGH) && (digitalRead(BowLightPin)) == LOW) {
        Serial.println("W1BOW");
    }
    else {
        Serial.println("W0BOW");
    }
    if ((digitalRead(RelayPortLight) == HIGH) && (digitalRead(PortLightPin)) == LOW) {
        Serial.print("W1PORT");
    }
    else {
        Serial.println("W0PORT");
    }
    if ((digitalRead(RelayStarbordLight) == HIGH) && (digitalRead(StarbordLightPin)) == LOW) {
        Serial.println("W1STAR");
    }
    else {
        Serial.println("W0STAR");
    }
    if ((digitalRead(RelaySternLight) == HIGH) && (digitalRead(SternLightPin)) == LOW) {
        Serial.println("W1STERN");
    }
    else {
        Serial.println("W0STERN");
    }
}

// Rudder angle Control
float readRudderAngle() {
    float rudder = analogRead(RudderAnglePin);
    return rudder / (float)5.683333333 - (float)90;
}

// Read Voltage
float readVoltage(){
  float valeur_capteur = analogRead(pin_capteur_volt);
  return (float)0.0293255131 * valeur_capteur;
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

    _rpm = readRPM();
    _temp = readTemperature();
    _rudder = readRudderAngle();
    _pressure = readPressure();
    _volt = readVoltage();

}

// Setup loop
void loop() {
    // COMMANDS
    //Serial.println(Serial.available());
    if(Serial.available() > 0) {
        //byte command = 0;
		int command = Serial.read();
        //Serial.print("COM");
        //Serial.println(command);
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
            digitalWrite(RelayAlarm,LOW);
            break;
        case 66 : //"B" ON ALARME
            digitalWrite(RelayAlarm,HIGH);
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
        Serial.print("R");
        Serial.println(_rpm);
    }

    if(millis() - _lastCheckTemp >= _periodCheckTemp){
        _lastCheckTemp += _periodCheckTemp;
        _temp = readTemperature();
        Serial.print("T");
        Serial.println(_temp);
    }

    if(millis() - _lastCheckRudder >= _periodCheckRudder){
        _lastCheckRudder += _periodCheckRudder;
        _rudder = readRudderAngle();
        Serial.print("A");
        Serial.println(_rudder);
    }    

    if(millis() - _lastCheckPressure >= _periodCheckPressure){
        _lastCheckPressure += _periodCheckPressure;
        _pressure = readPressure();
        Serial.print("P");
        Serial.println(_pressure);
    }

    if(millis() - _lastCheckLights >= _periodCheckLights){
        _lastCheckLights+= _periodCheckLights;
        lightsCheckControl2();
    }

    if(millis() - _lastCheckVolt >= _periodCheckVolt){
        _lastCheckVolt+= _periodCheckVolt;
        _volt = readVoltage();
        Serial.print("V");
        Serial.println(_volt);
    }

}
