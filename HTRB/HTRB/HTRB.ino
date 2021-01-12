#include <Arduino.h>
#include <SPI.h>              
#include <MCP23S17.h>

/*
    Write:
      - :ENABle dev,o (device; 1: on, 0: off)
      - :MES dev,m (device; 1: mes on, 0: gnd on)
      - :RELAy
        - :ON dev,o (device; 1: on, 0: off)
        - :MES dev,o (device; 1: on, 0: off)
        - :GND dev,o (device; 1: on, 0: off)
      - :LIGHt
        - :ORANge o (1: on, 0: off)
        - :RED o    (1: on, 0: off)
*/

#define IDN "CALY TECH,HTRB_test,000001,V1.1\n"
#define ENABLE_CMD_STR ":ENAB "
#define MES_CMD_STR ":MES "
#define RELAY_ENABLE_CMD_STR ":RELA:ON "
#define RELAY_MES_CMD_STR ":RELA:MES "
#define RELAY_GND_CMD_STR ":RELA:GND "
#define ORANGE_CMD_STR ":LIGH:ORAN "
#define RED_CMD_STR ":LIGH:RED "


#define ORANGE 8
#define RED 9


#define BLOCK_A 0x10
#define BLOCK_B 0x20
#define BLOCK_C 0x40

typedef enum{
  RELAY_ON  = 0x1,
  RELAY_MES = 0x2,
  RELAY_GND = 0x4
} relay_t;

typedef enum{
  NONE = 0,
  DEV_A1  = (BLOCK_A | 1), DEV_B1  = (BLOCK_C | 1),
  DEV_A2  = (BLOCK_A | 2), DEV_B2  = (BLOCK_C | 2),
  DEV_A3  = (BLOCK_A | 3), DEV_B3  = (BLOCK_C | 3),
  DEV_A4  = (BLOCK_A | 4), DEV_B4  = (BLOCK_C | 4),
  DEV_A5  = (BLOCK_A | 5), DEV_B5  = (BLOCK_C | 5),
  DEV_A6  = (BLOCK_A | 6), DEV_B6  = (BLOCK_C | 6),
  DEV_A7  = (BLOCK_A | 7), DEV_B7  = (BLOCK_C | 7),
  DEV_A8  = (BLOCK_A | 8), DEV_B8  = (BLOCK_C | 8),
  DEV_A9  = (BLOCK_B | 1), DEV_B9  = (BLOCK_B | 5),
  DEV_A10 = (BLOCK_B | 2), DEV_B10 = (BLOCK_B | 6),
  DEV_A11 = (BLOCK_B | 3), DEV_B11 = (BLOCK_B | 7),
  DEV_A12 = (BLOCK_B | 4), DEV_B12 = (BLOCK_B | 8)
} device_t;


MCP mcp1(0, 10);
MCP mcp2(4, 10);
MCP mcp3(2, 10);
MCP mcp4(6, 10);
MCP mcp5(1, 10);


#define DELAY_BETWEEN_CLICK 1000
#define NO_FLAG 255

volatile device_t device;
volatile int enable_flag = NO_FLAG;
volatile int measure_flag = NO_FLAG;
volatile int relay_on_flag = NO_FLAG;
volatile int relay_mes_flag = NO_FLAG;
volatile int relay_gnd_flag = NO_FLAG;


void serial_event();
void enable_device(device_t dev, bool on);
void measure_device(device_t dev, bool on);
bool getMcpAndPin(device_t dev, relay_t relay, MCP **mcp, int *pin);
device_t retrieveDevice(String str);


void setup() {
  Serial.begin(9600);
  
  pinMode(ORANGE, OUTPUT);
  pinMode(RED, OUTPUT);
  digitalWrite(ORANGE, LOW);
  digitalWrite(RED, LOW);
  
  mcp1.begin();
  mcp2.begin();
  mcp3.begin();
  mcp4.begin();
  mcp5.begin();
  
  mcp1.pinMode(0x0000);
  mcp2.pinMode(0x0000);
  mcp3.pinMode(0x0000);
  mcp4.pinMode(0x0000);
  mcp5.pinMode(0x0000);

  init_devices();

}

void loop() {
  MCP *mcp = NULL;
  int pin = 0;
  
  serial_event();

  if(enable_flag != NO_FLAG){
    enable_device(device, enable_flag);
    
    enable_flag = NO_FLAG;
  }
  
  if(measure_flag != NO_FLAG){
    measure_device(device, measure_flag);
    
    measure_flag = NO_FLAG;
  }
  
  if(relay_on_flag != NO_FLAG){
    getMcpAndPin(device, RELAY_ON, &mcp, &pin);
    mcp->digitalWrite(pin, relay_on_flag);
    
    relay_on_flag = NO_FLAG;
  }
  if(relay_mes_flag != NO_FLAG){
    getMcpAndPin(device, RELAY_MES, &mcp, &pin);
    mcp->digitalWrite(pin, relay_mes_flag);
    
    relay_mes_flag = NO_FLAG;
  }
  if(relay_gnd_flag != NO_FLAG){
    getMcpAndPin(device, RELAY_GND, &mcp, &pin);
    mcp->digitalWrite(pin, relay_gnd_flag);
    
    relay_gnd_flag = NO_FLAG;
  }
  
}

void enable_device(device_t dev, bool on){
  MCP *mcp_on = NULL;
  int pin_on = 0;
  MCP *mcp_mes = NULL;
  int pin_mes = 0;
  MCP *mcp_gnd = NULL;
  int pin_gnd = 0;

  getMcpAndPin(dev, RELAY_ON , &mcp_on , &pin_on );
  getMcpAndPin(dev, RELAY_MES, &mcp_mes, &pin_mes);
  getMcpAndPin(dev, RELAY_GND, &mcp_gnd, &pin_gnd);

  mcp_on->digitalWrite(pin_on, LOW);
  if(on){
    mcp_mes->digitalWrite(pin_mes, LOW);
    mcp_gnd->digitalWrite(pin_gnd, HIGH);
    delay(DELAY_BETWEEN_CLICK);
    mcp_on->digitalWrite(pin_on, HIGH);
  }
  else{
    mcp_on->digitalWrite(pin_on, LOW);
    delay(DELAY_BETWEEN_CLICK);
    mcp_mes->digitalWrite(pin_mes, LOW);
    mcp_gnd->digitalWrite(pin_gnd, LOW);
  }
}

void init_devices(){
  MCP *mcp_on = NULL;
  int pin_on = 0;
  MCP *mcp_mes = NULL;
  int pin_mes = 0;
  MCP *mcp_gnd = NULL;
  int pin_gnd = 0;

  for(int i=1; i<=8; i++){
    for(int j=0; j<3; j++){
      int block = (j == 0) ? BLOCK_A : ((j == 1) ? BLOCK_B : BLOCK_C);
      device_t dev = static_cast<device_t>(block | i);
      
      getMcpAndPin(dev, RELAY_ON , &mcp_on , &pin_on );
      getMcpAndPin(dev, RELAY_MES, &mcp_mes, &pin_mes);
      getMcpAndPin(dev, RELAY_GND, &mcp_gnd, &pin_gnd);
      
      mcp_on->digitalWrite(pin_on, LOW);
      mcp_mes->digitalWrite(pin_mes, LOW);
      mcp_gnd->digitalWrite(pin_gnd, LOW);
    }
  }
}


void measure_device(device_t dev, bool on){
  MCP *mcp_mes = NULL;
  int pin_mes = 0;
  MCP *mcp_gnd = NULL;
  int pin_gnd = 0;

  getMcpAndPin(dev, RELAY_MES, &mcp_mes, &pin_mes);
  getMcpAndPin(dev, RELAY_GND, &mcp_gnd, &pin_gnd);

  if(on){
    mcp_mes->digitalWrite(pin_mes, HIGH);
    delay(DELAY_BETWEEN_CLICK);
    mcp_gnd->digitalWrite(pin_gnd, LOW);
  }
  else{
    mcp_gnd->digitalWrite(pin_gnd, HIGH);
    delay(DELAY_BETWEEN_CLICK);
    mcp_mes->digitalWrite(pin_mes, LOW);
  }
}


bool getMcpAndPin(device_t dev, relay_t relay, MCP **mcp, int *pin){
  MCP *mcp_on = NULL;
  int pin_on = 0;
  MCP *mcp_mes = NULL;
  int pin_mes = 0;
  MCP *mcp_gnd = NULL;
  int pin_gnd = 0;
  
  if(dev & BLOCK_A){
    mcp_on  = &mcp1;
    pin_on  = 8 + (dev & 0xF);
    mcp_mes = &mcp1;
    pin_mes = 9 - (dev & 0xF);
    mcp_gnd = &mcp2;
    pin_gnd = 8 + (dev & 0xF);
  }
  else if(dev & BLOCK_B){
    mcp_on  = &mcp2;
    pin_on  = 9 - (dev & 0xF);
    mcp_mes = &mcp3;
    pin_mes = 8 + (dev & 0xF);
    mcp_gnd = &mcp3;
    pin_gnd = 9 - (dev & 0xF);
  }
  else if(dev & BLOCK_C){
    mcp_on  = &mcp4;
    pin_on  = 8 + (dev & 0xF);
    mcp_mes = &mcp4;
    pin_mes = 9 - (dev & 0xF);
    mcp_gnd = &mcp5;
    pin_gnd = 8 + (dev & 0xF);
  }
  else return false;

  if(relay & RELAY_ON){
    *mcp = mcp_on;
    *pin = pin_on;
  }
  else if(relay & RELAY_MES){
    *mcp = mcp_mes;
    *pin = pin_mes;
  }
  else if(relay & RELAY_GND){
    *mcp = mcp_gnd;
    *pin = pin_gnd;
  }
  else return false;

  return true;
}


device_t retrieveDevice(String str){
  device_t dev = NONE;
  bool isA = str.indexOf("A")>=0;
  int column = str.substring(1).toInt();

  switch(column){
    case 1:
      dev = isA ? DEV_A1:DEV_B1;
      break;
    case 2:
      dev = isA ? DEV_A2:DEV_B2;
      break;
    case 3:
      dev = isA ? DEV_A3:DEV_B3;
      break;
    case 4:
      dev = isA ? DEV_A4:DEV_B4;
      break;
    case 5:
      dev = isA ? DEV_A5:DEV_B5;
      break;
    case 6:
      dev = isA ? DEV_A6:DEV_B6;
      break;
    case 7:
      dev = isA ? DEV_A7:DEV_B7;
      break;
    case 8:
      dev = isA ? DEV_A8:DEV_B8;
      break;
    case 9:
      dev = isA ? DEV_A9:DEV_B9;
      break;
    case 10:
      dev = isA ? DEV_A10:DEV_B10;
      break;
    case 11:
      dev = isA ? DEV_A11:DEV_B11;
      break;
    case 12:
      dev = isA ? DEV_A12:DEV_B12;
      break;
  }

  return dev;
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
      String str_device, str_val;
      
      if (cmd.indexOf(ENABLE_CMD_STR) == 0) {
        str_device = cmd.substring(strlen(ENABLE_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        device = retrieveDevice(str_device);
        enable_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(MES_CMD_STR) == 0) {
        str_device = cmd.substring(strlen(MES_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        device = retrieveDevice(str_device);
        measure_flag = str_val.toInt();

        Serial.println(DELAY_BETWEEN_CLICK, DEC);
      }
      else if (cmd.indexOf(RELAY_ENABLE_CMD_STR) == 0) {
        str_device = cmd.substring(strlen(RELAY_ENABLE_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        device = retrieveDevice(str_device);
        relay_on_flag = str_val.toInt();
      }
      else if (cmd.indexOf(RELAY_MES_CMD_STR) == 0) {
        str_device = cmd.substring(strlen(RELAY_MES_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        device = retrieveDevice(str_device);
        relay_mes_flag = str_val.toInt();
      }
      else if (cmd.indexOf(RELAY_GND_CMD_STR) == 0) {
        str_device = cmd.substring(strlen(RELAY_GND_CMD_STR), cmd.indexOf(","));
        str_val = cmd.substring(cmd.indexOf(",")+1);
        device = retrieveDevice(str_device);
        relay_gnd_flag = str_val.toInt();
      }
      else if (cmd.indexOf(ORANGE_CMD_STR) == 0) {
        int on = cmd.substring(strlen(ORANGE_CMD_STR)).toInt();
        digitalWrite(ORANGE, on);
      }
      else if (cmd.indexOf(RED_CMD_STR) == 0) {
        int on = cmd.substring(strlen(RED_CMD_STR)).toInt();
        digitalWrite(RED, on);
      }
    }
  }
}
