## About

CrowPanel ESP32 E-Paper HMI 5.79-inch Displayをベースに、お天気情報のデジタルサイネージを作成しました。

## 特徴と作成理由

[CrowPanel-ESP32-5.79-E-paper](https://github.com/Elecrow-RD/CrowPanel-ESP32-5.79-E-paper-HMI-Display-with-272-792/tree/master/example/arduino/Demos/5.79_wifi_http_openweather)のお天気を取得する処理にはOpenWeatherMapが使われています。

しかしながら、OpenWeatherMapの利用にはクレジットカード登録が必須でしたので、  
[Open-Meteo](https://open-meteo.com/)APIと[MicroPython](https://micropython.org/)で実装を試してみました。  
Open-Meteo APIはAPIキーは不要です。非商用利用であれば無料で利用が可能です。

そのほかはAPIの実行のたびにWiFiをON/OFFすることで省エネ？にしています。

## Instration

```bash
$ curl -LO https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20250415-v1.25.0.bin

$ pip install esptool
$ esptool.py erase_flash
$ esptool.py --baud 460800 write_flash 0 ESP32_GENERIC_S3-SPIRAM_OCT-20250415-v1.25.0.bin
```

環境はVSCodeに[MicroPico](https://github.com/paulober/MicroPico)拡張を利用しました。

### VScodeでMicroPicoの操作

- config.py.sampleを別名でコピーしてWiFi情報を設定してください。
    - `$ cp config.py.sample config.py`
    - edit config.py
- CrowPanelには自動で接続できていると思います。以下は接続後の操作になります。
- エクスプローラーを左クリックで「Upload project to Pico」を実行します。
    - この操作により、*.py ファイルは全てアップロードされます。
- 最後にmain.pyを開いた状態で左下の「▷Run」を実行します。
    - うまくいけば画面が表示され、インストールは完了です。

##  開発の参考情報

### CrowPanelでMicroPythonの導入の手引き
- [Elecrow 5.79" screen library for Micropython](https://www.elecrow.com/sharepj/elecrow-579-screen-library-for-micropython-513.html)
- [Elecrow CrowPanel 5.79" E-Paper display](https://www.bukys.eu/components/crowpanel_5_79)
- [MicroPython-ESP32-S3](https://micropython.org/download/ESP32_GENERIC_S3/)

### 画面デザインの参考にしました

- [cubic9com/crowpanel-5.79_weather-display](https://github.com/cubic9com/crowpanel-5.79_weather-display)

### カスタムフォントの作成

- fonts.googleから[さわらびフォント](https://fonts.google.com/specimen/Sawarabi+Gothic)をダウンロード 
- 必要となるキャラクターのフォントを作成
```
$ curl -LO https://raw.githubusercontent.com/peterhinch/micropython-font-to-py/c24761448e6ef1c40716b9b2b629e6fa37b2c9d2/font_to_py.py

$ python font_to_py.py -c " 0123456789.C°℃:%％" SawarabiGothic-Regular.ttf 32 SawarabiGothicRegularNumeric32.py 
```

- 参考: [peterhinch/micropython-font-to-py](https://github.com/peterhinch/micropython-font-to-py)

### モノクロ画像の作成

#### 利用している天気のアイコン
- [erikflowers/weather-icons](https://github.com/erikflowers/weather-icons)

#### モノクロ画像の変換処理
jpegやpngをCrowPanel用のモノクロ画像に変換できるので便利です。
- [TimHanewich/MicroPython-SSD130](https://github.com/TimHanewich/MicroPython-SSD1306)

#### ImageMagickのconvertコマンドでsvgをpngに変換
```shell
$ for i in `ls *.svg`; convert -size 128x128 $i $i.png
```

```shell
$ curl -LO https://raw.githubusercontent.com/TimHanewich/MicroPython-SSD1306/refs/heads/master/src/convert.py
```

#### モノクロ画像の作成

icons.py にアイコンファイルをまとめる処理

```python
import convert
import os
import glob

flist = glob.glob("weather/*.png")
buffer_list = []
for fname in flist:
    name = os.path.basename(fname)
    name, _, _ = name.split(".")
    converted = convert.image_to_buffer(fname)
    buffer = converted[0]

    data = "'{}': {}".format(name, buffer)
    buffer_list.append(data)

with open("icons.py", "w") as f:
    f.write("weather_icons = {\n  " + ",\n  ".join(buffer_list) + "\n}")
```
