from math import sin, cos
import numpy as np

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty

# Using this for refence on transformations
# https://www.gamedev.net/articles/programming/math-and-physics/making-a-game-engine-transformations-r3566/

IDENT_3 = np.matrix(np.identity(3))


class Widget2D(Widget):

    # Properties don't work well with Numpy arrays
    coords = ObjectProperty((0, 0), force_dispatch=True)
    rotation = NumericProperty(0.0)
    scale_x = NumericProperty(1)
    scale_y = NumericProperty(1)
    scale = NumericProperty(1)

    def __init__(self, **kwargs):
        super(Widget2D, self).__init__(**kwargs)
        self.update_matrix()

    def get_parent_matrix(self):
        try:
            return self.parent.matrix
        except AttributeError:
            return IDENT_3

    def update_matrix(self):
        translation = np.matrix(
            ((1, 0, self.coords[0]),
             (0, 1, self.coords[1]),
             (0, 0, 1)))
        scale = np.matrix(
            ((self.scale_x, 0, 0),
             (0, self.scale_y, 0),
             (0, 0, 1)))
        rotation = np.matrix(
            ((cos(self.rotation), -sin(self.rotation), 0),
             (sin(self.rotation), cos(self.rotation), 0),
             (0, 0, 1)))
        self.matrix = self.get_parent_matrix() * translation * scale * rotation

    def on_coords(self, widget, coords):
        self.update_matrix()

    def on_rotation(self, widget, rotation):
        self.update_matrix()

    def on_scale_x(self, widget, scale_x):
        self.update_matrix()

    def on_scale_y(self, widget, scale_y):
        self.update_matrix()

    def on_scale(self, widget, scale):
        self.scale_x = self.scale_y = scale
        self.update_matrix()


class Canvas2D(Widget2D):
    """Root Canvas on wich other Canvas2D elements are placed
    It supports viewport and element transformations"""

    def get_parent_matrix(self):
        return IDENT_3


class Polygon(Widget2D):

    points = ObjectProperty(())
    view_points = ObjectProperty((0, 0))

    def __init__(self, **kwargs):
        super(Polygon, self).__init__(**kwargs)
        self.update_view_points()

    def update_view_points(self):
        self.update_matrix()
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

    def on_coords(self, widget, coords):
        super(Polygon, self).on_coords(widget, coords)
        self.update_view_points()

    def on_rotation(self, widget, rotation):
        super(Polygon, self).on_rotation(widget, rotation)
        self.update_view_points()
