from math import sin, cos

import numpy as np

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.lang.builder import Builder

# Using this for refence on transformations
# https://www.gamedev.net/articles/programming/math-and-physics/making-a-game-engine-transformations-r3566/


IDENT_3 = np.matrix(np.identity(3))

Builder.load_string(
    """
<Line2D>:
    canvas:
        Color:
            rgba: self.color
        Line:
            points: self.view_points

<Arc2D>:
    canvas:
        Color:
            rgba: self.color
        Line:
            circle: self.view_circle


<Rectangle2D>:
    source: None
    canvas:
        Quad:
            points: self.view_points
            source: self.source

"""
)


def point_inside_polygon(x, y, poly):
    n_points = len(poly)
    inside = False

    p1x, p1y = poly[0]
    for i in range(n_points + 1):
        p2x, p2y = poly[i % n_points]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def transform_point_2d(matrix, pnt):
    pnt = pnt + (1,)
    vector = matrix * np.transpose(np.matrix(pnt))
    return (vector[0, 0], vector[1, 0])


def transform_vector_2d(matrix, vector):
    vector = vector + (0,)
    vector = matrix * np.transpose(np.matrix(vector))
    return (vector[0, 0], vector[1, 0])


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
        self.translation_matrix = tltn = np.matrix(
            (
                (1, 0, self.coords[0]),
                (0, 1, self.coords[1]),
                (0, 0, 1),
            )
        )
        self.scale_matrix = scl = np.matrix(
            (
                (self.scale_x, 0, 0),
                (0, self.scale_y, 0),
                (0, 0, 1),
            )
        )
        self.rotation_matrix = rot = np.matrix(
            (
                (cos(self.rotation), -sin(self.rotation), 0),
                (sin(self.rotation), cos(self.rotation), 0),
                (0, 0, 1),
            )
        )
        self.this_matrix = tltn * scl * rot
        self.matrix = self.get_parent_matrix() * self.this_matrix
        self.inv_matrix = self.matrix.I
        for widget in self.children:
            try:
                widget.update()
            except AttributeError:  # Other standard widgets
                pass

    def update(self):
        self.update_matrix()

    def transform_point(self, pnt):
        pnt = pnt + (1,)
        vector = self.matrix * np.transpose(np.matrix(pnt))
        return (vector[0, 0], vector[1, 0])

    def transform_vector(self, vector):
        vector = vector + (0,)
        vector = self.matrix * np.transpose(np.matrix(vector))
        return (vector[0, 0], vector[1, 0])

    def inv_transform_point(self, vector):
        vector = vector + (1,)
        pnt = self.inv_matrix * np.transpose(np.matrix(vector))
        return (pnt[0, 0], pnt[1, 0])

    def inv_transform_vector(self, vector):
        vector = vector + (0,)
        vector = self.inv_matrix * np.transpose(np.matrix(vector))
        return (vector[0, 0], vector[1, 0])

    def on_coords(self, _widget, _coords):
        self.update_matrix()

    def on_rotation(self, _widget, _rotation):
        self.update_matrix()

    def on_scale_x(self, _widget, _scale_x):
        self.update_matrix()

    def on_scale_y(self, _widget, _scale_y):
        self.update_matrix()

    def on_scale(self, _widget, scale):
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
        for pnt in points:
            res += self.transform_point(pnt)
        self.view_points = tuple(res)

    def on_points(self, _widget, _points):
        self.update_view_points()

    def on_coords(self, widget, coords):
        super(Points2D, self).on_coords(widget, coords)
        self.update_view_points()

    def on_rotation(self, widget, rotation):
        super(Points2D, self).on_rotation(widget, rotation)
        self.update_view_points()


class Line2D(Points2D):

    color = ObjectProperty((1, 1, 1, 1))  # RGBA

    def on_color(self, _widget, _color):
        self.update_view_points()


class Arc2D(Line2D):

    circle = ObjectProperty((0, 0, 0))
    view_circle = ObjectProperty((0, 0, 0))

    def update_circle(self):
        self.update_matrix()

        circle = list(self.transform_point(self.circle[:2]))
        radius = np.linalg.norm(self.transform_vector((self.circle[2], 0)))
        self.view_circle = tuple(circle + [radius] + list(self.circle[3:]))

    def on_circle(self, _widget, _circle):
        self.update_circle()

    def update(self):
        self.update_circle()


class Rectangle2D(Line2D):

    pos = ObjectProperty((0, 0))
    size = ObjectProperty((0, 0))
    centered = BooleanProperty(True)
    view_points = ObjectProperty((0, 0, 0, 0, 0, 0, 0, 0))

    def __init__(self, **kwargs):
        self.update_points()
        super(Rectangle2D, self).__init__(**kwargs)

    def update_points(self):
        p_x, p_y, s_x, s_y = self.pos + self.size
        self.points = (
            self.pos + (p_x + s_x, p_y) + (p_x + s_x, p_y + s_y) + (p_x, p_y + s_y)
        )
        self.update_view_points()

    def on_pos(self, _widget, _pos):
        self.update_points()

    def on_size(self, _widget, _size):
        if self.centered:
            self.pos = (-self.size[0] / 2, -self.size[1] / 2)
        self.update_points()

    def on_centered(self, _widget, _centered):
        self.update_points()

    def collide_point(self, x, y):
        # For other optimized strategies see
        # https://stackoverflow.com/questions/16750618/whats-an-efficient-way-to-find-if-a-point-lies-in-the-convex-hull-of-a-point-cl
        poly = tuple(zip(self.view_points[0::2], self.view_points[1::2]))
        return point_inside_polygon(x, y, poly)
