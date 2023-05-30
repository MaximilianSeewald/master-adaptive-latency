#include <hidboot.h>
#include <usbhub.h>
#include <List.hpp>
#include <Mouse.h>

List<int> x;
List<int> y;
List<long> time;
List<long> timeButtons;
List<int> buttons;
long delayedTime = 150;
int xMove;
int yMove;
int button;


class MouseRptParser : public MouseReportParser
{
protected:
	void OnMouseMove	(MOUSEINFO *mi);
	void OnLeftButtonUp	(MOUSEINFO *mi);
	void OnLeftButtonDown	(MOUSEINFO *mi);
	void OnRightButtonUp	(MOUSEINFO *mi);
	void OnRightButtonDown	(MOUSEINFO *mi);
	void OnMiddleButtonUp	(MOUSEINFO *mi);
	void OnMiddleButtonDown	(MOUSEINFO *mi);
  long currentTime;
  int xPos;
  int yPos;
};
void MouseRptParser::OnMouseMove(MOUSEINFO *mi)
{
    currentTime = millis();
    xPos = mi->dX;
    yPos = mi->dY;
    time.add(currentTime);
    x.add(xPos);
    y.add(yPos);
};
void MouseRptParser::OnLeftButtonUp	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 0;
    buttons.add(test);
};
void MouseRptParser::OnLeftButtonDown	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 1;
    buttons.add(test);
};
void MouseRptParser::OnRightButtonUp	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 2;
    buttons.add(test);
};
void MouseRptParser::OnRightButtonDown	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 3;
    buttons.add(test);
};
void MouseRptParser::OnMiddleButtonUp	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 4;
    buttons.add(test);
};
void MouseRptParser::OnMiddleButtonDown	(MOUSEINFO *mi)
{
    currentTime = millis();
    timeButtons.add(currentTime);
    int test = 5;
    buttons.add(test);
};

USB Usb;
USBHub Hub(&Usb);
HIDBoot<USB_HID_PROTOCOL_MOUSE> HidMouse(&Usb);
MouseRptParser Prs;

void setup()
{
    Serial.begin( 115200 );
    Mouse.begin();
    time.clear();
    x.clear();
    y.clear();
    timeButtons.clear();
    buttons.clear();
    while (!Serial); // Wait for serial port to connect - used on Leonardo, Teensy and other boards with built-in USB CDC serial connection
    Serial.println("Start");
    if (Usb.Init() == -1)
        Serial.println("OSC did not start.");
    delay( 200 );
    HidMouse.SetReportParser(0, &Prs);
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
  if(millis() >= (time.getValue(0) + delayedTime) && time.getSize() > 0){
      xMove = x.getValue(0);
      yMove = y.getValue(0);
      time.removeFirst();
      x.removeFirst();
      y.removeFirst();
      Mouse.move(xMove, yMove, 0);
      Serial.print("MOVE:");
      Serial.print(xMove);
      Serial.print(":");
      Serial.println(yMove);
  }
  if(millis() >= (timeButtons.getValue(0) + delayedTime) && timeButtons.getSize() > 0){
      button = buttons.getValue(0);
      timeButtons.removeFirst();
      buttons.removeFirst();
      Serial.print("BUTTON:");
      Serial.println(button);
      if(button == 1)
        Mouse.press(MOUSE_LEFT);
      if(button == 3)
        Mouse.press(MOUSE_RIGHT);
      if(button == 5)
        Mouse.press(MOUSE_MIDDLE);
      if(button == 0)
        Mouse.release(MOUSE_LEFT);
      if(button == 2)
        Mouse.release(MOUSE_RIGHT);
      if(button == 4)
        Mouse.release(MOUSE_MIDDLE);

  }
  Usb.Task();
}