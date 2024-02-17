from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy_garden.mapview import MapView, MapMarker

class ControlStation(App):
    def __init__(self, **kwargs):
        super(ControlStation, self).__init__(**kwargs)
        self.autonomous_mission_started = False

    def build(self):
        # initialize
        self.green_lines = []
        self.blue_lines = []
        self.red_lines = []
        self.connected = False
        self.manuel_mod = True
        self.autonom_mod = False
        self.mission_completed = True
        self.flag = False
        layout = FloatLayout()

        # MAP
        self.mapview = MapView(zoom=10, lat=40.99, lon=28.796361)
        self.mapview.size_hint = (0.8, 0.6)
        self.mapview.pos_hint = {"right": 1, "top": 1}
        layout.add_widget(self.mapview)

        # LOGO
        logo = AsyncImage(source='balsa.jpeg', size_hint=(None, None), size=(100, 100), pos_hint={'right': 1, 'top': 1})
        layout.add_widget(logo)

        # BUTTONS
        buttons_layout = BoxLayout(orientation="vertical", size_hint=(0.2, 1), pos_hint={"left": 1, "bottom": 1})

        button_texts = ["BAGLAN", "MANUEL MOD", "TAM OTONOM", "SIRADAKİ GÖREVİ YAP", "GELDİĞİNİ BİLDİR", "YUVAYA DÖN"]
        button_colors = [(0, 1, 0, 1), (0, 0, 1, 1), (0, 0, 1, 1), (0, 1, 1, 1), (0, 1, 1, 1), (1, 0, 0, 1)]
        for text, color in zip(button_texts, button_colors):
            button = Button(text=text, background_color=color)
            buttons_layout.add_widget(button)
            # PRESSED
            button.bind(on_press=self.on_button_press)

        layout.add_widget(buttons_layout)

        # MISSONS
        label_layout = BoxLayout(orientation="vertical", size_hint=(0.25, 0.4), pos_hint={"right": 0.45, "bottom": 0.6})

        self.mssn1 = Label(text="Missions Uploading...")
        self.mssn2 = Label(text="Missions Uploading...")
        self.mssn3 = Label(text="Missions Uploading...")
        
        # Background
        with self.mssn1.canvas.before:
            Color(0.8, 0, 0, 1)  # red
            self.rect1 = Rectangle(pos=self.mssn1.pos, size=self.mssn1.size)
        with self.mssn2.canvas.before:
            Color(0, 0.5, 0, 1)  # green
            self.rect2 = Rectangle(pos=self.mssn2.pos, size=self.mssn2.size)
        with self.mssn3.canvas.before:
            Color(0, 0, 0.8, 1)  # blue
            self.rect3 = Rectangle(pos=self.mssn3.pos, size=self.mssn3.size)

        self.mssn1.bind(size=self.update_rect1, pos=self.update_rect1)
        self.mssn2.bind(size=self.update_rect2, pos=self.update_rect2)
        self.mssn3.bind(size=self.update_rect3, pos=self.update_rect3)

        # Adding Layout
        label_layout.add_widget(self.mssn1)
        label_layout.add_widget(self.mssn2)
        label_layout.add_widget(self.mssn3)

        layout.add_widget(label_layout)


        # INFORMATION ABOUT DRONE
        label_layout2 = BoxLayout(orientation="vertical", size_hint=(0.55, 0.4), pos_hint={"right": 1, "bottom": 1})

        self.infoDrone = Label(text="IHA DURUM BILGILERI")
        
        with self.infoDrone.canvas.before:
            Color(0.2, 0, 0, 1)
            self.rect4 = Rectangle(pos=self.infoDrone.pos, size=self.infoDrone.size)

        self.infoDrone.bind(size=self.update_rect4, pos=self.update_rect4)

        # Adding Layout
        label_layout2.add_widget(self.infoDrone)
        layout.add_widget(label_layout2)

        # READ LOG FILE
        self.readLog()
        Clock.schedule_interval(lambda dt: self.missions(), 5)

        return layout

    def autonomous_mode_start(self):
        if not self.autonomous_mission_started:
            print("Otomatik görevler başlatıldı")
            self.autonomous_mission_started = True
            self.current_autonomous_task = Clock.schedule_interval(self.missionStart, 5)

    def autonomous_mode_stop(self):
        if self.autonomous_mission_started:
            print("Otomatik görevler durduruldu")
            self.autonomous_mission_started = False
            if self.current_autonomous_task:
                Clock.unschedule(self.current_autonomous_task)
                self.current_autonomous_task = None

    def on_button_press(self, button):
        try:
            # CONNECTION
            if button.text != "BAGLAN" and not self.connected:
                raise Exception("Önce BAGLAN butonuna basınız.")

            elif button.text == "BAGLAN":
                self.connected = True
                self.infoDrone.text = "BAĞLANTI BAŞARILI"
                self.marker1 = MapMarker(lat=41.008238, lon=28.978357, source="heli.png")
                self.mapview.add_marker(self.marker1)
            
            # NEXT MISSION
            if button.text == "SIRADAKİ GÖREVİ YAP" and self.connected and self.manuel_mod:
                self.missionStart()

            # CHANGE MODE (MANUEL MODE)
            if button.text == "MANUEL MOD" and not self.manuel_mod:
                self.infoDrone.text = "MANUEL MODA GEÇİLDİ"
                print("MANUEL MODA GEÇİLDİ")
                self.manuel_mod = True
                self.autonomous_mode_stop()

            # CHANGE MODE (AUTONOMOUS MODE)
            if button.text == "TAM OTONOM":
                self.infoDrone.text = "TAM OTONOM MODA GEÇİLDİ"
                print("TAM OTONOM MODA GEÇİLDİ")
                self.manuel_mod = False
                self.autonom_mod = True
                self.autonomous_mode_start()
            # OTHER
            print(f"{button.text} button pressed")
        except Exception as e:
            print(e)

    def missionStart(self, *args):
        if(len(self.red_lines)>0):
            self.mssn1.text = f"Yapılan görev:\n {self.red_lines[0][0]} {self.red_lines[0][1]}"
            if self.flag:
                self.mapview.remove_marker(self.marker2)
            else:    
                self.flag = True
            self.marker2 = MapMarker(lat=self.red_lines[0][0], lon=self.red_lines[0][1], color=(1, 0, 0, 1))
            self.mapview.add_marker(self.marker2)
            self.flag = True
            self.red_lines.pop(0)
        elif(len(self.green_lines)>0):
            if self.flag:
                self.mapview.remove_marker(self.marker2)
            else:    
                self.flag = True
            self.marker2 = MapMarker(lat=self.green_lines[0][0], lon=self.green_lines[0][1], color=(0, 1, 0, 1))
            self.mapview.add_marker(self.marker2)
            self.mssn2.text = f"Yapılan görev:\n {self.green_lines[0][0]} {self.green_lines[0][1]}"
            self.green_lines.pop(0)
        elif(len(self.blue_lines)>0):
            if self.flag:
                self.mapview.remove_marker(self.marker2)
            else:    
                self.flag = True
            self.mapview.remove_marker(self.marker2)
            self.marker2 = MapMarker(lat=self.blue_lines[0][0], lon=self.blue_lines[0][1], color=(0, 0, 1, 1))
            self.mapview.add_marker(self.marker2)
            self.mssn3.text = f"Yapılan görev:\n {self.blue_lines[0][0]} {self.blue_lines[0][1]}"
            self.blue_lines.pop(0)
        else:
            self.mapview.remove_marker(self.marker2)
            print("YAPİLACAK GÖREV YOK")

    def update_rect1(self, instance, value):
        """
        continuous update function for rect1
        """
        self.rect1.pos = instance.pos
        self.rect1.size = instance.size

    def update_rect2(self, instance, value):
        """
        continuous update function for rect2
        """
        self.rect2.pos = instance.pos
        self.rect2.size = instance.size

    def update_rect3(self, instance, value):
        """
        continuous update function for rect3
        """
        self.rect3.pos = instance.pos
        self.rect3.size = instance.size

    def update_rect4(self, instance, value):
        """
        continuous update function for rect4
        """
        self.rect4.pos = instance.pos
        self.rect4.size = instance.size

    def readLog(self):
        with open("log.txt", "r") as file:
            lines = file.readlines()

        # SPLIT LINES
        for line in lines:
            parts = line.split(", ")
            x = float(parts[0].split(": ")[1])
            y = float(parts[1].split(": ")[1])
            color = int(parts[2].split(": ")[1])

            # Add to related list by color value
            if color == 1:
                self.red_lines.append((x, y))  
            elif color == 2:
                self.blue_lines.append((x, y))
            elif color == 3:
                self.green_lines.append((x, y))

    def missions(self):
        # Red Mission
        if(len(self.red_lines)==0):
            self.mssn1.text = f"YAPİLACAK GÖREV YOK"
        else:
            self.mssn1.text = f"X: {self.red_lines[0][0]}, Y: {self.red_lines[0][1]}"
        # Green Mission
        if(len(self.green_lines)==0):
            self.mssn2.text = f"YAPİLACAK GÖREV YOK"
        else:
            self.mssn2.text = f"X: {self.green_lines[0][0]}, Y: {self.green_lines[0][1]}"
        # Blue Mission
        if(len(self.blue_lines)==0):
            self.mssn3.text = f"YAPİLACAK GÖREV YOK"
        else:
            self.mssn3.text = f"X: {self.blue_lines[0][0]}, Y: {self.blue_lines[0][1]}"


if __name__ == '__main__':
    Window.clearcolor = (0.5, 0.5, 0.5, 1)
    ControlStation().run()

