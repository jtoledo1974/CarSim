from math import pi, fabs, tan, sqrt, cos, sin,\
    acos, atan, radians, degrees, hypot

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.factory import Factory
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from Canvas2D import Canvas2D, Widget2D, \
    transform_vector_2D, transform_point_2D, \
    Rectangle2D, Arc2D


def cot(a):
    return cos(a) / sin(a)


def acot(x):
    return pi / 2 - atan(x)


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
        R = (self.curb_turning_circle - self.ids['lfw'].size[0] / 2) / 2
        t, w = self.track, self.wheelbase
        a = atan(2 / (2 / sqrt(w ** 2 / (R ** 2 - w ** 2)) - t / w))
        self.max_steer_angle = degrees(a)

    def check_max_steer_angle(self):
        """Helper function that verifies that the max_steer_angle is properly found"""
        self.turn(self.max_steer_angle)
        m, p = self.turning_center.this_matrix.I, self.ids['lfw'].coords
        p = transform_point_2D(m, p)
        print(2 * hypot(*p) + self.ids['lfw'].size[0])
        self.steering = 0

    def roll(self, d):
        if self.turning_center is None:
            self.move((0, d))
        elif fabs(d) > 0:
            tc = self.turning_center
            x, y = tc.coords
            R = hypot(x, y)
            a = - d / R
            r = tc.rotation

            tc.rotation = a if x > 0 else -a
            p = transform_point_2D(tc.this_matrix, (-x, -y))

            tc.rotation = r
            self.move(p)
            self.heading = self.heading - degrees(a if x > 0 else -a)

    def move(self, delta):
        delta = transform_vector_2D(self.rotation_matrix, delta)
        x, y, dx, dy = self.coords + delta
        self.coords = (x + dx, y + dy)

    def steer_towards(self, p):
        """Turn steering wheel naively towards point p in car coordinates"""

    def calc_turning_center(self):
        angle = - radians(self.steering)
        return (- self.wheelbase / tan(angle), - self.wheelbase / 2)

    def add_turning_lines(self):
        tc = Rectangle2D()
        try:
            tc.coords = self.calc_turning_center()
        except ZeroDivisionError:
            return
        tc.size = (0.1, 0.1)
        self.add_widget(tc)
        self.turning_center = tc

        bl = BackingLines()
        self.add_widget(bl)

        def set_center(tc, coords):
            "Print set_center"
            bl.center = coords
            # Backing line near
            bl.r1 = hypot(coords[0] - self.width / 2,
                          self.length - self.wheelbase - self.wheel_to_front)
            # Backing line far
            bl.r2 = hypot(coords[0] + self.width / 2,
                          self.length - self.wheelbase - self.wheel_to_front)
            # Over when backing
            bl.r3 = hypot(fabs(coords[0]) + self.width / 2,
                          self.wheelbase + self.wheel_to_front)
            # Over when forwards
            bl.r4 = fabs(coords[0]) - self.width / 2
            # Max turn when backing
            # bl.r5 = 

        tc.bind(coords=set_center)
        bl.callback = set_center

        self.backing_lines = bl

    def remove_turning_lines(self):

        try:
            self.turning_center.unbind(coords=self.backing_lines.callback)
        except AttributeError:
            return
        self.remove_widget(self.backing_lines)
        del(self.backing_lines)

        self.remove_widget(self.turning_center)
        self.turning_center = None

    def turn(self, s_input):
        """Turn steering s_input degrees"""

        s = self.steering + s_input
        if s > self.max_steer_angle:
            s = self.max_steer_angle
        elif s < -self.max_steer_angle:
            s = -self.max_steer_angle
        self.steering = s

        t, w = self.track, self.wheelbase
        try:
            o = acot(cot(radians(s)) + (t / (2 * w)))
            i = acot(cot(radians(s)) - (t / (2 * w)))
        except ZeroDivisionError:
            o = i = 0
        self.left_wheel_rotation = - o
        self.right_wheel_rotation = - i

        if fabs(self.steering) > 0.1:
            if self.turning_center is None:
                self.add_turning_lines()
            self.turning_center.coords = self.calc_turning_center()
        elif self.turning_center is not None:
            self.remove_turning_lines()

    def on_heading(self, widget, heading):
        self.heading = self.heading % 360
        self.rotation = - radians(self.heading)
        self.update()

    def on_touch_down(self, touch):
        if (self.ids['body'].collide_point(*touch.pos)):
            touch.grab(self)
            touch.car = self
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return

        vector = self.inv_transform_vector(touch.dpos)

        # print(touch.profile)

        if 'button' in touch.profile:
            b = touch.button
            tp = False  # Touchpad
        else:
            tp = True
        if tp or (b == 'left'):
            a = hypot(*self.transform_vector((vector[0], 0))) ** 2 / 30
            a = a if vector[0] > 0 else -a
            self.turn(a)
            self.roll(float(vector[1]))
        elif b == 'right':
            self.move(vector)
        elif b == 'middle':
            self.heading = self.heading + touch.dpos[0]

        return True


class CarSimApp(App):

    car = ObjectProperty()

    def on_start(self, **kwargs):
        self.root.bind(on_touch_down=self.on_touch_down)
        self.root.bind(on_touch_move=self.on_touch_move)

        Window.bind(on_keyboard=self.on_keypress)

        self.car = None

        Config.set('input', 'mouse', 'mouse,disable_multitouch')

    def on_keypress(self, window, keycode1, keycode2, text, modifiers):
        print("%s: on_keypress k1: %s, k2: %s, text: %s, mod: %s" % (
            "CarSim", keycode1, keycode2, text, modifiers))
        d, a = 1, 5
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
            self.car.turn(-a)
        elif text == "d":
            self.car.turn(a)
        elif text == "s":
            self.car.roll(-d)
        elif text == "w":
            self.car.roll(d)

        return False

    def on_touch_down(self, widget, touch):
        if 'button' in touch.profile:
            if touch.button == 'scrolldown':
                self.root.scale *= 1.1
            elif touch.button == 'scrollup':
                self.root.scale *= 1 / 1.1
            if touch.button == 'left':
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

    def on_touch_move(self, widget, touch):
        Clock.schedule_once(lambda dt: self.on_post_touch_move(touch))

    def on_post_touch_move(self, touch):
        if hasattr(touch, "car"):
            return
        x, y, dx, dy = list(self.root.coords) + list(touch.dpos)
        self.root.coords = (x + dx, y + dy)
        self.root.update()


if __name__ == '__main__':
    CarSimApp().run()
