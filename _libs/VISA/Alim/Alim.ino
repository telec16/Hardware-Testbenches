#include <Encoder.h>
#include <LiquidCrystal.h>
#include <MCP4922.h>
#include <SPI.h>


#define IDN "CALY_TECH,Alim0_1500V,002,v2.0\n"
#define RAMPE_CMD_STR ":VOLT:RAMPE:AUTO"
#define OUTPUT_VOLTAGE_CMD_STR ":VOLT:OUT"
#define ENABLE_OUTPUT_RELAY_CMD_STR ":RELA:OUT"
#define ENABLE_INPUT_RELAY_CMD_STR ":RELA:IN"
#define MEASURE_VOLTAGE_CMD_STR ":MEAS:VOLT?"
#define RAMPE_MANUEL_CMD_STR ":VOLT:RAMPE:MANU"

#define CS 9
#define Relay 2
#define Rearme 14
#define Desarme 15
#define BP 16

unsigned long pressed_time = 0;
unsigned long current_time = 0;
unsigned long elapsed_time = 0;
char btn_etat;
int corrected_value;
bool moi = true;


LiquidCrystal monEcran(8,7,6,5,4,3);
MCP4922 DAC(11,13,10,5);    // (MOSI,SCK,CS,LDAC) define Connections for UNO_board, 


void setup()
{ 
  Serial.begin(9600);
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setClockDivider(SPI_CLOCK_DIV4);
  pinMode(CS, OUTPUT);
  pinMode(Relay, OUTPUT);
  pinMode(Rearme, INPUT);
  pinMode(Desarme, INPUT);
  digitalWrite(CS, HIGH);
  digitalWrite(Relay, LOW);
  digitalWrite(Rearme, LOW);
  digitalWrite(Desarme, LOW);
  monEcran.begin(16,2);
  monEcran.clear();
  monEcran.print("Tension :");
  DAC.Set(0,0);
}

void loop()
{
  
  serial_event();
  //btn_relay();
  afficheLCD();
  
}


void rampeAuto(float final_voltage, int nb_step, int step_time)
{
  float tampon = final_voltage*(4095/5);
  int nb_bit_max = ceil(tampon);
  int nb_bit = 0;
  int pas = nb_bit_max/nb_step;
  DAC.Set(0,0);
  while(nb_bit<nb_bit_max)
  {
    DAC.Set(nb_bit,nb_bit);
    nb_bit+=pas;
    delay(step_time);
  }
  DAC.Set(nb_bit_max,nb_bit_max);
  delay(step_time);
  DAC.Set(0,0); 
}

void rampeManu(float increment)
{
  int nb_bit = round((increment/5)*4095);
  DAC.Set(nb_bit,nb_bit);
}

void setOutputVoltage(float final_voltage, int HV_voltage) //fonction permettant de 
{
  if(HV_voltage == 0)
  {
    DAC.Set(0,0);
    rearmeRelay();
    delay(200);
  }
  else {
    float tampon = final_voltage*(4095/5);
    int nb_bit_max = ceil(tampon);
    DAC.Set(0,0);
    delay(150);
    DAC.Set(nb_bit_max, nb_bit_max);
    rearmeRelay();
    afficheLCD();
    delay(200);
    if(HV_voltage+5.0 < corrected_value < HV_voltage-5.0 )
    {
      int diff = abs(HV_voltage - corrected_value);
      int diff_bit = ceil((diff/1475.0)*4095.0);
      if(corrected_value < HV_voltage)
      {
        DAC.Set(nb_bit_max + diff_bit ,nb_bit_max + diff_bit);
      }
      if(corrected_value > HV_voltage)
      {
        DAC.Set(nb_bit_max - diff_bit ,nb_bit_max - diff_bit);
      }
    }
  }  
}

void serial_event()
{
  if (Serial.available()) 
  {
    String cmd = Serial.readStringUntil('\n');

    //Identification command
    if(cmd[0] == '*')
    {
      if(cmd.indexOf("IDN?") >= 0)
      {
        Serial.print(IDN);
      }
      else{
        Serial.print("\n");
      }
    }
    if(cmd[0] == ':')
    {
      String str_final_voltage, str_nb_step, str_step_time, str_output_voltage, str_step_voltage;

      if(cmd.indexOf(RAMPE_CMD_STR) == 0)
      {
        str_final_voltage = cmd.substring(cmd.indexOf(",")+1);
        int HV_voltage = str_final_voltage.toInt();
        float final_voltage = HV_voltage/309.2; 
        str_nb_step = cmd.substring(cmd.indexOf(";")+1);
        int nb_step = str_nb_step.toInt();
        str_step_time = cmd.substring(cmd.indexOf("/")+1);
        int step_time = str_step_time.toInt();
        rampeAuto(final_voltage, nb_step, step_time);
      }
      else if(cmd.indexOf(RAMPE_MANUEL_CMD_STR) == 0)
      {
        str_step_voltage = cmd.substring(cmd.indexOf(",")+1);
        int step_voltage = str_step_voltage.toInt();
        float DAC_step_voltage = (step_voltage+11.2)/319.9;
        rampeManu(DAC_step_voltage);
      }
      else if(cmd.indexOf(OUTPUT_VOLTAGE_CMD_STR) == 0)
      {
        str_output_voltage = cmd.substring(cmd.indexOf(",")+1);
        int HV_output_voltage = str_output_voltage.toInt();
        float DAC_output_voltage = (HV_output_voltage+11.2)/319.9;
        desarmeRelay();
        setOutputVoltage(DAC_output_voltage, HV_output_voltage);
      }
      else if(cmd.indexOf(ENABLE_OUTPUT_RELAY_CMD_STR) == 0)
      {
        int on = cmd.substring(strlen(ENABLE_OUTPUT_RELAY_CMD_STR)).toInt();
        digitalWrite(Relay, on);
      }
      else if(cmd.indexOf(MEASURE_VOLTAGE_CMD_STR) == 0)
      {
        short sense_value = read();
        int HV_value = (sense_value/4095.0)*1500.0;
        int true_value = (HV_value+0.3718)/1.0105;
        //String str_value = String(true_value);
        Serial.println(true_value, DEC);
      }
      else if(cmd.substring(strlen(ENABLE_INPUT_RELAY_CMD_STR) == 0))
      {
        int on = cmd.substring(strlen(ENABLE_INPUT_RELAY_CMD_STR)).toInt();
        if(on == LOW){
          desarmeRelay();
        }
        if(on == HIGH){
          rearmeRelay();
        }
      }
    }
  }
}

void desarmeRelay()
{
  pinMode(Desarme, OUTPUT);
  digitalWrite(Desarme, HIGH);
  delay(250);
  pinMode(Desarme, INPUT);
  digitalWrite(Desarme, LOW);
}

void rearmeRelay()
{
  pinMode(Rearme, OUTPUT);
  digitalWrite(Rearme, LOW);
  delay(250);
  pinMode(Rearme, INPUT);
  digitalWrite(Rearme, LOW);
}

short read()
{
    short val;
    short result;
    byte inByte;
    digitalWrite(CS, LOW);  // activer echange
    val = SPI.transfer(0x00);  // recuperer octet MSB
    val = val << 8;  // decaler pour mettre en MSB
    inByte = SPI.transfer(0x00);  // recuperer octet LSB
    val = val | inByte;  // assembler MSB et LSB
    digitalWrite(CS, HIGH);  // desactiver echange
    val = val >> 1;    // eliminer lsb
    result = val & 0xFFF;  // conserver les 12 bits
    return result;
    
}

void afficheLCD()
{
  monEcran.clear();
  monEcran.print("Tension :"); 
  short sense_value = read(); //lecture du nombre de bit de l'ADC
  int HV_value = (sense_value/4095.0)*1500.0; //conversion "grossière" du nombre de bit en tension
  corrected_value = (HV_value+0.3718)/1.0105; //calibration de l'ADC pour avoir une meilleure précision
  monEcran.setCursor(0,1);
  monEcran.print(corrected_value);
  delay(150);
}


void btn_relay() {
  if (digitalRead(BP) == LOW){
    btn_etat = LOW;
    current_time = millis();
    while (digitalRead(BP) == LOW) {
      pressed_time = millis();
    }
    int x = current_time;
    int y = pressed_time;
    elapsed_time = y - x;
    if (elapsed_time < 450 && digitalRead(Relay) == LOW && btn_etat == LOW){
      digitalWrite(Relay, HIGH);
      btn_etat = HIGH;
      delay(250);
    }
    if (elapsed_time < 450 && digitalRead(Relay) == HIGH && btn_etat == LOW){
      digitalWrite(Relay, LOW);
      btn_etat = HIGH;
      delay(250);
    }
    if (elapsed_time > 450 && analogRead(A0) > 160 && analogRead(A1) > 160 && btn_etat == LOW) {
      pinMode(Rearme, OUTPUT);
      digitalWrite(Rearme, LOW);
      delay(250);
      btn_etat = HIGH;
      pinMode(Rearme, INPUT);
      digitalWrite(Rearme, LOW);
    }
    if (elapsed_time > 450 && analogRead(A1) < 20 && analogRead(A0) > 140 && btn_etat == LOW) {
      pinMode(Desarme, OUTPUT);
      digitalWrite(Desarme, HIGH);
      delay(250);
      btn_etat = HIGH;
      pinMode(Desarme, INPUT);
      digitalWrite(Desarme, LOW);
    }
  }
}
