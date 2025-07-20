# CrowPanel ESP32 5.79" E-paper Display with 272*792 Resolution

import time
time.sleep(1)

import network
import utime
import urequests
import ntptime
# E-Paper display
import CrowPanel as eink
from writer import Writer
import freesans30
import framebuf
from icons import weather_icons

# rename config.py.sample -> config.py
from config import (
    ssid, password, ntp_host,
    latitude, longitude, utc_hour, api_url,
    icon_config
)

# Instantiate a Screen
screen = eink.Screen_579()
wri = Writer(screen, freesans30)

last_execution_time = 0
interval = 1800 # 30分毎に定期実行

# WiFiに接続
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(1)
    
    print('network config:', wlan.ifconfig())
    return wlan.isconnected()


def disconnect_wifi():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    if wlan.active():
        wlan.active(False)
    
    print('disconnect wifi')
    time.sleep(1)
    wlan.active(True)

def set_time():
    try:
        ntptime.host = ntp_host
        ntptime.settime()
        print("Time set from NTP server.")
        now = utime.localtime(utime.time() + utc_hour * 60 * 60)
        print("Current time:", "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(now[0], now[1], now[2], now[3], now[4], now[5]))
        return True
    except OSError as e:
        print("Error setting time:", e)
    return False


def get_weather_icon(weather_code):
    for cfg in icon_config:
        if weather_code in cfg[0]:
            return cfg[1]
    raise ValueError(f"Weather Code:{weather_code} is not set.")

# APIで温度取得
def get_weather():

    nowtime = utime.time() + utc_hour * 60 * 60
    now = utime.localtime(nowtime)
    tomorrow = utime.localtime(nowtime + 86400)
    start_date = "{:04d}-{:02d}-{:02d}".format(now[0], now[1], now[2])
    end_date = "{:04d}-{:02d}-{:02d}".format(tomorrow[0], tomorrow[1], tomorrow[2])

    param = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m,weather_code,precipitation_probability',
        'start_date': start_date,
        'timezone': "Asia/Tokyo",
        'end_date': end_date,
    }
    query_string = '&'.join(map(lambda key: f"{key}={param[key]}", param.keys()))
    url = api_url + "?" + query_string
    response = urequests.get(url)
    data = response.json()
    response.close()
    return data
    
def screen_rendering(data):
    # prepare framebuffer
    screen.fill(eink.COLOR_WHITE)
    want_dates = []
    
    def get_want_date(now):
        return "{:04d}-{:02d}-{:02d}T{:02d}:00".format(now[0], now[1], now[2], now[3])

    nowtime = utime.time() + utc_hour * 60 * 60
    for i in range(0,5):
        now = utime.localtime(nowtime + i * 3 * 60 * 60)
        want_dates.append(get_want_date(now))

    view_count = 0
    # 時間ごとの天気を表示
    for i, entry in enumerate(data["hourly"]["time"]):
        if entry in want_dates:
            index = data["hourly"]["time"].index(entry)
            temperature = data["hourly"]["temperature_2m"][index]
            precipitation_probability = data["hourly"]["precipitation_probability"][index]
            weather_code = data["hourly"]["weather_code"][index]
            _, hour_min = entry.split("T")

            x_center = int(792 / 5 * view_count)
            y_center = int(272 / 2 - 128 / 2)

            try:
                weather_icon = get_weather_icon(weather_code)
                if weather_icon in weather_icons:
                    img_data = bytearray(weather_icons[weather_icon])
                    img_buf = framebuf.FrameBuffer(img_data, 128, 128, framebuf.MONO_HLSB)
                    screen.blit(img_buf, x_center + 10, y_center -10)
            except Exception as e:
                screen.text(f"{e}", x_center, y_center, eink.COLOR_BLACK)
            Writer.set_textpos(screen, x_center + 35, 20)
            wri.printstring(f"{hour_min}", True)

            Writer.set_textpos(screen, x_center + 25, 200)
            wri.printstring(f"{temperature}°C", True)

            Writer.set_textpos(screen, x_center + 60, 240)
            wri.printstring(f"{precipitation_probability}%", True)
            
            view_count += 1

    screen.show()
    print("Completed screen rendering.")


def run():
    if connect_wifi():
        print("is connected wifi")
        if set_time():
            data = get_weather()
            screen_rendering(data)
        disconnect_wifi()

run()

while True:
    current_time = time.time()
    if current_time - last_execution_time >= interval:
        run()
        last_execution_time = current_time
    time.sleep(1)
