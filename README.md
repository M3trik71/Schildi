# Schildi

![Projektübersicht](Schildi.jpg)

This Phyton project is a robot pet, that can perceive its surroundings through many sensors and takes appropriate actions with it.  

The Base of that Project is a Raspberry Pi Pico W.

Build in Modules:
- 2x LM393 Photosensor
- 2x IR Sensor
- 1x PWM vibration motor
- 1x HC-SR04 Modul
- 1x Volt Sensor
- 1x MPU6050 Gyro Modul
- 1x DFPlayer Modul
- 1x DS3231 Modul
- 1x PCA9685 Servo Controller
- 1x Flex Touch Sensor
- 2x 1.3inch xfp1116-07a y oled displays
- 1x SSD1306 Display
- 4x MG995 Servos
- 8x MG90 Servos
  

 -------------------------------- Pin Assignment ------------------------------------- 


                         SDA  = GP0      VBUS     =  5V (USB Power)
                         SCL  = GP1      VSYS     =  1.8 to 5.5V
                              = GND      GND      = 
                              = GP2      3V3_EN   =  
                              = GP3      3V3(OUT) =  Sub Change for Gyro
                              = GP4      ADC_VREF =
                              = GP5      GP28_A2  = 
                             = GND      GND      =
  LM393 Photosensor Right     = GP6      GP27_A1  = 
  LM393 Photosensor Left      = GP7      GP26_A0  =  Volt Sensor 
                              = GP8      RUN      =  
  IR Sensor  - Right Distance = GP9      GP22     =  HC-SR505 PIR Movement Sensor 
                              = GND      GND      =  
  IR Sensor  - Left Distance  = GP10     GP21     =  Echo       - HC-SR04 Modul
                              = GP11     GP20     =  Trigger    - HC-SR04 Modul
  5V PWM Vibration Motor      = GP12     GP19     =  Busy-Pin   - DFPlayer Sound Modul
                              = GP13     GP18     =  Buzzer     - Sound Modul
                              = GND      GND      =
  Vibration  - Modul          = GP14     GP17     =  RX-Pin     - DFPlayer Sound Modul
  PIR Sensor - Movement Modul = GP15     GP16     =  TX-Pin     - DFPlayer Sound Modul
  


 ------------ Adress Assignment -----------

#60  =  SH1106 Display  - Left/Right  - 1.3 inch xfp1116-07a y oled displays
#61  =  SSD1306 Display - Front

#64  =  PCA9685 Servo Controller

#72  =  16 Byte 4-Channel I2C IIC Analog-Digital-ADC-PGA-Wandler

#104 =  DS3231 Real Time Clock Modul for Raspberry Pi 

#105 =  MPU6050 Modul build in Temperatur-Sensor between -40°C bis +85°C  - 3,3V / 5V ~5mA

#112 =  PCA9685 Servo Controller

# --------------------------------------- 

