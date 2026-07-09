'============================================'
'| Project: Schildi                         |'
'|                                          |'
'| This Phyton project is a robot pet,      |'
'| that can perceive its surroundings       |'
'| through many sensors and takes           |'
'| appropriate actions with it.             |'
'|                                          |'
'| Copyright: Daniel Rebholz                |'
'| License: Private Use Only                |'
'============================================'



# -------------------------------- Battery ------------------------------------- 
#  4,2V  to  3,71V


# -------------------------------- Pin Assignment ------------------------------------- 


#                         SDA  = GP0      VBUS     =  5V (USB Power)
#                         SCL  = GP1      VSYS     =  1.8 to 5.5V
#                              = GND      GND      = 
#                              = GP2      3V3_EN   =  
#                              = GP3      3V3(OUT) =  Sub Change for Gyro
#                              = GP4      ADC_VREF =
#                              = GP5      GP28_A2  = 
#                              = GND      GND      =
#  LM393 Photosensor Right     = GP6      GP27_A1  = 
#  LM393 Photosensor Left      = GP7      GP26_A0  =  Volt Sensor durch Spannungsteiler 
#                              = GP8      RUN      =  
#  IR Sensor  - Right Distance = GP9      GP22     =  HC-SR505 PIR Sensor Bewegungsmelder Modul
#                              = GND      GND      =  
#  IR Sensor  - Left Distance  = GP10     GP21     =  Echo       - HC-SR04 Modul
#                              = GP11     GP20     =  Trigger    - HC-SR04 Modul
#  5V PWM vibration motor      = GP12     GP19     =  Busy-Pin   - DFPlayer Sound Modul
#                              = GP13     GP18     =  Buzzer     - Sound Modul
#                              = GND      GND      =
#  Vibration  - Modul          = GP14     GP17     =  RX-Pin     - DFPlayer Sound Modul
#  PIR Sensor - Movement Modul = GP15     GP16     =  TX-Pin     - DFPlayer Sound Modul
  
  


# ------------ Adress Assignment -----------

#60  =  SH1106 Display  - Links/Rechts  - 1.3 inch xfp1116-07a y oled displays
#61  =  SSD1306 Display - Vorne

#64  =  PCA9685 Servo Controller

#72  =  16 Byte 4-Kanal I2C IIC Analog-Digital-ADC-PGA-Wandler

#104 =  DS3231 Real Time Clock Modul für Raspberry Pi 

#105 =  MPU6050 Modul  3-Achsen-Beschleunigungssensor und 3-Achsen-Gyroskop. Eingebauter Temperatur-Sensor von -40°C bis +85°C  - 3,3V / 5V ~5mA

#112 =  PCA9685 Servo Controller

#Flexibler Dünnfilm Drucksensor 3,3 / 5V Analog

# --------------------------------------- 




# Load libraries
import time
import machine

import framebuf

import ssd1306

# Load out libraries
from sh1106 import SH1106_I2C

from time import sleep
from machine import Pin, PWM, I2C, SPI, ADC, UART,

import mpu6050

from hcsr04 import HCSR04

#from mpu6050 import MPU6050

from ds3231 import DS3231


from pca9685 import PCA9685
from servo import Servos




# ------------------ Define Interface---------------------

i2c_interface = 0

# Create the I2C Bus
sdapin = Pin(0)
sclpin = Pin(1)

i2c = I2C(i2c_interface, scl=sclpin, sda=sdapin, freq=40000)


# --------------------- Bus Scanner ----------------------

i2cdevices = i2c.scan()

# Scan all Bus Devices
print('-- Bus Scanner --')
print(i2cdevices)
print('')

# ---------------------- initialize of Buzzer -----------------

# initialize of Buzzer
buzzer = PWM(Pin(18))
buzzer.freq(659)

tones = {"E5": 659,"A5": 880,"G5": 784}
startsong = ["E5","G5","A5"]


# -------------------- HC-SR505 PIR Bewegungssensor --------------------

pirfront_pin = Pin(22, Pin.IN)  # Sensor an GP122

# -------------------- MPU6050 Modul 3-Achsenssensor + Temperatur-Sensor --------------------

class MPU6050:
    def __init__(self, i2c, addr=0x69):  # 0x69 = Adresse 105
        self.i2c = i2c
        self.addr = addr
        # Wake up device
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')

    def read_raw_data(self, reg):
        high = self.i2c.readfrom_mem(self.addr, reg, 1)[0]
        low = self.i2c.readfrom_mem(self.addr, reg + 1, 1)[0]
        value = (high << 8) | low
        if value > 32767:
            value -= 65536
        return value

    def get_accel(self):
        ax = self.read_raw_data(0x3B) / 16384.0
        ay = self.read_raw_data(0x3D) / 16384.0
        az = self.read_raw_data(0x3F) / 16384.0
        return (ax, ay, az)

    def get_gyro(self):
        gx = self.read_raw_data(0x43) / 131.0
        gy = self.read_raw_data(0x45) / 131.0
        gz = self.read_raw_data(0x47) / 131.0
        return (gx, gy, gz)

    def get_temp(self):
        raw_temp = self.read_raw_data(0x41)
        temp_c = (raw_temp / 340.0) + 36.53
        return temp_c

mpu = MPU6050(i2c, addr=0x69)

# -------------------- Spannungsteiler 30k x 10k --------------------

#12.60v = Batterie ist Voll                  4,20 V
#11.10v = Batterie ist hälfte leer           3,70 V
#10.50v = Batterie ist leer                  3,00 V

adc = ADC(26)  # GP26 ist ADC0

# Widerstandswerte Spannungsteiler
R1 = 30000  # 3 x 10k Ohm in Reihe (Oberer Widerstand)
R2 = 10000  # 1 x 10k Ohm (Unterer Widerstand)

# Referenzspannung ADC (kann je nach Pico leicht variieren, z.B. 3.27 V)
VREF = 3.27

offset = 0.59  # gemessene Differenz

def read_battery_voltage():
    raw = adc.read_u16()
    voltage_adc = (raw / 65535) * VREF
    voltage_bat = voltage_adc * (R1 + R2) / R2
    voltage_bat += offset  # Korrektur hinzufügen
    return voltage_adc, voltage_bat

# -------------------- DS3231 Modul definition --------------------

rtc = DS3231(i2c)


# Uhrzeit einmalig setzen (danach auskommentieren)
# rtc.set_time(2025, 6, 28, 13, 34, 0)

# -------------------- Buzzer definition --------------------


#  Buzzer definition
def playtone(frequency):
    buzzer.duty_u16(1000)
    buzzer.freq(frequency)

def bequiet():
    buzzer.duty_u16(0)
    
# Plays ones by start
def playsong(mysong):
    for i in range(len(mysong)):
        if (mysong[i] == "P"):
            bequiet()
        else:
            playtone(tones[mysong[i]])
        sleep(0.3)
    bequiet()

def battery_warning_tone():
    for _ in range(3):                 # Zwei kurze Beeps
        buzzer.freq(1000)
        buzzer.duty_u16(1000)
        sleep(0.2)
        buzzer.duty_u16(0)
        sleep(0.2)


# ------ LM393 Photoelectric Sensor Module Right/Left definition  ------

pe_sensor_left = Pin(7, Pin.IN)
pe_sensor_right = Pin(6, Pin.IN)

# ------ 5V PWM vibration motor module definition ----------------------

vibmotor = Pin(12, Pin.OUT, value=0)

# ----------------------- HC-SR04 Modul definition  --------------------

# HC-SR04 an GP3 (Trigger) und GP2 (Echo)
frontdistancesensor = HCSR04(trigger_pin=20, echo_pin=21)


# ----------------------- Display definition  --------------------

oled_ssd1306 = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3D)

oled_sh1106 = SH1106_I2C(128, 64, i2c, addr=0x3C)

def load_image(filename):
    with open(filename, 'rb') as f:
        f.readline()
        f.readline()
        width, height = [int(v) for v in f.readline().split()]
        data = bytearray(f.read())
    return framebuf.FrameBuffer(data, width, height, framebuf.MONO_HLSB)


# Initialization of Eye Images
image1 = load_image('/eyes/image1.pbm')
image2 = load_image('/eyes/image2.pbm')
image3 = load_image('/eyes/image3.pbm')
image4 = load_image('/eyes/image4.pbm')
image5 = load_image('/eyes/image5.pbm')
image6 = load_image('/eyes/image6.pbm')
image7 = load_image('/eyes/image7.pbm')
image8 = load_image('/eyes/image8.pbm')       # Auge komplett geschlossen
image9 = load_image('/eyes/image9.pbm')
image10 = load_image('/eyes/image10.pbm')
image11 = load_image('/eyes/image11.pbm')
image12 = load_image('/eyes/image12.pbm')
image13 = load_image('/eyes/image13.pbm')
image14 = load_image('/eyes/image14.pbm')
image15 = load_image('/eyes/image15.pbm')
image16 = load_image('/eyes/image16.pbm')
image17 = load_image('/eyes/image17.pbm')
image18 = load_image('/eyes/image18.pbm')
image19 = load_image('/eyes/image19.pbm')
image20 = load_image('/eyes/image20.pbm')
image21 = load_image('/eyes/image21.pbm')     # Auge komplett geöffnet
image22 = load_image('/eyes/image22.pbm')
image23 = load_image('/eyes/image23.pbm')
image24 = load_image('/eyes/image24.pbm')
image25 = load_image('/eyes/image25.pbm')
image26 = load_image('/eyes/image26.pbm')
image27 = load_image('/eyes/image27.pbm')
image28 = load_image('/eyes/image28.pbm')
image29 = load_image('/eyes/image29.pbm')



# Raspberry Pi logo as 32x32 bytearray
buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
 
 
# Load the raspberry pi logo into the framebuffer (the image is 32x32)
fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)


# Initialization of Mouth
mouth1 = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xfc\x00\x00\x00\x00\x3f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0f\xff\xf0\x00\x00\x0f\xff\xf0\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xfe\x00\x00\x7f\xff\xff\x00\x00\x00\x00\x00\x00\x00\x03\xff\xff\xff\x00\x00\xff\xff\xff\xc0\x00\x00\x00\x00\xf0\x00\x0f\xff\xff\xff\x80\x01\xff\xff\xff\xf0\x00\x0f\x00\x01\xf0\x00\x1f\xff\xff\xff\xc0\x03\xff\xff\xff\xf8\x00\x0f\x80\x03\xf0\x00\x7f\xfe\x01\xff\xe0\x07\xff\x80\x7f\xfe\x00\x0f\xc0\x07\xf0\x00\xff\xe0\x00\x0f\xf0\x0f\xf0\x00\x07\xff\x00\x0f\xe0\x07\xf0\x03\xff\x80\x00\x07\xf8\x1f\xe0\x00\x01\xff\xc0\x0f\xe0\x0f\xf0\x0f\xfe\x00\x00\x03\xfc\x3f\xc0\x00\x00\x7f\xf0\x0f\xf0\x0f\xff\xff\xfc\x00\x00\x01\xfe\x7f\x80\x00\x00\x3f\xff\xff\xf0\x1f\xff\xff\xf0\x00\x00\x00\xff\xff\x00\x00\x00\x0f\xff\xff\xf8\x1f\xff\xff\xe0\x00\x00\x00\x7f\xfe\x00\x00\x00\x07\xff\xff\xf8\x3f\xff\xff\x80\x00\x00\x00\x3f\xfc\x00\x00\x00\x01\xff\xff\xfc\x1f\x3f\xfe\x00\x00\x00\x00\x1f\xf8\x00\x00\x00\x00\x7f\xfc\xf8\x0e\x0f\xf8\x00\x00\x00\x00\x0f\xf0\x00\x00\x00\x00\x1f\xf0\x70\x00\x00\x00\x00\x00\x00\x00\x07\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')


# Initialization of Mouth Buffer
mouth_smile = framebuf.FrameBuffer(mouth1, 128, 64, framebuf.MONO_HLSB)



# ------------------------------ DFPlayer Mini --------------------------

#GND = Schwarz
#VCC = Orange 
#RX  = Violett
#TX  = Gelb

# UART1 verwenden: TX=GPIO4, RX=GPIO5
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

def send_cmd(cmd, param1=0, param2=0):
    """Sendet einen DFPlayer-Befehl"""
    cmd_line = bytearray(10)
    cmd_line[0] = 0x7E  # Startbyte
    cmd_line[1] = 0xFF  # Version
    cmd_line[2] = 0x06  # Länge
    cmd_line[3] = cmd   # Befehl
    cmd_line[4] = 0x00  # Keine Rückmeldung
    cmd_line[5] = (param1 >> 8) & 0xFF
    cmd_line[6] = param1 & 0xFF
    checksum = 0 - sum(cmd_line[1:7])
    cmd_line[7] = (checksum >> 8) & 0xFF
    cmd_line[8] = checksum & 0xFF
    cmd_line[9] = 0xEF  # Endbyte
    uart.write(cmd_line)

# ---------------------- ADS1115 Modul definition -----------------------

ADS_ADDR = 0x48

def licht_richtung(a0, a1, a2, toleranz=200):
    """
    a0: vorne
    a1: hinten rechts
    a2: hinten links
    """

    def nahe(x, y):
        return abs(x - y) <= toleranz

    # Wenn hinten rechts und hinten links ähnlich hell und heller als vorne → "Hinten"
    if nahe(a1, a2) and a1 < a0 and a2 < a0:
        return "Hinten"

    # Wenn vorne und rechts ähnlich → "Vorne rechts"
    elif nahe(a0, a1) and a0 < a2:
        return "Vorne rechts"

    # Wenn vorne und links ähnlich → "Vorne links"
    elif nahe(a0, a2) and a0 < a1:
        return "Vorne links"

    # Ein Kanal deutlich heller als die anderen → eindeutige Richtung
    elif a0 < a1 and a0 < a2:
        return "vorne"
    elif a1 < a0 and a1 < a2:
        return "rechts"
    elif a2 < a0 and a2 < a1:
        return "links"

    # Wenn alles sehr ähnlich → gleichmäßig
    elif nahe(a0, a1) and nahe(a1, a2):
        return "Gleichmäßig / Zentral"

    else:
        return "Unklar"
    

def read_adc_channel(ch):
    if ch < 0 or ch > 3:
        raise ValueError("Kanal muss 0-3 sein")

    mux = 0x4000 + (ch << 12)

    config = 0x8000 | mux | 0x0200 | 0x0100 | 0x0080 | 0x0003

    i2c.writeto_mem(ADS_ADDR, 0x01, config.to_bytes(2, 'big'))

    time.sleep_ms(8)

    raw = i2c.readfrom_mem(ADS_ADDR, 0x00, 2)
    val = int.from_bytes(raw, 'big')

    if val > 0x7FFF:
        val -= 0x10000

    return val


# -------------------- PCA9685 Servo Modul definition --------------------

pca = PCA9685(i2c=i2c)
pca.freq(50)  # Servos benötigen 50 Hz

servo = Servos(i2c=i2c)

def move_servo(angle):
    servo.position(index=0, degrees=angle)
    print(f"Servo auf {angle}°")
    time.sleep(0.5)


# -------------------- Start of Programm --------------------

print('-- Programm beginnt --')
print('')

# ---------------- Startsong spielt einmal ab ---------------
playsong(startsong) 
    
# Hello
oled_ssd1306.fill(0)
oled_ssd1306.blit(fb, 96, 0)
oled_ssd1306.text('Hello', 0, 0)
oled_ssd1306.text('my name is', 0, 10)
oled_ssd1306.text('Schildi', 0, 24)
oled_ssd1306.show()
    
sleep(3)    
  
# -------------------- Start of Programm --------------------

while True:
       
    # ---------- Strom auslesen vom Spannungsteiler ----------
    
    adc_voltage, battery_voltage = read_battery_voltage()

    # ---------- HC-SR04 Modul -------------------------------
    
    entfernung = frontdistancesensor.distance_cm()
    
    # ---------- LM393 Photoelectric Sensor Module -----------
    
    pes_status_left = pe_sensor_left.value()
    pes_status_right = pe_sensor_right.value()
    
    # ---------- MPU6050 Gyro Modul auslesen -----------------
    
    accel = mpu.get_accel()
    gyro = mpu.get_gyro()
    
    temp_raw = mpu.get_temp()
    temp_korrigiert = temp_raw - 0.00  # Beispiel-Offset für deinen Sensor
    
       
    # ---------- DS3231 RealTimeClock Modul - Zeit auslesen --
    
    year, month, day, hour, minute, second = rtc.get_time()
    
    # ---------- ADS1115 auslesen ----------------------------

    a0 = read_adc_channel(0)
    a1 = read_adc_channel(1)
    a2 = read_adc_channel(2)

    richtung = licht_richtung(a0, a1, a2)
    
    # ---------- Flexibler Dünnfilm Drucksensor auslesen -----
    
    a3 = read_adc_channel(3)
    
    # ---------- Vibrationsfunktion -----
    
    if a3 > 900:
        
    # Vibration 3× ein/aus
        for _ in range(3):
            vibmotor.on()
            sleep(0.5)
            vibmotor.off()
            sleep(0.5)

    else:
        print("")
    
    
    sleep(5)
    

    # ------------- Display ausgabe - Werte -------------
    
    
    # SSD1306 auf Adresse 0x3D (61) - Display Vorne
    oled_ssd1306.fill(0)
    oled_ssd1306.text(f"ADC:      {adc_voltage:.2f} V", 0, 0)
    oled_ssd1306.text(f"Battery: {battery_voltage:.2f} V", 0, 10)
    oled_ssd1306.text('', 0,20, 1)
    oled_ssd1306.text("Batterie Status:", 0,30)
    if 11.10 <= battery_voltage <= 12.60:
        oled_ssd1306.text("voll", 0, 40) 

    if 10.50 <= battery_voltage <= 11.10:
        oled_ssd1306.text("hälfte leer", 0, 40) 

    if battery_voltage <= 10.50:
        oled_ssd1306.text("Bitte aufladen!", 0, 40) 
    oled_ssd1306.show()
    
    
    sleep(5)
    
    
    oled_ssd1306.fill(0)
    oled_ssd1306.text("AbstandSensoren:", 0, 0)
    oled_ssd1306.text("Vorne: {:.2f} cm".format(entfernung), 0,10, 1)
    oled_ssd1306.text("", 0, 20)
    oled_ssd1306.text("Links und Rechts:", 0, 30)
    if pes_status_left == 0:
        oled_ssd1306.text("LINKS  erkannt!", 0,40, 1)
    else:
        oled_ssd1306.text("Links  frei", 0,40, 1)
    if pes_status_right == 0:
        oled_ssd1306.text("RECHTS erkannt!", 0,50, 1)
    else:
        oled_ssd1306.text("Rechts frei", 0,50, 1)
    oled_ssd1306.show()
    
    
    sleep(5)
        
        
    oled_ssd1306.fill(0)
    oled_ssd1306.text("Lichtsensoren:", 0, 0)
    oled_ssd1306.text(f"Vorne : {a0}", 0, 10)
    oled_ssd1306.text(f"Rechts: {a1}", 0, 20)
    oled_ssd1306.text(f"Links : {a2}", 0, 30)
    oled_ssd1306.text(f"Lichtquelle ist:", 0, 40)
    oled_ssd1306.text(f"{richtung}", 0, 50) 
    oled_ssd1306.show() 
    
    
    sleep(5)
    
    
    oled_ssd1306.fill(0)
    oled_ssd1306.text("Temperatur:", 0, 0)
    oled_ssd1306.text('Temp:   ' + f"{temp_korrigiert:.2f} C", 0,10, 1)
    oled_ssd1306.text("Datum:", 0,30, 1)   
    oled_ssd1306.text(f"{day:02d}.{month:02d}.{year:04d}", 0,40, 1) 
    oled_ssd1306.text(f"{hour:02d}:{minute:02d}:{second:02d}", 0,50, 1)
    oled_ssd1306.show() 
    
    
    sleep(5)
    
    
    oled_ssd1306.fill(0)
    oled_ssd1306.text("Gyrowerte:", 0, 0)
    oled_ssd1306.text("", 0,10, 1)
    # Beschleunigung anzeigen
    oled_ssd1306.text(f"X: {accel[0]:.1f}", 0, 20)
    oled_ssd1306.text(f"Y: {accel[1]:.1f}", 0, 30)
    oled_ssd1306.text(f"Z: {accel[2]:.1f}", 0, 40)
    # Gyroskop anzeigen
    oled_ssd1306.text(f"X: {gyro[0]:.1f}", 64, 20)
    oled_ssd1306.text(f"Y: {gyro[1]:.1f}", 64, 30)
    oled_ssd1306.text(f"Z: {gyro[2]:.1f}", 64, 40)
    oled_ssd1306.show() 
    
    sleep(5) 
    
    oled_ssd1306.fill(0)
    oled_ssd1306.text("Drucksensor:", 0, 0)
    if a3 <= 900:
        oled_ssd1306.text("kein Druck", 0, 20)
    else:
        oled_ssd1306.text("Druck erkannt!", 0, 20)
    oled_ssd1306.text(f"Wert: {a3}", 0, 50)
    oled_ssd1306.show()  

    sleep(5)
    
    
    # ------------- Display ausgabe - Normal -------------
    
    # SSD1306 auf Adresse 0x3D (61) - Display Vorne
    # Mund
    oled_ssd1306.fill(0)
    oled_ssd1306.blit(mouth_smile, 0, 0)
    oled_ssd1306.show()
    
    
    # SH1106 auf Adresse 0x3C (60) - Display Links/Rechts    
    oled_sh1106.write_cmd(0xA1)  # Spiegelung X (horizontal)
    oled_sh1106.write_cmd(0xC8)  # Spiegelung Y (vertikal)
    
    #oled_sh1106.text("SH1106 Module", 0, 0)
    oled_sh1106.show()
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image21, 41, 4)
    oled_sh1106.show()
    sleep(0.05)      
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image22, 41, 4)
    oled_sh1106.show()
    sleep(0.05)    
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image23, 41, 4)
    oled_sh1106.show()
    sleep(0.05)

    oled_sh1106.fill(0)
    oled_sh1106.blit(image24, 41, 4)
    oled_sh1106.show()
    sleep(0.05)

    oled_sh1106.fill(0)
    oled_sh1106.blit(image25, 41, 4)
    oled_sh1106.show()
    sleep(0.05)
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image26, 41, 4)
    oled_sh1106.show()
    sleep(0.05)
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image27, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image28, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image29, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image1, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image2, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image3, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image4, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image5, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image6, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image7, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 

    oled_sh1106.fill(0)
    oled_sh1106.blit(image8, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image9, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image10, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image11, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image12, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image13, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image14, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image15, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image16, 41, 4)
    oled_sh1106.show()
    sleep(0.05)   
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image17, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image18, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image19, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image20, 41, 4)
    oled_sh1106.show()
    sleep(0.05) 
    
    oled_sh1106.fill(0)
    oled_sh1106.blit(image21, 41, 4)
    oled_sh1106.show()
    sleep(3) 
    
    




    # --------------------- Serialmonitor --------------------
    print("---- Stomwerte: ----") 
    print(f"ADC-Spannung:      {adc_voltage:.2f} V")
    print(f"Batteriespannung: {battery_voltage:.2f} V")   
    if 11.10 <= battery_voltage <= 12.60:
        print("Batterie: ist voll")

    if 10.50 <= battery_voltage <= 11.10:
        print("Batterie: zur hälfte leer")

    if battery_voltage <= 10.50:
        print("Batterie: ist leer, aufladen!")
        battery_warning_tone() 
    print("")   
    print("---- Gyrowerte: ----")     
    print("Beschleunigung (g): X={:.2f}, Y={:.2f}, Z={:.2f}".format(*accel))
    print("Gyroskop (°/s):     X={:.2f}, Y={:.2f}, Z={:.2f}".format(*gyro))
    print("")  
    print("---- Temperatur: ----")   
    print("Temperatur: {:.2f} °C".format(temp_korrigiert))
    print("")   
    print("---- Licht: ----")
    print("Lichtsensor  (vorne):", a0)
    print("Lichtsensor (rechts):", a1)
    print("Lichtsensor  (links):", a2)
    print("→ Richtung der Lichtquelle:", richtung)
    print("")
    print("---- Bewegungssensor Vorne: ----")
    if pirfront_pin.value() == 1:
        print("Bewegung erkannt!")
    else:
        print("Bewegung nicht erkannt!")
    print("")
    print("---- Drucksensor Vorne: ----")    
    if a3 <= 900:
        print("Druck nicht erkannt")
        print("Wert:", a3)
    else:
        print("Druck erkannt!")
        print("Wert:", a3)
    print("")
    print("---- Vorne: ----")       
    print("Entfernung: {:.2f} cm".format(entfernung))
    print("")
    print("---- Links: ----")      
    if pes_status_left == 0:
        print("Objekt LINKS erkannt!")
    else:
        print("Links frei.")
    print("")    
    print("---- Rechts: ----")    
    if pes_status_right == 0:
        print("Objekt RECHTS erkannt!")
    else:
        print("Rechts frei.")
    print("")
    print("---- Uhrzeit: ----")   
    print(f"Datum:            {day:02d}.{month:02d}.{year:04d}")
    print(f"Uhrzeit:          {hour:02d}:{minute:02d}:{second:02d}")  
    if hour <= 6:
        print('Hinweis:          Es ist Nacht')
    elif hour < 9:
        print('Hinweis:          Es ist Morgen')
    elif hour < 15:
        print('Hinweis:          Es ist Mittag')
    elif hour < 21:
        print('Hinweis:          Es ist Abend')
    else:
        print('Hinweis:          Es ist Nacht')    
    print("") 
    print("------------------------------------------------")
    print("")     


    # --------------------- Reload Time --------------------
      
    time.sleep(3)




# -------------------- End of Programm ----------