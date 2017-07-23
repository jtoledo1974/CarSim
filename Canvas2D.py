from math import sin, cos
import numpy as np

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty
from kivy.lang.builder import Builder

# Using this for refence on transformations
# https://www.gamedev.net/articles/programming/math-and-physics/making-a-game-engine-transformations-r3566/

IDENT_3 = np.matrix(np.identity(3))

Builder.load_string("""
<Line2D>:
    canvas:
        Color:
            rgba: self.color
        Line:
            points: self.view_points


<Rectangle2D>:
    canvas:
        Quad:
            points: self.view_points

""")


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
        for w in self.children:
            w.update()

    def update(self):
        self.update_matrix()

    def transform_point(self, p):
        p = p + (1, )
        v = self.matrix * np.transpose(np.matrix(p))
        return (v[0, 0], v[1, 0])

    def transform_vector(self, v):
        v = v + (0, )
        v = self.matrix * np.transpose(np.matrix(v))
        return (v[0, 0], v[1, 0])

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


class Points2D(Widget2D):

    points = ObjectProperty(())
    view_points = ObjectProperty((0, 0))

    def __init__(self, **kwargs):
        super(Points2D, self).__init__(**kwargs)
        self.update_view_points()

    def update(self):
        self.update_view_points()

    def update_view_points(self):
        self.update_matrix()
        points = zip(self.points[0::2], self.points[1::2])
        res = []
        for p in points:
            res += self.transform_point(p)
        self.view_points = tuple(res)

    def on_points(self, widget, points):
        self.update_view_points()

    def on_coords(self, widget, coords):
        super(Points2D, self).on_coords(widget, coords)
        self.update_view_points()

    def on_rotation(self, widget, rotation):
        super(Points2D, self).on_rotation(widget, rotation)
        self.update_view_points()


class Line2D(Points2D):

    color = ObjectProperty((1, 1, 1, 1))  # RGBA

    def on_color(self, widget, color):
        self.update_view_points()


class Rectangle2D(Line2D):

    pos = ObjectProperty((0, 0))
    size = ObjectProperty((0, 0))
    view_points = ObjectProperty((0, 0, 0, 0, 0, 0, 0, 0))

    def __init__(self, **kwargs):
        self.update_points()
        super(Rectangle2D, self).__init__(**kwargs)

    def update_points(self):
        p_x, p_y, s_x, s_y = self.pos + self.size
        self.points = self.pos + (p_x + s_x, p_y) \
            + (p_x + s_x, p_y + s_y) + (p_x, p_y + s_y)
        print(self.points)
        self.update_view_points()

    def on_pos(self, widget, pos):
        self.update_points()

    def on_size(self, widget, size):
        self.update_points()
