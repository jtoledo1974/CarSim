from math import pi

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from Canvas2D import Widget2D, transform_vector_2D


class Car(Widget2D):

    heading = NumericProperty(0)
    steering = NumericProperty(0.0)

    def move(self, delta):
        delta = (0, delta[1])
        delta = transform_vector_2D(self.rotation_matrix, delta)
        x, y, dx, dy = self.coords + delta
        self.coords = (x + dx, y + dy)

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
        self.move(vector)


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

    def on_keypress(self, window, keycode1, keycode2, text, modifiers):
        print("%s: on_keypress k1: %s, k2: %s, text: %s, mod: %s" % (
            "CarSim", keycode1, keycode2, text, modifiers))
        return False


if __name__ == '__main__':
    CarSimApp().run()
