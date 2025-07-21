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
import freesans32
import framebuf
from icons import weather_icons
import machine

# rename config.py.sample -> config.py
from config import (
    ssid, password, ntp_host,
    latitude, longitude, utc_hour, api_url,
    icon_config
)

# Instantiate a Screen
screen = eink.Screen_579()
wri = Writer(screen, freesans32)

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


def get_now(sec=0):
    return utime.localtime(utime.time() + utc_hour * 60 * 60 + sec)

def set_time():
    ntptime.host = ntp_host
    time.sleep(0.1)
    ntptime.settime()
    print("Time set from NTP server.")
    now = get_now()
    print("Current time:", "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}".format(now[0], now[1], now[2], now[3], now[4], now[5]))

def get_weather_icon(weather_code):
    for cfg in icon_config:
        if weather_code in cfg[0]:
            return cfg[1]
    raise ValueError(f"Weather Code:{weather_code} is not set.")

# APIで天候情報取得
def get_weather():
    now = get_now()
    tomorrow = get_now(86400)
    start_date = "{:04d}-{:02d}-{:02d}".format(now[0], now[1], now[2])
    end_date = "{:04d}-{:02d}-{:02d}".format(tomorrow[0], tomorrow[1], tomorrow[2])

    param = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m,weather_code,precipitation_probability,is_day',
        'start_date': start_date,
        'timezone': "Asia/Tokyo",
        'end_date': end_date,
    }
    query_string = '&'.join(map(lambda key: f"{key}={param[key]}", param.keys()))
    url = api_url + "?" + query_string
    print("Get Weahter Request Start.")
    response = urequests.get(url)
    if response.reason != b"OK" or response.status_code >= 400:
        raise Exception(f"HTTP Request failed. Status Code: {response.status_code}")
    
    print("Get Weahter Request Success.")
    data = response.json()
    response.close()
    return data
    
def screen_rendering(data):
    # prepare framebuffer
    screen.fill(eink.COLOR_WHITE)
    want_dates = []
    
    def get_want_date(now):
        return "{:04d}-{:02d}-{:02d}T{:02d}:00".format(now[0], now[1], now[2], now[3])

    for i in range(0,5):
        now = get_now(i * 3 * 60 * 60) # 3時間毎
        want_dates.append(get_want_date(now))

    view_count = 0
    # 時間ごとの天気を表示
    for i, entry in enumerate(data["hourly"]["time"]):
        if entry in want_dates:
            index = data["hourly"]["time"].index(entry)
            temperature = data["hourly"]["temperature_2m"][index]
            precipitation_probability = data["hourly"]["precipitation_probability"][index]
            weather_code = data["hourly"]["weather_code"][index]
            is_day = data["hourly"]["is_day"][index]
            _, hour_min = entry.split("T")

            x_center = int(792 / 5 * view_count)
            y_center = int(272 / 2 - 128 / 2)

            try:
                weather_icon = get_weather_icon(weather_code)
                if is_day == 0:
                    weather_icon = "night_" + weather_icon
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
    try:
        machine.freq(240000000) # High Power 240MHz
        print("freq: ", machine.freq())
        if connect_wifi():
            print("is connected wifi")
            set_time()
            data = get_weather()
            screen_rendering(data)
    except Exception as e:
        screen.fill(eink.COLOR_WHITE)
        screen.text(f"{e}", 0, 0, eink.COLOR_BLACK)
        screen.show()
    finally:
        disconnect_wifi()
        machine.freq(20000000) # Low Power 20MHz

# 起動時実行
run()

# 毎時1分に1度だけ実行
try:
    while True:
        min,sec = get_now()[4:6]
        # Debug
        # if sec == 1:
        #     run()
        if min == 1:
            run()
        time.sleep(60)
except KeyboardInterrupt:
    pass