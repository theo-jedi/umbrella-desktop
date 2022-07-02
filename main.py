import firebase_admin
import qrcode
from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from firebase_admin import credentials
from firebase_admin import firestore


class UmbrellaDesktop(App):
    primary_color = (58 / 255, 68 / 255, 90 / 255, 1)
    surface_color = (1, 1, 1, 1)

    Window.title = "Umbrella Desktop"
    Window.clearcolor = surface_color

    api_stations = "stations"
    api_statuses = "auth"
    api_code = "securityWord"
    api_active = "active"
    api_status = "status"
    api_status_status = "status"
    api_status_umbrella = "umbrella"

    station1_id = "100_msk"
    station2_id = "101_msk"

    statuses = {
        "inactive": "Inactive",
        "waiting": "Ready",
        "giving": "User takes an umbrella",
        "returning": "User returns an umbrella"
    }

    statuses_colors = {
        "inactive": (58 / 255, 68 / 255, 90 / 255, 1),
        "waiting": (21 / 255, 176 / 255, 151 / 255, 1),
        "giving": (201 / 255, 112 / 255, 105 / 255, 1),
        "returning": (201 / 255, 112 / 255, 105 / 255, 1)
    }

    def __init__(self):
        super().__init__()

        self.count = "0"
        self.station1_code = ""
        self.station1_status = "waiting"
        self.station1_active = "inactive"
        self.station1_umbrella = "0"
        self.station2_code = ""
        self.station2_status = "waiting"
        self.station2_active = "inactive"
        self.station2_umbrella = "0"
        self.station1_status_label = Label(text="Ready")
        self.station2_status_label = Label(text="Ready")
        self.station1_qr_image = Image(source=self.station1_id + ".png", size=(500, 500))
        self.station2_qr_image = Image(source=self.station2_id + ".png")

        self.setup_auth()
        self.db = firestore.client()
        self.firestore_station1 = self.db.collection(self.api_stations).document(self.station1_id)
        self.firestore_station1_status = self.firestore_station1.collection(self.api_statuses).document(self.api_status)
        self.firestore_station2 = self.db.collection(self.api_stations).document(self.station2_id)
        self.firestore_station2_status = self.firestore_station2.collection(self.api_statuses).document(self.api_status)
        self.setup_firestore()

    # noinspection PyUnusedLocal
    def enable_station1(self, *args):
        self.firestore_station1.update({"active": 1})

    # noinspection PyUnusedLocal
    def disable_station1(self, *args):
        self.firestore_station1.update({"active": 0})

    # noinspection PyUnusedLocal
    def enable_station2(self, *args):
        self.firestore_station2.update({"active": 1})

    # noinspection PyUnusedLocal
    def disable_station2(self, *args):
        self.firestore_station2.update({"active": 0})

    @mainthread
    def update_station1_qr_code(self, code):
        qrcode.make(code).save(self.station1_id + ".png")
        self.station1_qr_image.reload()

    @mainthread
    def update_station2_qr_code(self, code):
        qrcode.make(code).save(self.station2_id + ".png")
        self.station2_qr_image.reload()

    def on_station1_qr_code_changed(self, doc_snapshot):
        code = doc_snapshot[0].get(self.api_code) + "-" + self.station1_id
        if self.station1_code != code:
            self.station1_code = code
            self.update_station1_qr_code(code)

    def on_station2_qr_code_changed(self, doc_snapshot):
        code = doc_snapshot[0].get(self.api_code) + "-" + self.station2_id
        if self.station2_code != code:
            self.station2_code = code
            self.update_station2_qr_code(code)

    def get_umbrella(self, doc_status):
        return str(doc_status.get(self.api_status_umbrella)) if self.api_status_umbrella in doc_status else ""

    def get_status_data(self, doc_snapshot):
        doc_status = doc_snapshot[0]
        status = doc_status.get(self.api_status_status)
        umbrella = self.get_umbrella(doc_status.to_dict())
        return status, umbrella

    def get_status_message(self, status, umbrella):
        message = self.statuses.get(status)
        if status != "inactive" and status != "waiting" and umbrella != "" and umbrella != "0":
            message += " (" + str(umbrella) + ")"
        color = self.statuses_colors.get(status)
        return message, color

    def update_station1_status(self, status, umbrella):
        if self.station1_active != "inactive" or status == "inactive":
            message, color = self.get_status_message(status, umbrella)
            self.station1_status_label.text = message
            self.station1_status_label.color = color

    def update_station2_status(self, status, umbrella):
        if self.station2_active != "inactive" or status == "inactive":
            message, color = self.get_status_message(status, umbrella)
            self.station2_status_label.text = message
            self.station2_status_label.color = color

    # noinspection PyUnusedLocal
    def on_station1_status_changed(self, doc_snapshot, changes, read_time):
        status, umbrella = self.get_status_data(doc_snapshot)
        self.station1_status = status
        self.station1_umbrella = umbrella
        self.update_station1_status(status, umbrella)

    # noinspection PyUnusedLocal
    def on_station2_status_changed(self, doc_snapshot, changes, read_time):
        status, umbrella = self.get_status_data(doc_snapshot)
        self.station2_status = status
        self.station2_umbrella = umbrella
        self.update_station2_status(status, umbrella)

    def get_active_status(self, doc_snapshot):
        if self.api_active in doc_snapshot[0].to_dict() and doc_snapshot[0].get(self.api_active) == 1:
            return "active"
        else:
            return "inactive"

    def on_station1_active_changed(self, doc_snapshot):
        status = self.get_active_status(doc_snapshot)
        if self.station1_active != status:
            self.station1_active = status
            if status == "active":
                self.update_station1_status(self.station1_status, self.station1_umbrella)
            elif status == "inactive":
                self.update_station1_status(status, "")

    def on_station2_active_changed(self, doc_snapshot):
        status = self.get_active_status(doc_snapshot)
        if self.station2_active != status:
            self.station2_active = status
            if status == "active":
                self.update_station2_status(self.station2_status, self.station2_umbrella)
            elif status == "inactive":
                self.update_station2_status(status, "")

    # noinspection PyUnusedLocal
    def on_station1_changed(self, doc_snapshot, changes, read_time):
        self.on_station1_qr_code_changed(doc_snapshot)
        self.on_station1_active_changed(doc_snapshot)

    # noinspection PyUnusedLocal
    def on_station2_changed(self, doc_snapshot, changes, read_time):
        self.on_station2_qr_code_changed(doc_snapshot)
        self.on_station2_active_changed(doc_snapshot)

    # noinspection PyMethodMayBeStatic
    def setup_auth(self):
        local_credentials = credentials.Certificate("api_key.json")
        firebase_admin.initialize_app(local_credentials)

    def setup_firestore(self):
        self.firestore_station1.on_snapshot(self.on_station1_changed)
        self.firestore_station1_status.on_snapshot(self.on_station1_status_changed)
        self.firestore_station2.on_snapshot(self.on_station2_changed)
        self.firestore_station2_status.on_snapshot(self.on_station2_status_changed)

    def build(self):
        main_box = BoxLayout(orientation="vertical")
        header_box = BoxLayout()
        info_box = BoxLayout()
        qr_box = BoxLayout()
        statuses_box = BoxLayout()
        actions_box = BoxLayout()

        app_label = Button(text="Umbrella | Admin Panel", background_color=(144 / 255, 161 / 255, 220 / 255, 1))
        header_box.add_widget(app_label)

        station1_title_label = Label(text="Station 1")
        station2_title_label = Label(text="Station 2")
        station1_title_label.color = self.primary_color
        station2_title_label.color = self.primary_color
        info_box.add_widget(station1_title_label)
        info_box.add_widget(station2_title_label)

        qr_box.add_widget(self.station1_qr_image)
        qr_box.add_widget(self.station2_qr_image)

        self.station1_status_label.color = self.primary_color
        self.station2_status_label.color = self.primary_color
        statuses_box.add_widget(self.station1_status_label)
        statuses_box.add_widget(self.station2_status_label)

        station1_enable_button = Button(text="Enable", background_color=(180 / 255, 180 / 255, 180 / 255, 1))
        station1_disable_button = Button(text="Disable", background_color=(180 / 255, 180 / 255, 180 / 255, 1))
        station2_enable_button = Button(text="Enable", background_color=(180 / 255, 180 / 255, 180 / 255, 1))
        station2_disable_button = Button(text="Disable", background_color=(180 / 255, 180 / 255, 180 / 255, 1))
        station1_enable_button.bind(on_release=self.enable_station1)
        station1_disable_button.bind(on_release=self.disable_station1)
        station2_enable_button.bind(on_release=self.enable_station2)
        station2_disable_button.bind(on_release=self.disable_station2)
        actions_box.add_widget(station1_enable_button)
        actions_box.add_widget(station1_disable_button)
        actions_box.add_widget(station2_enable_button)
        actions_box.add_widget(station2_disable_button)

        main_box.add_widget(header_box)
        main_box.add_widget(info_box)
        main_box.add_widget(qr_box)
        main_box.add_widget(statuses_box)
        main_box.add_widget(actions_box)

        return main_box


if __name__ == "__main__":
    UmbrellaDesktop().run()
