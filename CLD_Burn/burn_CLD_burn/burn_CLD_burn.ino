#include <Arduino.h>

/*
    Query:
      - :LongPULse n(n in milliseconds, return nothing)
      - :PULSe n    (n in microseconds, return n if less than 1000, otherwise n/1000)
    Write:
      - :LIGHt
        - :ORANge o (1: on, 0: off)
        - :RED o    (1: on, 0: off)
*/

//#define DEBUG_SERIAL

#define IDN "CALY TECH,CLD_burning,000001,V1.6\n"
#define PULSE_CMD_STR ":PULS "
#define LONG_PULSE_CMD_STR ":LPUL "
#define ORANGE_CMD_STR ":LIGH:ORAN "
#define RED_CMD_STR ":LIGH:RED "

//PORTB
#define ORANGE 8
#define RED 9
#define LED 13
//PORTD
#define DRIVER 3
#define BUTTON1 2
#define BUTTON2 4

#define POT A1

inline void delay_1us();
void serial_event();
void debug(String str);

/*
 * INITIALISATION
 */
void setup() {
  Serial.begin(9600);
  pinMode(DRIVER, OUTPUT);
  digitalWrite(DRIVER, LOW);
  pinMode(BUTTON1, INPUT);
  pinMode(BUTTON2, INPUT_PULLUP);

  pinMode(ORANGE, OUTPUT);
  pinMode(RED, OUTPUT);
  pinMode(LED, OUTPUT);
  digitalWrite(ORANGE, LOW);
  digitalWrite(RED, LOW);
  digitalWrite(LED, LOW);
}

//Variables globales de durée de pulse
unsigned int pulse = 0;
unsigned int long_pulse = 0;

/*
 * PROGRAMME PRINCIPAL
 */
void loop() {

  //Communication
  serial_event();

  //Si appuie sur le bouton 1, pulse de 10us
  if(digitalRead(BUTTON1) == 0){
    debug("BTN1");
  	digitalWrite(LED, HIGH);
      PORTD = 0b00001000;
      delayMicroseconds(10);
      PORTD = 0b00000000;
      
      while(digitalRead(BUTTON1) == 0);
      delay(200);
  	digitalWrite(LED, LOW);
    debug("_BTN1");
  }
  
  //Si appuie sur le bouton 2, pulse de 3s
  if(digitalRead(BUTTON2) == 0){
    debug("BTN2");
  	digitalWrite(LED, HIGH);
      PORTD = 0b00001000;
      delay(3000);
      PORTD = 0b00000000;
      
      while(digitalRead(BUTTON2) == 0);
      delay(200);
  	digitalWrite(LED, LOW);
    debug("_BTN2");
  }

  
  //Commande long pulse (en ms)
  if (long_pulse != 0) {
    debug("Long:"+String(long_pulse));
  	digitalWrite(LED, HIGH);
  	PORTD = 0b00001000;
      delay(long_pulse);
  	PORTD = 0b00000000;
  	digitalWrite(LED, LOW);
  	
  	long_pulse = 0;
    debug("_Long");
  }
  
  //Commande pulse (en us)
  if (pulse != 0) {
    debug("Short:"+String(pulse));
	  digitalWrite(LED, HIGH);
	//Si la durée est plus courte que 30us, pour être plus précis on code en dur les delais
    if (pulse <= 30) {
      switch (pulse) {
        case 1:
    		  PORTD = 0b00001000;
    		  delay_1us();
    		  PORTD = 0b00000000;
          break;
        case 3:
    		  PORTD = 0b00001000;
    		  delay_1us();
    		  delay_1us();
    		  delay_1us();
    		  PORTD = 0b00000000;
          break;
        case 10:
    		  PORTD = 0b00001000;
    		  delayMicroseconds(10);
    		  PORTD = 0b00000000;
          break;
        case 30:
    		  PORTD = 0b00001000;
    		  delayMicroseconds(30);
    		  PORTD = 0b00000000;
          break;
    		default:
    		  PORTD = 0b00001000;
    		  delayMicroseconds(pulse);
    		  PORTD = 0b00000000;
    		  break;
      }
	//Si on reste inférieur à la milliseconde
    } else if (pulse < 1000) {
  	  PORTD = 0b00001000;
      delayMicroseconds(pulse);
  	  PORTD = 0b00000000;
	//Sinon (perte de précision)
    } else {
      pulse /= 1000;
  	  PORTD = 0b00001000;
      delay(pulse);
  	  PORTD = 0b00000000;
    }
	  digitalWrite(LED, LOW);

    Serial.println("!done:"+String(pulse));
    pulse = 0;
    debug("_Short");
  }
}

/*
 * COMMUNICATION
 * - indexOf cherche la position d'une chaine dans une autre. 
 *   Si la chaine cherchée est en première position, il renvoit 0
 *   Si la chaine cherchée n'est pas trouvée, il renvoit -1
 * - substring recupére une sous chaine à partir d'une position
 * - strlen renvoit la longueur de la chaine
 * - toInt convertit une chaine en nombre entier
 */
void serial_event() {
  //Reception d'une transmition série
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); //Commande

  	//Identification command
  	if(cmd[0] == '*'){//Est-ce que le premier caractère est un '*'
		//Demande d'identification
  		if(cmd.indexOf("IDN?") >= 0){
  			Serial.print(IDN);
  		}
  		else{
  			Serial.print("\n");
  		}
  	}
	
	//Specific command
    if (cmd[0] == ':') {//Est-ce que le premier caractère est un ':'
      if (cmd.indexOf(PULSE_CMD_STR) == 0) { 
        pulse = cmd.substring(strlen(PULSE_CMD_STR)).toInt();
      }
      else if (cmd.indexOf(LONG_PULSE_CMD_STR) == 0) {
        long_pulse = cmd.substring(strlen(LONG_PULSE_CMD_STR)).toInt();
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


inline void delay_1us(){
  //16MHz -> 16 nop
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
  __asm__("nop\n\t");
}

void debug(String str){
  #ifdef DEBUG_SERIAL
  Serial.println(str);
  #endif
}
