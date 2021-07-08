// Board On Boat

// Init
const int baudRate = 9600; //constant integer to set the baud rate for serial monitor

// ANALOG
const char VoltagePin = A0;
const char ThermistorPin = A1;
const char RudderAnglePin = A2;
const char PressurePin = A3;
//const char FuelTankPin = A4;

// DIGITAL
// IN
const int BowLightPin = 6;
const int PortLightPin = 5;
const int StarboardLightPin = 4;
const int SternLightPin = 3;
const int RPMInPin = 12;
// Out
const int BowLightRelay = 11; // Proue
const int PortLightRelay = 10; // Tribord
const int StarboardLightRelay = 9; // Babord
const int SternLightRelay = 8; // Poupe
const int HornRelay = 7; // Corne de brume
const int AlarmRelay = 12; // Alarme

//Pour les temporisations
const unsigned long _periodCheckRPM = 1000;
unsigned long _lastCheckRPM = 0;

const unsigned long _periodCheckTemp = 2000;
unsigned long _lastCheckTemp = 0;

const unsigned long _periodCheckPressure = 2000;
unsigned long _lastCheckPressure = 0;

const unsigned long _periodCheckRudder = 100;
unsigned long _lastCheckRudder = 0;

const unsigned long _periodCheckLights = 60000;
unsigned long _lastCheckLights = 0;

const unsigned long _periodCheckVolt = 2000;
unsigned long _lastCheckVolt = 0;

// const unsigned long _periodCheckFuel = 60000;
// unsigned long _lastCheckFuel = 0;

// void alarmControl();
int readRPM();
float readTemperature();
int readPressure();
void lightsCheck();
float readRudderAngle();
float readVoltage();


// RPM Control
//Regime moteur temps reel en tour par minute
int _rpm = 0;
//Cette fonction permet de retourner le regime moteur.
//0 si le moteur est eteint.
//Attention, cette fonction dure 100ms au moins ...
//Pin digitale num 2, donc il y  a la possibilite de gerer les impulsions par interruption si jamais on veut changer.

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
        durationPulseLOW += pulseIn(RPMInPin, LOW, (unsigned long)100000);
        durationPulseHIGH += pulseIn(RPMInPin, HIGH, (unsigned long)100000);
        f = f + (float)1;
        nowMillis = millis();
    }

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
//temperature of the engine coude d'echappement en degre celsius
float _temp;
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
//oil pressure of the engine
int _pressure = 0;
const float  Offset = 0.397 ;
float pressureV, pressureP, pressureB;
int readPressure() {
    pressureV = analogRead(PressurePin) * 5.00 / 1024;     //Sensor output voltage
    pressureP = (3.0 * (pressureV - Offset)) * 1000000.0;             //Calculate water pressure
    pressureB = pressureP/10e5;             //Calculate water pressure
    //pressureP = analogRead(PressurePin);

    //Serial.println(pressureB);
    _pressure = pressureB;
    return _pressure;
}

// Rudder angle Control
float _rudder = 0;
float readRudderAngle() {
    float rudder = analogRead(RudderAnglePin);
    return rudder / (float)5.683333333 - (float)90;
}

// Read Voltage
float _volt = 0;
float readVoltage(){
  float valeur_capteur = analogRead(VoltagePin);
  // Serial.println(valeur_capteur);
  return (float)0.029296875 * valeur_capteur;
}

//  Lights check control
void lightsCheck() {
    int state = 0;
    // BOW LIGHT (PROUE)
    if (digitalRead(BowLightRelay) == HIGH) {
        state = 1;
        digitalWrite(BowLightRelay, LOW);
        delay(5);
    }
    if (digitalRead(BowLightPin) == LOW) {
        Serial.println("W0BOW");
    }
    else {
        Serial.println("W1BOW");
        state = 0;
    }
    if (state == 1) {
        digitalWrite(BowLightRelay, HIGH);
        state = 0;
    }
    
    // PORT LIGHT (BABORD)
    if (digitalRead(PortLightRelay) == HIGH) {
        state = 1;
        digitalWrite(PortLightRelay, LOW);
        delay(5);
    }
    if (digitalRead(PortLightPin) == LOW) {
        Serial.println("W0PORT");
    }
    else {
        Serial.println("W1PORT");
    }
    if (state == 1) {
        digitalWrite(PortLightRelay, HIGH);
    }
    state = 0;
    // STARBOARD LIGHT (TRIBORD)
    if (digitalRead(StarboardLightRelay) == HIGH) {
        state = 1;
        digitalWrite(StarboardLightRelay, LOW);
        delay(5);
    }
    if (digitalRead(StarboardLightPin) == LOW) {
        Serial.println("W0STAR");
    }
    else {
        Serial.println("W1STAR");
    }
    if (state == 1) {
        digitalWrite(StarboardLightRelay, HIGH);
    }
    state = 0;
    // STERN LIGHT (POUPE)
    if (digitalRead(SternLightRelay) == HIGH) {
        state = 1;
        digitalWrite(SternLightRelay, LOW);
        delay(5);
    }
    if (digitalRead(SternLightPin) == LOW) {
        Serial.println("W0STERN");
    }
    else {
        Serial.println("W1STERN");
    }
    if (state == 1) {
        digitalWrite(SternLightRelay, HIGH);
    }
    state = 0;
}

// Setup the programm
void setup() {
    //Initialisation of the serial port
    Serial.begin(baudRate);

    //Initialisation of the digital pin
    pinMode(BowLightRelay, OUTPUT);
    pinMode(PortLightRelay, OUTPUT);
    pinMode(StarboardLightRelay, OUTPUT);
    pinMode(SternLightRelay, OUTPUT);
    pinMode(HornRelay, OUTPUT);
    pinMode(AlarmRelay, OUTPUT);
    pinMode(BowLightPin, INPUT);
    pinMode(PortLightPin, INPUT);
    pinMode(StarboardLightPin, INPUT);
    pinMode(SternLightPin, INPUT);
    pinMode(RPMInPin, INPUT);

    //Init of the synchro var
    _lastCheckRPM = millis();
    _lastCheckTemp = millis();
    _lastCheckPressure = millis();
    _lastCheckRudder = millis();
    
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
    if (Serial.available() > 0) {
        //byte command = 0;
		int command = Serial.read();
        //Serial.print("COM");
        //Serial.println(command);
        /**/

        switch (command)
        {
        case 49 :
            digitalWrite(BowLightRelay,HIGH);
            break;
        case 50 :
            digitalWrite(BowLightRelay,LOW);
            break;
        case 51 :
            digitalWrite(PortLightRelay,HIGH);
            break;
        case 52 :
            digitalWrite(PortLightRelay,LOW);
            break;
        case 53 :
            digitalWrite(StarboardLightRelay,HIGH);
            break;
        case 54 :
            digitalWrite(StarboardLightRelay,LOW);
            break;
        case 55 :
            digitalWrite(SternLightRelay,HIGH);
            break;
        case 56 :
            digitalWrite(SternLightRelay,LOW);
            break;
        case 65 : //"A" STOP ALARME
            digitalWrite(AlarmRelay,LOW);
            break;
        case 66 : //"B" ON ALARME
            digitalWrite(AlarmRelay,HIGH);
            break;
        case 67 : //"C" TEST LIGHT
            lightsCheck();
            break;
        case 68 : //D
            digitalWrite(HornRelay,HIGH);
            break;
        case 69 : //E
            digitalWrite(HornRelay,LOW);
            break;
        }
        /**/
    }
    if(millis() - _lastCheckRPM >= _periodCheckRPM){
        _lastCheckRPM += _periodCheckRPM;
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
        // lightsCheck();
    }

    if(millis() - _lastCheckVolt >= _periodCheckVolt){
        _lastCheckVolt+= _periodCheckVolt;
        _volt = readVoltage();
        Serial.print("V");
        Serial.println(_volt);
    }

}
