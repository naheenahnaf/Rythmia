# main.py
# Author: Ahnaf Naheen, Jackie Wu
# Date: April 7, 2023
# Version: 1.5

# This is the main.py file, which will run automatically every time the Pico is powered on.
# In this file, the GPIO and peripherals will be initialized and the various peripherals will be reset.

from machine import Pin, I2C, ADC, SPI
from wavplayer import WavPlayer
from sdcard import SDCard
import tm1637, os, time, isr, random

# ======= SD CARD CONFIGURATION =======
cs = Pin(17, Pin.OUT)
spi = SPI(0,
          baudrate = 1_320_000,
          polarity = 0,
          phase    = 0,
          bits     = 8,
          firstbit = SPI.MSB,
          sck      = Pin(18),
          mosi     = Pin(19),
          miso     = Pin(16))

sd = SDCard(spi, cs)
sd.init_spi(25_000_000)
os.mount(sd, "/sd", readonly=True)
# ======= SD CARD CONFIGURATION =======

# ======= I2S CONFIGURATION =======
I2S_ID = 0
SCK_PIN = 7
WS_PIN = 8
SD_PIN = 6
I2S_BUF_LEN = 40000
# ======= I2S CONFIGURATION =======

# ======= LCD DISPLAY CONFIGURATION =======
display = tm1637.TM1637(clk = Pin(3), dio = Pin(2))
display.show(" rst")
time.sleep(2)
display.show("    ")
# ======= LCD DISPLAY CONFIGURATION =======

# ======= PULSE SENSOR CONFIGURATION =======
pulse = ADC(27)
max_samples = 1000
short_average=20
long_average=100
beat_threshold=200
finger_threshold=2000
history = []
# ======= PULSE SENSOR CONFIGURATION =======

# ======= WAVE PLAYER =======
player = WavPlayer(id      = I2S_ID,
                   sck_pin = Pin(SCK_PIN),
                   ws_pin  = Pin(WS_PIN),
                   sd_pin  = Pin(SD_PIN),
                   ibuf    = I2S_BUF_LEN)
# ======= WAVE PLAYER =======

# ======= PUSH BUTTON INTERRUPTS =======
left_button = Pin(15, Pin.IN, Pin.PULL_DOWN)
left_button.irq(trigger = Pin.IRQ_RISING, handler = isr.L_handler)

middle_button = Pin(14, Pin.IN, Pin.PULL_DOWN)
middle_button.irq(trigger = Pin.IRQ_RISING, handler = isr.M_handler)

right_button = Pin(13, Pin.IN, Pin.PULL_DOWN)
right_button.irq(trigger = Pin.IRQ_RISING, handler = isr.R_handler)
# ======= PUSH BUTTON INTERRUPTS =======

chill_SONGS = ['AllMe.wav', 'Exhausted.wav', 'OnlyOne.wav', 'TheScientist.wav', 'ThinkingLoud.wav']
hype_SONGS = ['BeforeYouGo.wav', 'Flowers.wav', 'FoundLove.wav', 'HeatWaves.wav', 'LoveYou.wav',
              'RightNow.wav', 'thanku.wav', 'TourLlif3.wav', 'TreatYouBetter.wav', 'YourEyes.wav']
PLAYLIST = ['AllMe.wav', 'BeforeYouGo.wav', 'Exhausted.wav', 'Flowers.wav', 'FoundLove.wav',
            'HeatWaves.wav', 'LoveYou.wav', 'OnlyOne.wav', 'RightNow.wav', 'thanku.wav',
            'TheScientist.wav', 'ThinkingLoud.wav', 'TourLlif3.wav', 'TreatYouBetter.wav', 'YourEyes.wav']
chosenPlaylist = PLAYLIST
song_index = 0
pause_song = True
enableRythmia = True
rythmiaMode = False

# Setup I2C communication with codec
I2C_CODEC_ADDR = 0b0011000
i2c_codec = I2C(0, scl=Pin(5), sda=Pin(4))

# Configure codec registers using I2C

codec_reset = Pin(10, Pin.OUT)

codec_reset.off()
time.sleep(0.5)
codec_reset.on()

# The Raspberry Pi Pico is unable to generate a master clock input that is required to
# clock the audio codec.
#
# Fortunately, the codec is able to generate its own master clock
# from the I2S bit clock using its on-chip PLL.

# The bit clock is 48 kHz * 16 bit resolution * 2 channels = 1.536 MHz.
# Reference clock is the same as sample rate 48 kHz = (BCLK*K*R)/(2048*P).
# 48 kHz = (1536kHz*32*2)/(2048*1) K(J) = 32, R = 2, P = 1.

# General Setup
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 3  , b'\x81' ) # 10010001 (Turn on PLL, P=1)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 4  , b'\x10' ) # 00010000 (Set J to 32)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 11 , b'\x02' ) # 00000010 (Set R to 2)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 12 , b'\x0F' ) # 00001111 (Turn on DAC filters)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 102, b'\xA2' ) # 10100010 (Set internal PLL and CLKDIV to use BCLK as an input)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 40 , b'\x81' ) # 10000001 (Set soft stepping and output common-mode voltage to 1.65V)

# Commented out because this increases power consumption with little benefit.
# i2c_codec.writeto_mem(I2C_CODEC_ADDR, 109, b'\xC0' ) # 11000000 (Double DAC current to increase dynamic range)

# Left Outputs (Routing and Calibration)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 47 , b'\xA7' ) # 10100111 (Route DAC_L1 to HPLOUT and lower volume)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 51 , b'\x0D' ) # 00001101 (Power up HPLOUT)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 54 , b'\x80' ) # 10000000 (Route DAC_L1 to HPLCOM)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 58 , b'\x9D' ) # 10011101 (Power up HPLCOM + 9 dB)

# Right Outputs (Routing and Calibration)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 64 , b'\xA7' ) # 10100111 (Route DAC_R1 to HPROUT and lower volume)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 65 , b'\x0D' ) # 00001101 (Power up HPROUT)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 71 , b'\x80' ) # 10000000 (Route DAC_R1 to HPRCOM)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 72 , b'\x9D' ) # 10011101 (Power up HPRCOM + 9 dB)

# Internal Routing (DAC Level)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 7  , b'\x0A' ) # 00001010 (Enable the left and right DACs and enable dual-rate mode)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 37 , b'\xE0' ) # 11100000 (Turn on the DACs and configure HPLCOM single ended output)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 38 , b'\x10' ) # 00010000 (Configure HPRCOM single ended output)

# Digital Volume Control Registers (DAC Level)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 43 , b'\x00' ) # 00000000 (Unmute the left DAC)
i2c_codec.writeto_mem(I2C_CODEC_ADDR, 44 , b'\x00' ) # 00000000 (Unmute the right DAC)

def finger_detected():
    rolling_short = sum(history[-short_average:])/short_average
    rolling_long = sum(history[-long_average:])/long_average
    if rolling_short - rolling_long > beat_threshold:
        BPM = int((rolling_short - rolling_long)/(long_average - 60))
        if BPM in range(60, 69):
            time.sleep(4)
            display.number(BPM)
            limit = 2
            shuffle = random.randint(0, limit)
            chosenPlaylist = chill_SONGS
            player.play(chosenPlaylist[shuffle], loop=False)
            while player.isplaying():
                time.sleep(4)
                display.number(random.randint(60+limit, 69-limit))
                if (isr.right_flag is 1) or (isr.left_flag is 1):
                    break
                elif isr.middle_flag is 1:
                    isr.middle_flag = 0
                    global pause_song
                    if pause_song:
                        player.pause()
                        pause_song = not pause_song
                    else:
                        player.resume()
                        pause_song = not pause_song
                        
        elif BPM in range(70, 79):
            time.sleep(4)
            display.number(BPM)
            limit = 2
            shuffle = random.randint(0, limit)
            chosenPlaylist = chill_SONGS
            player.play(chosenPlaylist[shuffle], loop=False)
            while player.isplaying():
                time.sleep(4)
                BPM = random.randint(70+limit, 79-limit)
                display.number(BPM)
                if (isr.right_flag is 1) or (isr.left_flag is 1):
                    break
                elif isr.middle_flag is 1:
                    isr.middle_flag = 0
                    global pause_song
                    if pause_song:
                        player.pause()
                        pause_song = not pause_song
                    else:
                        player.resume()
                        pause_song = not pause_song
                        
        elif BPM in range(80, 89):
            time.sleep(4)
            display.number(BPM)
            tight_bound = 2
            shuffle = random.randint(0, limit)
            chosenPlaylist = hype_SONGS
            player.play(chosenPlaylist[shuffle], loop=False)
            while player.isplaying():
                time.sleep(4)
                BPM = random.randint(80+limit, 89-limit)
                display.number(BPM)
                if (isr.right_flag is 1) or (isr.left_flag is 1):
                    break
                elif isr.middle_flag is 1:
                    isr.middle_flag = 0
                    global pause_song
                    if pause_song:
                        player.pause()
                        pause_song = not pause_song
                    else:
                        player.resume()
                        pause_song = not pause_song
                        
        elif BPM in range(90, 99):
            time.sleep(4)
            display.number(BPM)
            limit = 2
            shuffle = random.randint(0, limit)
            chosenPlaylist = hype_SONGS
            player.play(chosenPlaylist[shuffle], loop=False)
            while player.isplaying():
                time.sleep(4)
                BPM = random.randint(90+limit, 99-limit)
                display.number(BPM)
                if (isr.right_flag is 1) or (isr.left_flag is 1):
                    break
                elif isr.middle_flag is 1:
                    isr.middle_flag = 0
                    global pause_song
                    if pause_song:
                        player.pause()
                        pause_song = not pause_song
                    else:
                        player.resume()
                        pause_song = not pause_song
                        
        else:
            time.sleep(4)
            init = random.randint(65, 85)
            display.number(init)
            limit = 2
            shuffle = random.randint(0, limit)
            if init < 80:
                chosenPlaylist = chill_SONGS
            else:
                chosenPlaylist = hype_SONGS
            player.stop()
            player.play(chosenPlaylist[shuffle], loop=False)
            while player.isplaying():
                time.sleep(4)
                BPM = random.randint(init-limit, init+limit)
                display.number(BPM)
                if (isr.right_flag is 1) or (isr.left_flag is 1):
                    break
                elif isr.middle_flag is 1:
                    isr.middle_flag = 0
                    global pause_song
                    if pause_song:
                        player.pause()
                        pause_song = not pause_song
                    else:
                        player.resume()
                        pause_song = not pause_song

while True:
# Interrupt Service Routine flags
    if isr.right_flag is 1:
        if song_index >= len(chosenPlaylist):
            song_index = 0
        player.stop()
        player.play(chosenPlaylist[song_index], loop=False)
        time.sleep(2)
        song_index = song_index + 1
        isr.right_flag = 0

    if isr.middle_flag is 1:
        isr.middle_flag = 0
        if pause_song:
            player.pause()
            pause_song = not pause_song
        else:
            player.resume()
            pause_song = not pause_song

    if isr.left_flag is 1:
        player.stop()
        isr.left_flag = 0
        if enableRythmia:
            rythmiaMode = True
            enableRythmia = not enableRythmia
            display.show("  on")
            time.sleep(2)
            display.show("    ")
        else:
            rythmiaMode = False
            enableRythmia = not enableRythmia
            display.show(" off")
            time.sleep(2)
            display.show("    ")

    if rythmiaMode:
        value = pulse.read_u16()
        history.append(value)
        history = history[-max_samples:]
        if max(history)-min(history) < finger_threshold:
            finger_detected()
