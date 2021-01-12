#include <Arduino.h>
#include <Wire.h>
#include <MCP342x.h>

/*
    Write:
      - :SURGe dev (device)
      - :HTRB dev,o (device; 1: on, 0: off)
      - :MES dev (device)
      - :READ dev (device)
      - :GAIN g (gain:1,2,4,8)
      - :STOP
      - :RELAy
        - :SURGe dev,o (device; 1: on, 0: off)
        - :HT dev,o (device; 1: on, 0: off)
        - :MES dev,o (device; 1: on, 0: off)
        - :MUX chn (0: none, 1: mes, 2: ht, 3: surge)
      - :BoaRDS
        - :STOP rel (bit0: off mes, bit1: off htrb, bit2 off surge)
      - :LIGHt
        - :ORANge o (1: on, 0: off)
        - :RED o    (1: on, 0: off)
*/

#define IDN "CALY TECH,Carac_test,000001,V1.31\n"
#define SURGE_CMD_STR ":SURG "
#define HTRB_CMD_STR ":HTRB "
#define MES_CMD_STR ":MES "
#define READ_CMD_STR ":READ "
#define GAIN_CMD_STR ":GAIN "
#define STOP_MUX_CMD_STR ":STOP"
#define RELAY_SURGE_CMD_STR ":RELA:SURG "
#define RELAY_HT_CMD_STR ":RELA:HT "
#define RELAY_MES_CMD_STR ":RELA:MES "
#define RELAY_MUX_CMD_STR ":RELA:MUX "
#define STOP_BOARDS_CMD_STR ":BRDS:STOP "
#define ORANGE_CMD_STR ":LIGH:ORAN "
#define RED_CMD_STR ":LIGH:RED "


/* ADC */

const int tmo = 100*1000; //milliseconds
const MCP342x::Channel CHN[4] = { MCP342x::channel1, 
                                  MCP342x::channel2, 
                                  MCP342x::channel3, 
                                  MCP342x::channel4};
MCP342x adcs[4] = {
  MCP342x(0x6E),
  MCP342x(0x68),
  MCP342x(0x6A),
  MCP342x(0x6C)
};

MCP342x::Gain gain = MCP342x::gain1;


/* Pins definition */
#define ORANGE 8
#define RED 9

#define ROWS 7
#define COLUMNS 2
typedef struct {int surge; int ht; int mes; int adc; int chn;} cardPin_t;
const cardPin_t pins[ROWS][COLUMNS] = {
  {{.surge=22, .ht=24, .mes=26, .adc=0, .chn=1}, {.surge=23, .ht=25, .mes=27, .adc=0, .chn=2}},
  {{.surge=28, .ht=30, .mes=32, .adc=1, .chn=1}, {.surge=29, .ht=31, .mes=33, .adc=1, .chn=2}},
  {{.surge=34, .ht=36, .mes=38, .adc=1, .chn=3}, {.surge=35, .ht=37, .mes=39, .adc=1, .chn=4}},
  {{.surge=40, .ht=42, .mes=44, .adc=2, .chn=1}, {.surge=41, .ht=43, .mes=45, .adc=2, .chn=2}},
  {{.surge=46, .ht=48, .mes=50, .adc=2, .chn=3}, {.surge=47, .ht=49, .mes=51, .adc=2, .chn=4}},
  {{.surge=A12,.ht=A11,.mes=A10,.adc=3, .chn=1}, {.surge=A15,.ht=A14,.mes=A13,.adc=3, .chn=2}},
  {{.surge=A9, .ht=A8, .mes=A7, .adc=3, .chn=3}, {.surge=A6, .ht=A5, .mes=A4, .adc=3, .chn=4}}
};

#define MASTER_SURGE 4
#define MASTER_MES 3
#define MASTER_HT 2


typedef enum {MUX_NONE=0, MUX_SURGE=MASTER_SURGE, MUX_HT=MASTER_HT, MUX_MES=MASTER_MES} mux_t;


#define DELAY_BETWEEN_CLICK 750
#define NO_FLAG 255

cardPin_t currentCard;
mux_t currentMux = MUX_NONE;
volatile bool htrb_on = false;
volatile int mux_flag = NO_FLAG;
volatile int read_flag = NO_FLAG;
volatile int gain_flag = NO_FLAG;
volatile int relay_surge_flag = NO_FLAG;
volatile int relay_ht_flag = NO_FLAG;
volatile int relay_mes_flag = NO_FLAG;
volatile int relay_mux_flag = NO_FLAG;
volatile int relay_stop_flag = NO_FLAG;


void serial_event();
void init_devices();

void selectMux(mux_t m);
void sequenceSurge(cardPin_t cardPin);
void sequenceHTRB(cardPin_t cardPin, bool on);
void sequenceMes(cardPin_t cardPin);

void closeAllSurge();
void closeAllHt();
void closeAllMes();


void setup() {
  Serial.begin(9600);
  Wire.begin();
  
  // Reset devices
  MCP342x::generalCallReset();
  delay(1); // MC342x needs 300us to settle, wait 1ms
  
  pinMode(ORANGE, OUTPUT);
  pinMode(RED, OUTPUT);
  digitalWrite(ORANGE, HIGH);
  digitalWrite(RED, HIGH);

  init_devices();
}

void loop(){
  serial_event();

  switch(mux_flag){
    case MUX_SURGE:
      sequenceSurge(currentCard);
      break;
    case MUX_HT:
      sequenceHTRB(currentCard, htrb_on);
      break;
    case MUX_MES:
      sequenceMes(currentCard);
      break;
    case MUX_NONE:
      selectMux(MUX_NONE);
	    closeAllHt();
	    closeAllMes();
	    closeAllSurge();
      break;
  }
  mux_flag=NO_FLAG;

  if(relay_surge_flag != NO_FLAG){
    digitalWrite(currentCard.surge, relay_surge_flag);
    relay_surge_flag=NO_FLAG;
  }
  if(relay_ht_flag != NO_FLAG){
    digitalWrite(currentCard.ht, relay_ht_flag);
    relay_ht_flag=NO_FLAG;
  }
  if(relay_mes_flag != NO_FLAG){
    digitalWrite(currentCard.mes, relay_mes_flag);
    relay_mes_flag=NO_FLAG;
  }

  if(relay_mux_flag != NO_FLAG){
    if(relay_mux_flag == 0) selectMux(MUX_NONE);
    if(relay_mux_flag == 1) selectMux(MUX_MES);
    if(relay_mux_flag == 2) selectMux(MUX_HT);
    if(relay_mux_flag == 3) selectMux(MUX_SURGE);
    relay_mux_flag=NO_FLAG;
  }
  
  if(relay_stop_flag != NO_FLAG){
    if(relay_stop_flag & 0b100) closeAllSurge();
    if(relay_stop_flag & 0b010) closeAllHt();
    if(relay_stop_flag & 0b001) closeAllMes();
    relay_stop_flag=NO_FLAG;
  }

  if(read_flag != NO_FLAG){
    MCP342x a = adcs[currentCard.adc];
    MCP342x::Channel c = CHN[currentCard.chn-1];
    long value = 0;
    MCP342x::Config status;
    uint8_t err = a.convertAndRead(c, MCP342x::oneShot, MCP342x::resolution16, gain, tmo, value, status);
    if (err)
      Serial.println("-1,-1");
    else
      Serial.println(String(value) + "," + String(value * 2.048 / 32768 / int(gain), 6) + "V");
    read_flag = NO_FLAG;
  }

  if(gain_flag != NO_FLAG){
    switch(gain_flag){
        case 1:
            gain = MCP342x::gain1;
            break;
        case 2:
            gain = MCP342x::gain2;
            break;
        case 4:
            gain = MCP342x::gain4;
            break;
        case 8:
            gain = MCP342x::gain8;
            break;
    }
    Serial.println(String(int(gain)));
    gain_flag = NO_FLAG;
  }
}


void init_devices(){
  pinMode(MASTER_SURGE, OUTPUT);
  pinMode(MASTER_HT, OUTPUT);
  pinMode(MASTER_MES, OUTPUT);
  digitalWrite(MASTER_SURGE, LOW);
  digitalWrite(MASTER_HT, LOW);
  digitalWrite(MASTER_MES, LOW);

  for(int x=0; x<ROWS; x++){
    for(int y=0; y<COLUMNS; y++){
      pinMode(pins[x][y].surge, OUTPUT);
      digitalWrite(pins[x][y].surge, LOW);
      pinMode(pins[x][y].ht, OUTPUT);
      digitalWrite(pins[x][y].ht, LOW);
      pinMode(pins[x][y].mes, OUTPUT);
      digitalWrite(pins[x][y].mes, LOW);
    }
  }
}

void sequenceSurge(cardPin_t cardPin){
  if(currentMux != MUX_SURGE) selectMux(MUX_NONE);

  closeAllHt();
  closeAllMes();
  closeAllSurge();
  delay(DELAY_BETWEEN_CLICK);

  digitalWrite(cardPin.surge, HIGH);
  digitalWrite(cardPin.mes, HIGH);

  if(currentMux != MUX_SURGE) selectMux(MUX_SURGE);
}
void sequenceHTRB(cardPin_t cardPin, bool on){
  if(currentMux != MUX_HT){
    selectMux(MUX_HT);

    closeAllHt();
    closeAllMes();
    closeAllSurge();
    delay(DELAY_BETWEEN_CLICK);
  }
  digitalWrite(cardPin.ht, on);
}
void sequenceMes(cardPin_t cardPin){
  selectMux(MUX_MES);

  closeAllHt();
  closeAllMes();
  closeAllSurge();
  delay(DELAY_BETWEEN_CLICK);

  digitalWrite(cardPin.surge, HIGH);
}

void selectMux(mux_t m){
  //Stop everything first
  if(m != MUX_SURGE) digitalWrite(MASTER_SURGE, LOW);
  if(m != MUX_MES) digitalWrite(MASTER_MES, LOW);
  if(m != MUX_HT) digitalWrite(MASTER_HT, LOW);
  delay(DELAY_BETWEEN_CLICK);
  
  //Then activate the selected one
  if(m != MUX_NONE) digitalWrite(m, HIGH);
  currentMux = m;
}

void closeAllSurge(){
  for(int x=0; x<ROWS; x++){
    for(int y=0; y<COLUMNS; y++){
      digitalWrite(pins[x][y].surge, LOW);
    }
  }
}
void closeAllHt(){
  for(int x=0; x<ROWS; x++){
    for(int y=0; y<COLUMNS; y++){
      digitalWrite(pins[x][y].ht, LOW);
    }
  }
}
void closeAllMes(){
  for(int x=0; x<ROWS; x++){
    for(int y=0; y<COLUMNS; y++){
      digitalWrite(pins[x][y].mes, LOW);
    }
  }
}

cardPin_t retrieveCard(String str){
  int column = str.indexOf("A")>=0 ? 0:1;
  int row = str.substring(1).toInt();

  return pins[row][column];
}

void serial_event() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');

  //Identification command
  if(cmd[0] == '*'){
    if(cmd.indexOf("IDN?") >= 0){
      Serial.print(IDN);
    }
    else{
      Serial.print("\n");
    }
  }
  
    if (cmd[0] == ':') {
      String str_card, str_val;

      /* Multiplexer stuff */
      if (cmd.indexOf(SURGE_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(SURGE_CMD_STR));
        currentCard = retrieveCard(str_card);
        mux_flag = MUX_SURGE;
		
		if(currentMux != MUX_SURGE) 
			Serial.println(DELAY_BETWEEN_CLICK*3, DEC);
		else
			Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(HTRB_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(HTRB_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        currentCard = retrieveCard(str_card);
        htrb_on = str_val.toInt();
        mux_flag = MUX_HT;

        Serial.println(DELAY_BETWEEN_CLICK*2, DEC);
      }
      else if (cmd.indexOf(MES_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(MES_CMD_STR));
        currentCard = retrieveCard(str_card);
        mux_flag = MUX_MES;

        Serial.println(DELAY_BETWEEN_CLICK*2, DEC);
      }
      else if (cmd.indexOf(READ_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(READ_CMD_STR));
        currentCard = retrieveCard(str_card);
        read_flag = 1;
      }
      else if (cmd.indexOf(GAIN_CMD_STR) == 0) {
        str_val = cmd.substring(strlen(GAIN_CMD_STR));
        gain_flag = str_val.toInt();
      }
      else if (cmd.indexOf(STOP_MUX_CMD_STR) == 0) {
        mux_flag = MUX_NONE;

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      /* Relays direct commands */
      else if (cmd.indexOf(RELAY_SURGE_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(RELAY_SURGE_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        currentCard = retrieveCard(str_card);
        relay_surge_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(RELAY_HT_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(RELAY_HT_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        currentCard = retrieveCard(str_card);
        relay_ht_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(RELAY_MES_CMD_STR) == 0) {
        str_card = cmd.substring(strlen(RELAY_MES_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        currentCard = retrieveCard(str_card);
        relay_mes_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(RELAY_MUX_CMD_STR) == 0) {
        str_val = cmd.substring(strlen(RELAY_MUX_CMD_STR));
        relay_mux_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(STOP_BOARDS_CMD_STR) == 0) {
        str_val = cmd.substring(strlen(STOP_BOARDS_CMD_STR));
        relay_stop_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      /* Lamps */
      else if (cmd.indexOf(ORANGE_CMD_STR) == 0) {
        int on = cmd.substring(strlen(ORANGE_CMD_STR)).toInt();
        digitalWrite(ORANGE, !on);
      }
      else if (cmd.indexOf(RED_CMD_STR) == 0) {
        int on = cmd.substring(strlen(RED_CMD_STR)).toInt();
        digitalWrite(RED, !on);
      }
    }
  }
}
