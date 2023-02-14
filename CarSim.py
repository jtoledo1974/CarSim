from math import pi, fabs, tan, sqrt, cos, sin, atan, radians, degrees, hypot

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from Canvas2D import (
    Widget2D,
    transform_vector_2d,
    transform_point_2d,
    Rectangle2D,
)


def cot(angle):
    return cos(angle) / sin(angle)


def acot(cot_):
    return pi / 2 - atan(cot_)


class BackingLines(Widget2D):
    pass


class Car(Widget2D):

    heading = NumericProperty(0.0)
    steering = NumericProperty(0.0)
    turning_center = ObjectProperty(None, allownone=True)
    max_steer_angle = NumericProperty(0.0)
    left_wheel_rotation = NumericProperty(0.0)
    right_wheel_rotation = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(Car, self).__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.calc_max_steer_angle())

    def calc_max_steer_angle(self):
        # http://ckw.phys.ncku.edu.tw/public/pub/Notes/GeneralPhysics/Powerpoint/Extra/05/11_0_0_Steering_Theroy.pdf
        radius = (self.curb_turning_circle - self.ids["lfw"].size[0] / 2) / 2
        trk, wbs = self.track, self.wheelbase
        ang = atan(2 / (2 / sqrt(wbs**2 / (radius**2 - wbs**2)) - trk / wbs))
        self.max_steer_angle = degrees(ang)

    def check_max_steer_angle(self):
        """Helper function that verifies that the max_steer_angle is properly found"""
        self.turn(self.max_steer_angle)
        matrix, pnt = self.turning_center.this_matrix.I, self.ids["lfw"].coords
        pnt = transform_point_2d(matrix, pnt)
        print(2 * hypot(*pnt) + self.ids["lfw"].size[0])
        self.steering = 0

    def roll(self, dist):
        if self.turning_center is None:
            self.move((0, dist))
        elif fabs(dist) > 0:
            tc = self.turning_center
            x, y = tc.coords
            radius = hypot(x, y)
            angle = -dist / radius
            rot = tc.rotation

            tc.rotation = angle if x > 0 else -angle
            pnt = transform_point_2d(tc.this_matrix, (-x, -y))

            tc.rotation = rot
            self.move(pnt)
            self.heading = self.heading - degrees(angle if x > 0 else -angle)

    def move(self, delta):
        delta = transform_vector_2d(self.rotation_matrix, delta)
        x, y, dx, dy = self.coords + delta
        self.coords = (x + dx, y + dy)

    def steer_towards(self, _p):
        """Turn steering wheel naively towards point p in car coordinates"""

    def calc_turning_center(self):
        angle = -radians(self.steering)
        return (-self.wheelbase / tan(angle), -self.wheelbase / 2)

    def add_turning_lines(self):
        # pylint: disable=attribute-defined-outside-init
        tc = Rectangle2D()
        try:
            tc.coords = self.calc_turning_center()
        except ZeroDivisionError:
            return
        tc.size = (0.1, 0.1)
        self.add_widget(tc)
        self.turning_center = tc

        blines = BackingLines()
        self.add_widget(blines)

        def set_center(_tc, coords):
            "Print set_center"
            blines.center = coords
            # Backing line near
            blines.r1 = hypot(
                coords[0] - self.width / 2,
                self.length - self.wheelbase - self.wheel_to_front,
            )
            # Backing line far
            blines.r2 = hypot(
                coords[0] + self.width / 2,
                self.length - self.wheelbase - self.wheel_to_front,
            )
            # Over when backing
            blines.r3 = hypot(
                fabs(coords[0]) + self.width / 2, self.wheelbase + self.wheel_to_front
            )
            # Over when forwards
            blines.r4 = fabs(coords[0]) - self.width / 2
            # Max turn when backing
            # bl.r5 =

        tc.bind(coords=set_center)
        blines.callback = set_center

        self.backing_lines = blines

    def remove_turning_lines(self):

        try:
            self.turning_center.unbind(coords=self.backing_lines.callback)
        except AttributeError:
            return
        self.remove_widget(self.backing_lines)
        del self.backing_lines

        self.remove_widget(self.turning_center)
        self.turning_center = None

    def turn(self, s_input):
        """Turn steering s_input degrees"""

        str_angl = self.steering + s_input
        if str_angl > self.max_steer_angle:
            str_angl = self.max_steer_angle
        elif str_angl < -self.max_steer_angle:
            str_angl = -self.max_steer_angle
        self.steering = str_angl

        trk, wlbs = self.track, self.wheelbase
        try:
            outer = acot(cot(radians(str_angl)) + (trk / (2 * wlbs)))
            inner = acot(cot(radians(str_angl)) - (trk / (2 * wlbs)))
        except ZeroDivisionError:
            outer = inner = 0
        self.left_wheel_rotation = -outer
        self.right_wheel_rotation = -inner

        if fabs(self.steering) > 0.1:
            if self.turning_center is None:
                self.add_turning_lines()
            self.turning_center.coords = self.calc_turning_center()
        elif self.turning_center is not None:
            self.remove_turning_lines()

    def on_heading(self, _widget, _heading):
        self.heading = self.heading % 360
        self.rotation = -radians(self.heading)
        self.update()

    def on_touch_down(self, touch):
        if self.ids["body"].collide_point(*touch.pos):
            touch.grab(self)
            touch.car = self
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return

        vector = self.inv_transform_vector(touch.dpos)

        # print(touch.profile)

        if "button" in touch.profile:
            btn = touch.button
            tchpd = False  # Touchpad
        else:
            tchpd = True
        if tchpd or (btn == "left"):
            angle = hypot(*self.transform_vector((vector[0], 0))) ** 2 / 30
            angle = angle if vector[0] > 0 else -angle
            self.turn(angle)
            self.roll(float(vector[1]))
        elif btn == "right":
            self.move(vector)
        elif btn == "middle":
            self.heading = self.heading + touch.dpos[0]

        return True


class CarSimApp(App):

    car = ObjectProperty()

    def on_start(self, **_kwargs):
        self.root.bind(on_touch_down=self.on_touch_down)
        self.root.bind(on_touch_move=self.on_touch_move)

        Window.bind(on_keyboard=self.on_keypress)

        self.car = None

        Config.set("input", "mouse", "mouse,disable_multitouch")

    def on_keypress(self, _window, keycode1, keycode2, text, modifiers):
        print(
            f"Carsim: on_keypress k1: {keycode1}, k2: {keycode2}, text: {text}, mod: {modifiers}"
        )
        dist, angle = 1, 5
        x, y, pan = *self.root.coords, self.root.width / 10
        if keycode1 == 273:  # UP
            self.root.coords = (x, y - pan)
        elif keycode1 == 274:  # DOWN
            self.root.coords = (x, y + pan)
        elif keycode1 == 275:  # RIGHT
            self.root.coords = (x - pan, y)
        elif keycode1 == 276:  # LEFT
            self.root.coords = (x + pan, y)
        elif text == "+":
            self.root.scale = self.root.scale * 1.1
        elif text == "-":
            self.root.scale = self.root.scale / 1.1

        if not self.car:
            return False

        if text == "a":
            self.car.turn(-angle)
        elif text == "d":
            self.car.turn(angle)
        elif text == "s":
            self.car.roll(-dist)
        elif text == "w":
            self.car.roll(dist)

        return False

    def on_touch_down(self, _widget, touch):
        if "button" in touch.profile:
            if touch.button == "scrolldown":
                self.root.scale *= 1.1
            elif touch.button == "scrollup":
                self.root.scale *= 1 / 1.1
            if touch.button == "left":
                touch.grab(self.root)

        Clock.schedule_once(lambda dt: self.on_post_touch_down(touch))

    def on_post_touch_down(self, touch):
        if hasattr(touch, "car"):
            try:
                self.car.remove_turning_lines()
            except AttributeError:
                pass
            self.car = touch.car
            self.car.add_turning_lines()

    def on_touch_move(self, _widget, touch):
        Clock.schedule_once(lambda dt: self.on_post_touch_move(touch))

    def on_post_touch_move(self, touch):
        if hasattr(touch, "car"):
            return
        x, y, dx, dy = list(self.root.coords) + list(touch.dpos)
        self.root.coords = (x + dx, y + dy)
        self.root.update()


if __name__ == "__main__":
    CarSimApp().run()
