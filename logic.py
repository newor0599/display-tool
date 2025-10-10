from ignis.variable import Variable
from ignis.utils import Utils


class display_data:
    def __init__(self, wlr_json: dict):
        js = wlr_json
        self.name: str = js.get("name") or "Unknown"
        self.enabled: bool = js.get("enabled") or False
        self.modes: list[dict] = js.get("modes") or [
            {"width": 0, "height": 0, "refresh": 0, "current": True}
        ]
        try:
            self.x = js.get("position")["x"]
            self.y = js.get("position")["y"]
        except:
            self.x = 0
            self.y = 0

        self.scale: float = js.get("scale") or 1
        self.transform = js.get("transform") or "normal"
        self.cur_mode = self.get_cur_mode(self.modes)
        self.width = self.cur_mode.get("width")
        self.height = self.cur_mode.get("height")
        self.refresh = self.cur_mode.get("refresh")

    def get_cur_mode(self, modes: list[dict]):
        for i in modes:
            if i.get("current"):
                return i


class Logic:
    def __init__(self):
        self.name = Variable()
        self.modes = Variable()
        self.x = Variable()
        self.y = Variable()
        self.scale = Variable()
        self.data = display_data({})
        self.update_sett(self.data)

    def update_sett(self, data):
        self.data = data
        self.name.set_value(self.data.name)
        self.modes.set_value(
            [f"{i['width']}x{i['height']}@{i['refresh']}" for i in self.data.modes]
        )
        self.x.set_value(self.data.x)
        self.y.set_value(self.data.y)
        self.scale.set_value(self.data.scale * 100)

    def apply(self, data):
        cmd = f"wlr-randr --output {data.name} --pos {int(data.x)},{int(data.y)}"
        print(f"Executing '{cmd}'")
        Utils.exec_sh(cmd)
