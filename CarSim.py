from math import pi, fabs, tan

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from Canvas2D import Widget2D, transform_vector_2D, Rectangle2D


class Car(Widget2D):

    heading = NumericProperty(0)
    steering = NumericProperty(0)
    turning_center = ObjectProperty(None, allownone=True)

    def move(self, delta):
        delta = transform_vector_2D(self.rotation_matrix, delta)
        x, y, dx, dy = self.coords + delta
        self.coords = (x + dx, y + dy)

    def calc_turning_center(self):
        angle = - self.steering * pi / 180
        return (- self.wheelbase / 2 / tan(angle), - self.wheelbase / 2)

    def turn(self, s_input):
        self.steering = self.steering + s_input
        if fabs(self.steering) > 1:
            if self.turning_center is None:
                tc = Rectangle2D()
                tc.coords = self.calc_turning_center()
                tc.size = (0.1, 0.1)
                self.add_widget(tc)
                self.turning_center = tc
            self.turning_center.coords = self.calc_turning_center()
        elif self.turning_center is not None:
            self.remove_widget(self.turning_center)
            self.turning_center = None

    def on_heading(self, widget, heading):
        self.heading = self.heading % 360
        self.rotation = - self.heading * pi / 180
        self.update()

    def on_touch_down(self, touch):
        # will receive all motion events.
        if (self.ids['body'].collide_point(*touch.pos)):
            touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return True

        vector = self.inv_transform_vector(touch.dpos)

        if 'button' in touch.profile:
            b = touch.button
            if b == 'left':
                self.turn(float(vector[0]))
                self.move((0, vector[1]))
            elif b == 'right':
                self.move(vector)
            elif b == 'middle':
                self.heading = self.heading + touch.dpos[0]


class CarSimApp(App):

    car = ObjectProperty()

    def timer(self, *largs):
        pass

    def on_start(self, **kwargs):
        Clock.schedule_interval(self.timer, 1)
        self.car = Car()
        self.root.add_widget(self.car)
        self.car.heading = 270

        Window.bind(on_keyboard=self.on_keypress)

        Config.set('input', 'mouse', 'mouse,disable_multitouch')

    def on_keypress(self, window, keycode1, keycode2, text, modifiers):
        print("%s: on_keypress k1: %s, k2: %s, text: %s, mod: %s" % (
            "CarSim", keycode1, keycode2, text, modifiers))
        return False


if __name__ == '__main__':
    CarSimApp().run()
