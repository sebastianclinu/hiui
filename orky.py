import base64
import random
import requests
from seleniumbase import SB

class TwitchAutomation:
    def __init__(self, encoded_name):
        self.target_url = self._generate_url(encoded_name)
        self.geo_config = self._get_geo_data()

    def _generate_url(self, encoded_name):
        """Decodează numele și returnează URL-ul canalului."""
        decoded_name = base64.b64decode(encoded_name).decode("utf-8")
        return f"https://www.twitch.tv/{decoded_name}"

    def _get_geo_data(self):
        """Preia datele geografice pentru sincronizarea browserului."""
        try:
            response = requests.get("http://ip-api.com/json/", timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "timezone": data.get("timezone"),
                "proxy": None  # Setat pe None în loc de False pentru claritate
            }
        except Exception as e:
            print(f" Eroare la preluarea datelor geo: {e}")
            return None

    def handle_overlays(self, driver):
        """Gestionează butoanele de tip 'Accept' sau 'Start Watching'."""
        buttons = ["Accept", "Start Watching"]
        for btn_text in buttons:
            selector = f'button:contains("{btn_text}")'
            if driver.is_element_present(selector):
                driver.cdp.click(selector, timeout=4)
                driver.sleep(2)

    def run_session(self):
        """Lansează sesiunea principală de automatizare."""
        if not self.geo_config:
            return

        # Configurații pentru instanța de browser
        sb_config = {
            "uc": True,
            "locale": "en",
            "ad_block": True,
            "chromium_arg": "--disable-webgl",
            "proxy": self.geo_config["proxy"]
        }

        while True:
            with SB(**sb_config) as sb:
                # Activare mod CDP cu datele geo locale
                sb.activate_cdp_mode(
                    self.target_url, 
                    tzone=self.geo_config["timezone"],
                    geoloc=(self.geo_config["lat"], self.geo_config["lon"])
                )
                
                sb.sleep(5)
                self.handle_overlays(sb)

                # Verifică dacă stream-ul este activ
                if sb.is_element_present("#live-channel-stream-information"):
                    # Deschide un driver secundar dacă este necesar
                    self._run_secondary_driver(sb)
                    
                    # Timp de vizionare randomizat (între 7.5 și 13 minute)
                    watch_time = random.randint(450, 800)
                    print(f"Sesiune activă. Vizionare timp de {watch_time} secunde...")
                    sb.sleep(watch_time)
                else:
                    print("Canalul nu pare să fie live. Închidere...")
                    break

    def _run_secondary_driver(self, master_sb):
        """Gestionează o a doua instanță de driver în paralel."""
        try:
            driver2 = master_sb.get_new_driver(undetectable=True)
            driver2.activate_cdp_mode(
                self.target_url, 
                tzone=self.geo_config["timezone"],
                geoloc=(self.geo_config["lat"], self.geo_config["lon"])
            )
            driver2.sleep(10)
            self.handle_overlays(driver2)
        except Exception as e:
            print(f"Eroare driver secundar: {e}")

if __name__ == "__main__":
    # Numele de utilizator codificat
    ENCODED_TARGET = "YnJ1dGFsbGVz"
    
    bot = TwitchAutomation(ENCODED_TARGET)
    bot.run_session()
