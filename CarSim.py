from math import pi, sin, cos
import numpy as np

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.properties import NumericProperty, ObjectProperty

view_matrix = ObjectProperty(np.identity(3))


# Using this for refence on transformations
# https://www.gamedev.net/articles/programming/math-and-physics/making-a-game-engine-transformations-r3566/


class Car(Widget):

    # Properties don't work well with Numpy arrays
    coords = ObjectProperty((50, 50), force_dispatch=True)
    heading = NumericProperty(0)
    rotation = NumericProperty(0.0)

    points = ObjectProperty((-9, -20, 9, -20, 9, 20, 9, -20))
    view_points = ObjectProperty((0, 0))

    steering = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super(Car, self).__init__(**kwargs)
        self.matrix = np.identity(3)
        self.update_view_points()

    def update_view_points(self):
        self.matrix = np.matrix(
            ((1, 0, self.coords[0]),
             (0, 1, self.coords[1]), (0, 0, 1))) * np.array(
            ((cos(self.rotation), -sin(self.rotation), 0),
             (sin(self.rotation), cos(self.rotation), 0),
             (0, 0, 1)))
        self.view_points = self.transform(self.points)

    def transform(self, points):
        # De manera general es mejor utilizar un yield, supongo
        points = zip(points[0::2], points[1::2], [1] * int((len(points) / 2)))
        res = []
        for p in points:
            p = self.matrix * np.transpose(np.matrix(p))
            x, y = p[0, 0], p[1, 0]
            res += (x, y)
        return res

    def move(self, d):
        self.coords = self.coords + np.array((d, d))
        self.heading = self.heading + d
        pass

    def on_coords(self, widget, coords):
        self.update_view_points()

    def on_heading(self, widget, heading):
        self.heading = self.heading % 360
        self.rotation = - self.heading * pi / 180
        self.update_view_points()


class CarSimApp(App):

    car = ObjectProperty()

    def timer(self, *largs):
        self.car.move(10)

    def on_start(self, **kwargs):
        Clock.schedule_interval(self.timer, 0.3)
        self.car = Car()
        self.root.add_widget(self.car)


if __name__ == '__main__':
    CarSimApp().run()
