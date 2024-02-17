from kivy.config import Config

coef = 3 / 8
Config.set("graphics", "width", "405")
Config.set("graphics", "height", "720")

from kivy.uix.button import Button
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from plyer import gps
from kivy.utils import platform
from kivy.network.urlrequest import UrlRequest
from kivy.uix.image import Image
from kivy.clock import Clock
import json
from firebase_admin import db
from firebase_admin import credentials
import firebase_admin
import hashlib

sm = ScreenManager()

# sabitler
koordinatlar = [[21, 34], [41, 34], [24, 35], [18, 33]]  # toplanma merkezi koordinatları
konum = [91, 181]  # lat [-90, 90], lon [-180, 180] arasında tanımlı
enYakinMerkez = [91, 181]
yardimTuru = -1  # -1: boş, 0: ilk yardım, 1: gida, 2: kiyafet
yardimTuruStr = ["ilk yardım", "gida", "kiyafet"]
isim = "Balsa Teknoloji Takımı"
durumIndex = 0  # 0: yardım talep edilmedi, 1: drone istenilen yardımı alıyor, 2: drone yola çıktı, 3: Yardım geldi, şahıs yardımı almadı, 4: yardım alındı
durumList = ["Henüz Yardım Talep Etmediniz", "Yardım Hazırlanıyor", "Yardım Yola Çıktı",
             "Yardım Konuma Ulaştı, Henüz Teslim Edilmedi", "Yardım Size Teslim Edildi"]
maxBasmaHakki = 1
ilkYardimBasmaHakki = maxBasmaHakki  # her 10dk da basma hakkı
gidaBasmaHakki = maxBasmaHakki
kiyafetBasmaHakki = maxBasmaHakki
postUrl = "http://httpbin.org/post"
jsonKeyFileAndroid = "app/missions-balsa.json"
fireBaseUrl = "https://missions-balsa-default-rtdb.firebaseio.com/"  # 'https://fir-deneme-5067f-default-rtdb.firebaseio.com/'


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        # variables
        self.ilkYardimTimeRemained = "10"  # 600 seconds = 10 minutes, time wait for another 3 help request
        self.gidaTimeRemained = "10"
        self.kiyafetTimeRemained = "10"

        self.baseLayout = FloatLayout()
        self.layout = BoxLayout(pos_hint={"x": 0, "y": .15}, size_hint=(1, .68),
                                orientation="vertical", spacing=50)

        self.btnSizeHint = (.6, 1)

        self.btn0 = Button(text="İlk Yardım {}".format("* " * ilkYardimBasmaHakki),
                           color=(1, 1, 1, 1),
                           size_hint=self.btnSizeHint,
                           pos_hint={"center_x": 0.5, "center_y": 0.5},
                           on_release=self.ilkYardimFonks,
                           background_down="resim/ilk1.png",
                           background_normal="resim/ilk0.png"
                           )
        self.btn1 = Button(text="Gıda {}".format("* " * gidaBasmaHakki),
                           color=(1, 1, 1, 1),
                           size_hint=self.btnSizeHint,
                           pos_hint={"center_x": 0.5, "center_y": 0.5},
                           on_release=self.gidaFonks,
                           background_down="resim/gida1.png",
                           background_normal="resim/gida0.png"
                           )
        self.btn2 = Button(text="Kıyafet {}".format("* " * kiyafetBasmaHakki),
                           color=(1, 1, 1, 1),
                           size_hint=self.btnSizeHint,
                           pos_hint={"center_x": 0.5, "center_y": 0.5},
                           on_release=self.kiyafetFonks,
                           background_down="resim/kiyafet1.png",
                           background_normal="resim/kiyafet0.png"
                           )

        self.btn3 = Button(text="<--",
                           color=(1, 1, 1, 1),
                           size_hint=(0.17, 0.1),
                           pos_hint={"left": 0, "top": 1},
                           on_release=self.changeToInfoScreen
                           )
        self.infoLabel = Label(text="...",
                               color=(1, 0, 0, 1),
                               size_hint=(.6, .15),
                               pos_hint={"center_x": 0.5, "center_y": 0.5},
                               )

        # GOOGLE HARİTALAR LİNKİ YARDIM BAŞARIYLA TALEP EDİLDİĞİNDE HAZIR OLACAK, aşağıdaki kodla
        # self.mapsUrl = "https://www.google.com/maps/dir/{},{}/{},{}/".format(konum[0], konum[1], enYakinMerkez[0], enYakinMerkez[1])
        # self.mapLink.markup = True
        # self.mapLink.text = "[ref={}]tikla[/ref]".format(self.mapsUrl)
        self.mapLink = Label(text="Yardım Talep Ettiğinizde\nKargo Konum Linki burada görünecek",
                             color=(0, 0, 0, 1),
                             size_hint=(.6, .15),
                             pos_hint={"center_x": 0.5, "center_y": 0.5},
                             markup=True,
                             on_ref_press=self.openGoogleMaps
                             )

        self.balsa = Image(source="resim/balsaLogo.png",
                           pos_hint={"right": 1, "top": 1.06},
                           size_hint=(0.3, 0.3))

        self.layout.add_widget(self.infoLabel)
        self.layout.add_widget(self.mapLink)
        self.layout.add_widget(self.btn0)
        self.layout.add_widget(self.btn1)
        self.layout.add_widget(self.btn2)
        self.baseLayout.add_widget(self.balsa)
        self.baseLayout.add_widget(self.btn3)
        self.baseLayout.add_widget(self.layout)
        self.add_widget(self.baseLayout)

    def ilkYardimFonks(self, ins):
        global ilkYardimBasmaHakki

        if ilkYardimBasmaHakki > 0:
            self.dataGonder(0)
            # burayı post request başarılı olduğunda yapmalıyım
            # ilkYardimBasmaHakki -= 1
            # self.btn0.text = "İlk Yardım {}".format("* " * ilkYardimBasmaHakki)

    def gidaFonks(self, ins):
        global gidaBasmaHakki

        if gidaBasmaHakki > 0:
            self.dataGonder(1)

    def kiyafetFonks(self, ins):
        global kiyafetBasmaHakki

        if kiyafetBasmaHakki > 0:
            self.dataGonder(2)

    ## Timer Fonksiyonları
    def ilkYardimTimerStart(self):
        self.ilkYardimClock = Clock.schedule_interval(self.ilkYardimWait, 1)

    def gidaTimerStart(self):
        self.gidaClock = Clock.schedule_interval(self.gidaWait, 1)

    def kiyafetTimerStart(self):
        self.kiyafetClock = Clock.schedule_interval(self.kiyafetWait, 1)

    def ilkYardimWait(self, *args):
        global ilkYardimBasmaHakki
        print(f"ilkYardimWait(), timeRemained:, {self.ilkYardimTimeRemained}, kalan Hak: {ilkYardimBasmaHakki}")
        self.ilkYardimTimeRemained = str(int(self.ilkYardimTimeRemained) - 1)

        # when timer ends, button is clicable again
        if int(self.ilkYardimTimeRemained) <= 0:
            # reset variables to default
            ilkYardimBasmaHakki = maxBasmaHakki
            self.ilkYardimTimeRemained = "600"
            self.ilkYardimClock.cancel()  # stop timer
            self.btn0.text = "İlk Yardım {}".format("* " * ilkYardimBasmaHakki)
            self.btn0.disabled = False

        # cant click button now, show remained time as "min : sec" format
        elif int(self.ilkYardimTimeRemained) > 0 and ilkYardimBasmaHakki == 0:
            self.btn0.text = "İlk Yardım ({})".format(self.convertToMinSec(self.ilkYardimTimeRemained))

    def gidaWait(self, *args):
        global gidaBasmaHakki

        self.gidaTimeRemained = str(int(self.gidaTimeRemained) - 1)

        # when timer ends, button is clicable again
        if int(self.gidaTimeRemained) <= 0:
            # reset variables to default
            gidaBasmaHakki = maxBasmaHakki
            self.gidaTimeRemained = "600"
            self.gidaClock.cancel()  # stop timer
            self.btn1.text = "Gıda {}".format("* " * gidaBasmaHakki)
            self.btn1.disabled = False

        # cant click button now, show remained time as "min : sec" format
        elif int(self.gidaTimeRemained) > 0 and gidaBasmaHakki == 0:
            self.btn1.text = "Gıda ({})".format(self.convertToMinSec(self.gidaTimeRemained))

    def kiyafetWait(self, *args):
        global kiyafetBasmaHakki

        self.kiyafetTimeRemained = str(int(self.kiyafetTimeRemained) - 1)

        # when timer ends, button is clicable again
        if int(self.kiyafetTimeRemained) <= 0:
            # reset variables to default
            kiyafetBasmaHakki = maxBasmaHakki
            self.kiyafetTimeRemained = "600"
            self.kiyafetClock.cancel()  # stop timer
            self.btn2.text = "Kıyafet {}".format("* " * kiyafetBasmaHakki)
            self.btn2.disabled = False

        # cant click button now, show remained time as "min : sec" format
        elif int(self.kiyafetTimeRemained) > 0 and kiyafetBasmaHakki == 0:
            self.btn2.text = "Kıyafet ({})".format(self.convertToMinSec(self.kiyafetTimeRemained))

    def convertToMinSec(self, seconds: str):
        minInt = int(seconds) // 60
        secInt = int(seconds) % 60
        minStr = ""
        secStr = ""

        if minInt // 10 == 0:
            minStr = "0" + str(minInt)
        else:
            minStr = str(minInt)

        if secInt // 10 == 0:
            secStr = "0" + str(secInt)
        else:
            secStr = str(secInt)

        minSec = "{} : {}".format(minStr, secStr)
        return minSec

        ##

    def openGoogleMaps(self, ins, value):
        print(value)
        if platform == 'android':
            import android
            android.open_url(value)
        elif platform == 'ios':
            pass
        else:
            import webbrowser
            webbrowser.open(value)

    # yardimTuru: 0 = ilkyardım, 1 = gida, 2 = kiyafet
    def dataGonder(self, yardimTuruArg):
        global yardimTuru

        # yardımTürü -1 se hiçbir tuş yardımTürünü değiştirmemiş demek, -1 den farklıysa yardimTürü kullanılıyor demek
        if yardimTuru == -1:
            yardimTuru = yardimTuruArg
            self.gps_basla()

    def gps_basla(self):
        try:
            gps.start()
        except NotImplementedError:
            self.fake_gps()  # starting fake gps to simulate app working on platforms lacking gps

        self.infoLabel.text = "GPS'ten konum bekleniyor..."

    def gps_dur(self):
        try:
            gps.stop()
        except NotImplementedError:
            print("gps could not be stopped, probably using fake_gps()")

    # for devices having no gps, avoid app from crashing
    def fake_gps(self):
        global konum, enYakinMerkez
        self.on_location(lat=89, lon=179)
        print("fake gps started")

    def on_location(self, **kwargs):
        global konum, enYakinMerkez, yardimTuru

        # gps konumu tespit edince, konum ve enYakinMerkez değerlerini bul
        lat = kwargs["lat"]
        lon = kwargs["lon"]
        konum = [lat, lon]
        enYakinMerkez = self.enYakinMerkeziBul()

        self.gps_dur()

        # update label in InfoScreen
        infoScreen.label1_1.text = "Sizin Konumunuz: {}\nEn Yakın Merkez Konumu: {}".format(konum,
                                                                                            enYakinMerkez)
        infoScreen.label2_1.text = "Durumu öğrenmek için 'Kontol et' e basın"

        # yardım talep edildiyse veriyi gönder
        if yardimTuru != -1:
            self.infoLabel.text = "{} için talep gönderiliyor".format(yardimTuruStr[yardimTuru])

            self.data = {"x": enYakinMerkez[0], "y": enYakinMerkez[1], "color": yardimTuru}
            self.data_json = json.dumps(self.data)
            self.url = postUrl  #"http://httpbin.org/post"  # "http://192.168.241.7:8080//api/data"

            # post request code
            self.r = UrlRequest(self.url, req_body=self.data_json, on_success=self.postSuccess,
                                on_failure=self.postFail, on_error=self.postFail, timeout=10)

    def postSuccess(self, *args):
        global yardimTuru, ilkYardimBasmaHakki, gidaBasmaHakki, kiyafetBasmaHakki

        self.infoLabel.text = "Talep Gönderildi"

        self.mapsUrl = "https://www.google.com/maps/dir/{},{}/{},{}/".format(konum[0], konum[1], enYakinMerkez[0],
                                                                             enYakinMerkez[1])
        self.mapLink.text = "[ref={}]Buraya Tıklayarak\nKargonun Geleceği Yere Gidin[/ref]".format(self.mapsUrl)
        self.mapLink.color = (0, 0, 1, 1)

        if yardimTuru == 0:
            # ilk basışta ve Timer başlar
            if ilkYardimBasmaHakki == maxBasmaHakki:
                self.ilkYardimTimerStart()

            ilkYardimBasmaHakki -= 1
            self.btn0.text = "İlk Yardım {}".format("* " * ilkYardimBasmaHakki)
            if ilkYardimBasmaHakki == 0:
                self.btn0.disabled = True
                self.btn0.disabled_color = (1, 0, 0, 1)

        if yardimTuru == 1:
            if gidaBasmaHakki == maxBasmaHakki:
                self.gidaTimerStart()

            gidaBasmaHakki -= 1
            self.btn1.text = "Gıda {}".format("* " * gidaBasmaHakki)
            if gidaBasmaHakki == 0:
                self.btn1.disabled = True
                self.btn1.disabled_color = (0.2, 0.6, 0.3, 1)

        if yardimTuru == 2:
            if kiyafetBasmaHakki == maxBasmaHakki:
                self.kiyafetTimerStart()

            kiyafetBasmaHakki -= 1
            self.btn2.text = "Kıyafet {}".format("* " * kiyafetBasmaHakki)
            if kiyafetBasmaHakki == 0:
                self.btn2.disabled = True
                self.btn2.disabled_color = (0.3, 0.3, 0.9, 1)

        yardimTuru = -1  # veri gönderimi tamamlanınca yardim türünü resetle

        print("post request BAŞARILI ! ", args)

    def postFail(self, *args):
        global yardimTuru, ilkYardimBasmaHakki, gidaBasmaHakki, kiyafetBasmaHakki

        self.infoLabel.text = "Talep Başarısız ! Tekrar Deneyin Lütfen"
        yardimTuru = -1  # veri gönderimi tamamlanınca yardim türünü resetle

        print("post request BAŞARISIZ ! ", args)

    def enYakinMerkeziBul(self):
        mesafeList = []  # her merkez için konuma olan mesafeyi içerecek liste

        for merkez in koordinatlar:
            # basit pisagor teoremi işlemi:
            mesafeList.append(((merkez[0] - konum[0]) ** 2 + (merkez[1] - konum[1]) ** 2) ** (1 / 2))

        enYakinMerkezIndex = mesafeList.index(min(mesafeList))
        enYakinMerkez = koordinatlar[enYakinMerkezIndex]

        return enYakinMerkez

    def changeToInfoScreen(self, ins):
        # update infoScreen
        labelKonum = ["???", "???"]
        labelEnYakinMerkezKonum = ["???", "???"]

        if konum != [91, 181]:
            labelKonum = konum
        if enYakinMerkez != [91, 181]:
            labelEnYakinMerkezKonum = enYakinMerkez

        infoScreen.label1_1.text = "Sizin Konumunuz: {}\nEn Yakın Merkez Konumu: {}".format(labelKonum,
                                                                                            labelEnYakinMerkezKonum)

        # change screen
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "info_screen"


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super(InfoScreen, self).__init__(**kwargs)
        self.bigFont = 25
        self.smallFont = 20
        self.baseLayout = FloatLayout()
        self.layout = BoxLayout(orientation="vertical",
                                spacing=10,
                                size_hint=(1, 0.5),
                                pos_hint={"center_x": 0.5, "top": 1})

        self.btn0 = Button(text="Menu'ye Dön",
                           color=(1, 1, 1, 1),
                           size_hint=(0.5, 0.1),
                           pos_hint={"center_x": 0.5, "center_y": 0.2},
                           on_release=self.changeToMainScreen
                           )
        self.label0 = Label(text="Kişisel Bilgiler:",
                            color=(1, 0, 0, 1),
                            )
        self.label0_1 = Label(text="İsim: {}".format(isim),
                              color=(0, 0, 0, 1)
                              )
        self.label1 = Label(text="Konum Bilgileri:",
                            color=(1, 0, 0, 1),
                            )
        self.label1_1 = Label(text="...",
                              color=(0, 0, 0, 1)
                              )
        self.label2 = Label(text="Kargo Durumu:",
                            color=(1, 0, 0, 1),
                            )
        self.label2_1 = Label(text="Kargo Durumu burada yazacak",
                              color=(0, 0, 0, 1),
                              )

        self.btn1 = Button(text="Kontrol et",
                           color=(1, 1, 1, 1),
                           size_hint=(0.5, 2),
                           pos_hint={"center_x": 0.5, "center_y": 0.2},
                           on_release=self.check_idCondition
                           )
        self.label3 = Label(text="Post URL linki:",
                            color=(1, 0, 0, 1)
                            )
        self.textInput0 = TextInput(text=postUrl,
                                    size_hint=(1, 2),
                                    )
        self.textInput0.bind(text=self.on_url_text_change)

        self.layout.add_widget(self.label0)
        self.layout.add_widget(self.label0_1)
        self.layout.add_widget(self.label1)
        self.layout.add_widget(self.label1_1)
        self.layout.add_widget(self.label2)
        self.layout.add_widget(self.label2_1)
        self.layout.add_widget(self.btn1)
        self.layout.add_widget(self.label3)
        self.layout.add_widget(self.textInput0)
        self.baseLayout.add_widget(self.layout)
        self.baseLayout.add_widget(self.btn0)
        self.add_widget(self.baseLayout)

    def changeToMainScreen(self, ins):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "main_screen"

    def on_url_text_change(self, ins, value):
        global postUrl
        postUrl = value
        print(postUrl)

    def initializeDatabaseConnection(self):
        try:
            # Initialize Firebase app with service account credentials
            if platform == "win":
                cred = credentials.Certificate("app/fireBaseKey1.json")
                firebase_admin.initialize_app(cred, {
                    'databaseURL': fireBaseUrl
                })
            if platform == "android":
                cred = credentials.Certificate(jsonKeyFileAndroid)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': fireBaseUrl
                })

            print("firebase app initialized")
        except Exception as e:
            print("Error, DataBase could not be initiliazed: ", e)

    def readfromDatabase(self, path):
        data = None

        try:
            ref = db.reference(path)
            data = ref.get()

        except Exception as e:
            print("Error, Data could not be readed: ", e)

        return data

    def check_idCondition(self, ins):
        global yardimTuru, konum, enYakinMerkez

        # is able to check for condition, are coordinates ready?
        if konum != [91, 181] and enYakinMerkez != [91, 181]:
            path = "/id/" + self.convertToHash(enYakinMerkez)
            data = self.readfromDatabase(path)

            self.label2_1.text = str(data)
            print("Data read: ", data, " Where data located in server: ", path)

        # if app dont know location: startsGps
        else:
            self.label2_1.text = "Konum bekleniyor..."
            mainScreen.gps_basla()
            # mainScreen.on_location()
            # konum, enYakinMerkez = [41, 34], [41, 34]
            yardimTuru = -1  # yardım istemeden konum alınacak

    def convertToHash(self, coordList):
        stringForHash = f"{coordList[0]}, {coordList[1]}"
        hash = hashlib.md5(stringForHash.encode()).hexdigest()

        return hash


# APP
mainScreen = MainScreen(name="main_screen")
infoScreen = InfoScreen(name="info_screen")


class MyApp(App):
    def on_start(self):
        # initialize firebase connection
        infoScreen.initializeDatabaseConnection()

        # gps configure on_start
        try:
            gps.configure(on_location=mainScreen.on_location)
            mainScreen.gps_basla()  # ilk başta konumu belirlemek için, normalde sadece yardım talep edilirken gps çalışıyor
            mainScreen.infoLabel.text = "GPS algılandı"
        except NotImplementedError:
            import traceback
            traceback.print_exc()
            mainScreen.infoLabel.text = "Platformunuzda GPS'e ulaşamadık"

    def request_android_permissions(self):
        """
        izinler verilmediyse request_android_permissions() çalışma esnasında bir popup gösterecek,
        verildiyse bir şey yapmayacak
        """
        from android.permissions import request_permissions, Permission

        def callback(permissions, results):
            """
            tüm izinlerin alınıp alınmadığını söyleyen geribildirim (callback)
            """
            if all([res for res in results]):
                print("Geri Bildirim: Tüm izinler alındı.")
            else:
                print("Geri Bildirim: Bazı izinler alınamadı.")

        request_permissions([Permission.ACCESS_COARSE_LOCATION,
                             Permission.ACCESS_FINE_LOCATION], callback)
        # # izinleri geribildirimsiz istemek için bunu kullanın:
        # request_permissions([Permission.ACCESS_COARSE_LOCATION,
        #                      Permission.ACCESS_FINE_LOCATION])

    def build(self):
        if platform == "android":
            print("android tespit edildi, izinler isteniyor...")
            self.request_android_permissions()

        # background color
        Window.clearcolor = (1, 1, 1, 1)

        sm.add_widget(mainScreen)
        sm.add_widget(infoScreen)

        return sm


if __name__ == "__main__":
    MyApp().run()

"""
Yapmam gerekenler:
dp, pixel density kivy, telefon pc ekranın aynı kalması
konum her zaman açık olsun
art arda isteklerde konuma tekrar bakılmayabilir
talep geçmişi
yeni talep esnasında maps linki silinip tekrar hazırlanabilir

Olası hatalar:
"""
