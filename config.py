# TODO Fix snap to displays and edge jitter (partially solved)
# TODO Unified logic
# - Changing settings updates visual
# TODO Display transform
# TODO Collision
# TODO Toggle collision
import json
from logic import Logic, display_data
from typing import Callable
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
        self.glob.update_sett(disp.data)

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
        disp.data.x = self.plane.get_child_position(disp)[0] / self.display_scale
        disp.data.y = self.plane.get_child_position(disp)[1] / self.display_scale
        self.glob.update_sett(disp.data)

    def add_display(self, disp_data: display_data, sett_update: Callable):
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
            lambda *args: self.glob.update_sett(disp.data),
        )
        disp.add_controller(controller)
        self.plane.put(
            disp,
            data.x * self.display_scale,
            data.y * self.display_scale,
        )
        self.plane_child.append(disp)

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
        self.set_title("Test Drag & Drop")

        # Display positions
        self.disp_ctrl = DisplayControl(self.glob)
        wlrs = json.loads(Utils.exec_sh("wlr-randr --json").stdout)
        tmp_disp = '{ "name": "HDMI-A-1", "description": "Daewoo Electronics Company Ltd HDMI 0 (HDMI-A-1)", "make": "Daewoo Electronics Company Ltd", "model": "HDMI", "serial": "0", "physical_size": { "width": 340, "height": 190 }, "enabled": true, "modes": [ { "width": 1366, "height": 768, "refresh": 59.790001, "preferred": true, "current": true }, { "width": 1920, "height": 1080, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 1920, "height": 1080, "refresh": 59.939999, "preferred": false, "current": false }, { "width": 1920, "height": 1080, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 1920, "height": 1080, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 1280, "height": 720, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 1280, "height": 720, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 1280, "height": 720, "refresh": 59.939999, "preferred": false, "current": false }, { "width": 1280, "height": 720, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 1280, "height": 720, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 1024, "height": 768, "refresh": 75.028999, "preferred": false, "current": false }, { "width": 1024, "height": 768, "refresh": 72.003998, "preferred": false, "current": false }, { "width": 1024, "height": 768, "refresh": 70.069000, "preferred": false, "current": false }, { "width": 1024, "height": 768, "refresh": 60.004002, "preferred": false, "current": false }, { "width": 960, "height": 720, "refresh": 59.966999, "preferred": false, "current": false }, { "width": 832, "height": 624, "refresh": 74.551003, "preferred": false, "current": false }, { "width": 800, "height": 600, "refresh": 75.000000, "preferred": false, "current": false }, { "width": 800, "height": 600, "refresh": 72.188004, "preferred": false, "current": false }, { "width": 800, "height": 600, "refresh": 60.317001, "preferred": false, "current": false }, { "width": 800, "height": 600, "refresh": 56.250000, "preferred": false, "current": false }, { "width": 720, "height": 576, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 720, "height": 576, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 720, "height": 576, "refresh": 50.000000, "preferred": false, "current": false }, { "width": 720, "height": 480, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 720, "height": 480, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 720, "height": 480, "refresh": 59.939999, "preferred": false, "current": false }, { "width": 720, "height": 480, "refresh": 59.939999, "preferred": false, "current": false }, { "width": 640, "height": 480, "refresh": 75.000000, "preferred": false, "current": false }, { "width": 640, "height": 480, "refresh": 72.808998, "preferred": false, "current": false }, { "width": 640, "height": 480, "refresh": 66.667000, "preferred": false, "current": false }, { "width": 640, "height": 480, "refresh": 60.000000, "preferred": false, "current": false }, { "width": 640, "height": 480, "refresh": 59.939999, "preferred": false, "current": false }, { "width": 720, "height": 400, "refresh": 70.082001, "preferred": false, "current": false } ], "position": { "x": 0, "y": 0 }, "transform": "normal", "scale": 1.000000, "adaptive_sync": false }'
        # wlrs.append(json.loads(tmp_disp))
        [
            self.disp_ctrl.add_display(display_data(i), self.glob.update_sett)
            for i in wlrs
        ]

        # Settings
        self.data = display_data({})
        self.disp_name = Widget.Label(
            label=self.glob.name.bind("value"), halign="start"
        )
        self.disp_modes = Widget.DropDown(
            items=self.glob.modes.bind(
                "value",
            ),
        )
        self.disp_x = Widget.SpinButton(
            min=0,
            max=1920 * 2,
            step=1,
            value=self.glob.x.bind("value"),
        )
        self.disp_y = Widget.SpinButton(
            min=0,
            max=1920 * 2,
            step=1,
            value=self.glob.y.bind("value"),
        )
        self.disp_scale = Widget.SpinButton(
            min=1,
            max=200,
            step=1,
            value=self.glob.scale.bind("value"),
        )
        self.disp_apply = Widget.Button(
            label="Apply settings",
            on_click=lambda x: [
                self.glob.apply(i.data) for i in self.disp_ctrl.plane_child
            ],
        )

        self.sett_box = Widget.Box(
            child=[
                self.disp_name,
                self.disp_modes,
                self.disp_x,
                self.disp_y,
                self.disp_scale,
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


app = IgnisApp.get_default()
app.apply_css("/home/newor/code/display_settings/style.scss")
glob = Logic()
MainWindow(glob, namespace="Monitor IGNIS")
