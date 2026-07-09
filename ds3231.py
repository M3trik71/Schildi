rom machine import I2C

class DS3231:
    def __init__(self, i2c, address=0x68):
        self.i2c = i2c
        self.address = address

    def bcd2dec(self, bcd):
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def dec2bcd(self, dec):
        return ((dec // 10) << 4) | (dec % 10)

    def get_time(self):
        data = self.i2c.readfrom_mem(self.address, 0x00, 7)
        second = self.bcd2dec(data[0] & 0x7F)
        minute = self.bcd2dec(data[1])
        hour = self.bcd2dec(data[2] & 0x3F)
        day = self.bcd2dec(data[4])
        month = self.bcd2dec(data[5] & 0x1F)
        year = self.bcd2dec(data[6]) + 2000
        return (year, month, day, hour, minute, second)

    def set_time(self, year, month, day, hour, minute, second):
        data = bytes([
            self.dec2bcd(second),
            self.dec2bcd(minute),
            self.dec2bcd(hour),
            0,  # Wochentag, optional
            self.dec2bcd(day),
            self.dec2bcd(month),
            self.dec2bcd(year - 2000)
        ])
        self.i2c.writeto_mem(self.address, 0x00, data)