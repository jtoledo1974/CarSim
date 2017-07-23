from math import pi
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty

from Canvas2D import Rectangle


class Car(Rectangle):

    color = ObjectProperty((1, 0, 0, 1))
    pos = ObjectProperty((-9, -20))
    size = ObjectProperty((18, 40))
    heading = NumericProperty(0)
    steering = NumericProperty(0.0)

    def move(self, d):
        self.coords = self.coords + np.array((d, d))
        self.heading = self.heading + d
        
    def on_heading(self, widget, heading):
        self.heading = self.heading % 360
        self.rotation = - self.heading * pi / 180
        self.update_view_points()


class CarSimApp(App):

    car = ObjectProperty()

    def timer(self, *largs):
        self.car.move(.3)

    def on_start(self, **kwargs):
        Clock.schedule_interval(self.timer, 0.02)
        self.car = Car()
        self.root.add_widget(self.car)


if __name__ == '__main__':
    CarSimApp().run()
