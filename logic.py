from ignis.variable import Variable
from ignis.utils import Utils
from enum import Enum


class Transform(Enum):
    NORMAL = "normal"
    ROTATE_90 = "90"
    ROTATE_180 = "180"
    ROTATE_270 = "270"
    FLIPPED = "flipped"
    FLIPPED_90 = "flipped-90"
    FLIPPED_180 = "flipped-180"
    FLIPPED_270 = "flipped-270"


class display_data:
    def __init__(self, wlr_json: dict):
        js = wlr_json
        self.name: str = js.get("name") or "Unknown"
        self.enabled: bool = js.get("enabled") or False
        self.modes: list[dict] = js.get("modes") or [
            {"width": 0, "height": 0, "refresh": 0, "current": True}
        ]
        self.transforms: list[str] = [
            "normal",
            "90",
            "180",
            "270",
            "flipped",
            "flipped-90",
            "flipped-180",
            "flipped-270",
        ]
        try:
            self.x = js.get("position")["x"]
            self.y = js.get("position")["y"]
        except:
            self.x = 0
            self.y = 0

        self.mode = self.modes[0]
        for i, j in enumerate(self.modes):
            if j.get("current"):
                self.mode = j
                self.modes.pop(i)
                self.modes = [self.mode] + self.modes

        self.scale: float = js.get("scale") or 1
        self.transform = js.get("transform") or "normal"
        self.width = self.mode.get("width")
        self.height = self.mode.get("height")
        self.refresh = self.mode.get("refresh")


class Logic:
    def __init__(self):
        self.name = Variable()
        self.modes = Variable()
        self.x = Variable()
        self.y = Variable()
        self.scale = Variable()

    def set_display_data(self, display):
        self.disp = display
        self.x.set_value(display.data.x)
        self.y.set_value(display.data.y)
        self.name.set_value(display.data.name)
        self.scale.set_value(display.data.scale)
        self.modes.set_value(
            [f"{j['width']}x{j['height']}@{j['refresh']}" for j in display.data.modes]
        )

    def apply_cmd(self, data):
        cmd = f"wlr-randr --output {data.name} --pos {int(data.x)},{int(data.y)} --scale {data.scale} {'--on' if data.enabled else '--off'} --mode {data.width}x{data.height}@{data.refresh}"
        print(f"Executing '{cmd}'")
        Utils.exec_sh(cmd)
