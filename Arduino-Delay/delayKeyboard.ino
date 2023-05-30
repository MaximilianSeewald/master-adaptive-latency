#include <hidboot.h>
#include <usbhub.h>
#include <List.hpp>
#include <Keyboard.h>

List<long> timeDown;
List<long> timeUp;
List<int> keysDown;
List<int> keysUp;
long delayedTime = 150;
int keyDown;
int keyUp;

class KbdRptParser : public KeyboardReportParser
{
  long currentTime;
  int keySend;

  protected:
    void OnKeyDown	(uint8_t mod, uint8_t key);
    void OnKeyUp	(uint8_t mod, uint8_t key);
};


void KbdRptParser::OnKeyDown(uint8_t mod, uint8_t key)
{
    currentTime = millis();
    keySend = key;
    if (keySend == 40 || keySend == 41 || keySend == 1|| keySend == 2 || keySend == 72){
      if (keySend == 40)
        keySend = 176;  
      else if(keySend == 41)
        keySend = 177;   
      else if(keySend == 1)
        keySend = 128;
      else if(keySend == 72)
        keySend = 208;
      else
        keySend = 129;  
    }
    else{
      keySend = OemToAscii(0, keySend);
    }
    if(keySend != 0){
      keysDown.add(keySend);
      timeDown.add(currentTime);
    }

}


void KbdRptParser::OnKeyUp(uint8_t mod, uint8_t key)
{
    currentTime = millis();
    keySend = key;
    if (keySend == 40 || keySend == 41 || keySend == 1|| keySend == 2 || keySend == 72){
      if (keySend == 40)
        keySend = 176;  
      else if(keySend == 41)
        keySend = 177;   
      else if(keySend == 1)
        keySend = 128;
      else if(keySend == 72)
        keySend = 208;
      else
        keySend = 129;
    }
    else{
      keySend = OemToAscii(0, keySend);
    }
    if(keySend != 0){
      keysUp.add(keySend);
      timeUp.add(currentTime);
    }
}


USB     Usb;
//USBHub     Hub(&Usb);
HIDBoot<USB_HID_PROTOCOL_KEYBOARD>    HidKeyboard(&Usb);

KbdRptParser Prs;

void setup()
{
  Serial.begin( 115200 );
  Keyboard.begin();
  timeDown.clear();
  timeUp.clear();
  keysDown.clear();
  keysUp.clear();
  while (!Serial); // Wait for serial port to connect - used on Leonardo, Teensy and other boards with built-in USB CDC serial connection
  Serial.println("Start");
  if (Usb.Init() == -1)
    Serial.println("OSC did not start.");
  delay( 200 );
  HidKeyboard.SetReportParser(0, &Prs);
}

void loop()
{
  char message[5];
  int message_pos = 0;
  while(Serial.available() != 0){
    char inByte = Serial.read();
      if ( inByte != '\n' && (message_pos < 5 - 1) )
      {
        message[message_pos] = inByte;
        message_pos++;
      }else{
        message[message_pos] = '\0';
        delayedTime = atoi(message);
        message_pos = 0;
      }
  }
  if(millis() >= (timeDown.getValue(0) + delayedTime) && timeDown.getSize() > 0){
    keyDown = keysDown.getValue(0);
    Serial.print("KeyDown:");
    Serial.println(keyDown);
    keysDown.removeFirst();
    timeDown.removeFirst();
    Keyboard.press(keyDown);
  }
  if(millis() >= (timeUp.getValue(0) + delayedTime) && timeUp.getSize() > 0){
    keyUp = keysUp.getValue(0);
    Serial.print("KeyUp:");
    Serial.println(keyUp);
    keysUp.removeFirst();
    timeUp.removeFirst();
    Keyboard.release(keyUp);
  }
  Usb.Task();
}

