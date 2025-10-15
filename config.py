# TODO Fix snap to displays and edge jitter (partially solved)
# TODO Unified logic
# - Changing settings updates visual
# TODO Display transform
# TODO Collision
# TODO Toggle collision
import json
from logic import Logic, display_data
import gi
import operator
from gi.repository import Gtk
from ignis.widgets import Widget
from ignis.app import IgnisApp
from ignis.utils import Utils

gi.require_version("Gtk", "4.0")


class DisplayControl(Widget.Box):
    def __init__(self, glob: Logic):
        super().__init__(
            valign="start",
            hexpand=True,
            css_classes=["monitor", "box"],
        )
        self.glob = glob
        self.display_scale = 0.2
        self.plane = Gtk.Fixed()
        self.plane.set_hexpand(True)
        self.plane.set_css_classes(["monitor", "fixed"])
        self.set_child([self.plane])
        self.plane_child = []

    def on_begin(self, disp):
        self.diff = tuple(
            map(
                operator.sub,
                self.plane.get_child_position(disp),
                self.get_plane_pos(),
            )
        )

    def on_update(self, disp):
        move = map(operator.add, self.get_plane_pos(), self.diff)
        self.glob.disp = disp
        px, py = self.get_plane_pos()

        # bounding the movable widget inside the GtkFixed container
        max_width = self.plane.get_width() - disp.get_width()
        max_height = self.plane.get_height() - disp.get_height()
        move_x, move_y = map(min, (max_width, max_height), map(max, (0, 0), move))
        snap_range = 10

        # edge snap
        if move_x <= snap_range:
            move_x = 0
        if move_x >= self.plane.get_width() - snap_range - disp.get_width():
            move_x = self.plane.get_width() - disp.get_width()
        if move_y <= snap_range:
            move_y = 0
        if move_y >= self.plane.get_height() - snap_range - disp.get_height():
            move_y = self.plane.get_height() - disp.get_height()

        # display snap
        target = self.plane.get_child_position(disp)
        for i in self.plane_child:
            pos = self.plane.get_child_position(i)
            if pos != target:
                # Outer
                if (
                    move_x <= pos[0] + i.get_width() + snap_range
                    and move_x >= pos[0] + i.get_width() - snap_range
                ):
                    move_x = pos[0] + i.get_width()
                if (
                    move_y <= pos[1] + i.get_height() + snap_range
                    and move_y >= pos[1] + i.get_height() - snap_range
                ):
                    move_y = pos[1] + i.get_height()
                if (
                    move_x + disp.get_width() <= pos[0] + snap_range
                    and move_x + disp.get_width() >= pos[0] - snap_range
                ):
                    move_x = pos[0] - disp.get_width()
                if (
                    move_y + disp.get_height() >= pos[1] - snap_range
                    and move_y + disp.get_height() <= pos[1] + snap_range
                ):
                    move_y = pos[1] - disp.get_height()

                # Inner
                if move_x <= pos[0] + snap_range and move_x > pos[0]:
                    move_x = pos[0] - 0.01

                if move_y <= pos[1] + snap_range and move_y > pos[1]:
                    move_y = pos[1] - 0.01
                if (
                    move_y + disp.get_height() <= pos[1] + i.get_height() + snap_range
                    and move_y + disp.get_height()
                    >= pos[1] + i.get_height() - snap_range
                ):
                    move_y = pos[1] + i.get_height() - disp.get_height()
                if (
                    move_x + disp.get_width() >= pos[0] + i.get_width() - snap_range
                    and move_x + disp.get_width() <= pos[0] + i.get_width() + snap_range
                ):
                    move_x = pos[0] + i.get_width() - disp.get_width()

        self.plane.move(disp, move_x, move_y)
        disp.data.x = move_x / self.display_scale
        disp.data.y = move_y / self.display_scale
        self.glob.x.set_value(disp.data.x)
        self.glob.y.set_value(disp.data.y)

    def set_pos(self, disp, x, y):
        disp.data.x = x
        disp.data.y = y
        move_x = x * self.display_scale
        move_y = y * self.display_scale
        self.plane.move(
            disp,
            move_x,
            move_y,
        )

    def set_mode(self, disp, w, h, refresh):
        disp.set_style(
            f"min-width:{w * self.display_scale / disp.data.scale}px;min-height:{h * self.display_scale / disp.data.scale}px;"
        )
        disp.data.width = w
        disp.data.height = h
        disp.data.refresh = refresh

    def set_scale(self, disp, scale):
        disp.data.scale = scale
        self.set_mode(
            disp,
            disp.data.mode["width"],
            disp.data.mode["height"],
            disp.data.refresh,
        )

    def add_display(self, disp_data: display_data):
        data = disp_data
        disp = Widget.EventBox(
            child=[
                Widget.Label(
                    label=data.name,
                    halign="center",
                    hexpand=True,
                )
            ],
            style=f"min-width:{data.width * self.display_scale / data.scale}px;min-height:{data.height * self.display_scale / data.scale}px;",
            css_classes=["monitor", "display"],
        )
        disp.data = data
        controller = Gtk.GestureDrag()
        controller.connect(
            "drag-begin",
            lambda *args: self.on_begin(disp),
        )
        controller.connect(
            "drag-update",
            lambda *args: self.on_update(disp),
        )
        disp.add_controller(controller)
        controller = Gtk.GestureClick()
        controller.connect(
            "pressed",
            lambda *args: self.glob.set_display_data(disp),
        )
        disp.add_controller(controller)
        self.plane.put(
            disp,
            data.x * self.display_scale,
            data.y * self.display_scale,
        )
        self.plane_child.append(disp)

    def clear_displays(self):
        [self.plane.remove(i) for i in self.plane_child]
        self.plane_child = []

    def get_plane_pos(self):
        pointer = self.get_display().get_default_seat().get_pointer()
        _, px, py, _ = (
            self.plane.get_native().get_surface().get_device_position(pointer)
        )
        coords = self.translate_coordinates(self.plane, px, py)
        return coords


class MainWindow(Widget.RegularWindow):
    def __init__(self, glob: Logic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.glob = glob
        self.set_default_size(1920 // 2, 1080 // 2)
        self.set_title("Display tool")

        # Display positions
        self.disp_ctrl = DisplayControl(self.glob)
        [self.disp_ctrl.add_display(i) for i in self.get_wlr()]
        self.glob.set_display_data(self.disp_ctrl.plane_child[0])

        # Settings
        self.disp_name = Widget.Label(
            label=self.glob.name.bind("value"), halign="start"
        )
        self.disp_modes = Widget.DropDown(
            items=self.glob.modes.bind("value"),
            on_selected=lambda x, selected: self.disp_ctrl.set_mode(
                self.glob.disp,
                int(selected[: selected.find("x")]),
                int(selected[selected.find("x") + 1 : selected.find("@")]),
                float(selected[selected.find("@") + 1 :]),
            ),
        )
        self.disp_x = Widget.SpinButton(
            min=0,
            max=1920 * 2,
            step=1,
            digits=3,
            value=self.glob.x.bind("value"),
            on_change=lambda x, y: self.disp_ctrl.set_pos(
                self.glob.disp, y, self.glob.disp.data.y
            ),
        )
        self.disp_y = Widget.SpinButton(
            min=0,
            max=1920 * 2,
            digits=3,
            step=1,
            value=self.glob.y.bind("value"),
            on_change=lambda x, y: self.disp_ctrl.set_pos(
                self.glob.disp, self.glob.disp.data.x, y
            ),
        )
        self.disp_scale = Widget.SpinButton(
            min=0.1,
            max=2.0,
            step=0.01,
            digits=3,
            value=self.glob.scale.bind("value"),
            on_change=lambda x, y: self.disp_ctrl.set_scale(self.glob.disp, y),
        )
        self.disp_en = Widget.ToggleButton(
            label="Enable",
            on_toggled=lambda x, active: setattr(
                self.glob.disp.data, "enabled", active
            ),
            active=self.glob.disp.data.enabled,
        )
        self.disp_apply = Widget.Button(
            label="Apply settings",
            on_click=lambda x: (
                [self.glob.apply_cmd(i.data) for i in self.disp_ctrl.plane_child],
                self.disp_ctrl.clear_displays(),
                [self.disp_ctrl.add_display(i) for i in self.get_wlr()],
            ),
        )

        self.sett_box = Widget.Box(
            child=[
                self.disp_name,
                self.disp_modes,
                self.disp_x,
                self.disp_y,
                self.disp_scale,
                self.disp_en,
                self.disp_apply,
            ],
            vexpand=True,
            vertical=True,
            css_classes=["monitor", "sett"],
            spacing=10,
            hexpand=True,
        )

        # Group
        self.set_child(Widget.Box(child=[self.disp_ctrl, self.sett_box], vertical=True))

    def get_wlr(self):
        return [
            display_data(i)
            for i in json.loads(Utils.exec_sh("wlr-randr --json").stdout)
        ]


app = IgnisApp.get_default()
app.apply_css("/home/newor/code/display_settings/style.scss")
glob = Logic()
MainWindow(glob, namespace="Monitor IGNIS")
