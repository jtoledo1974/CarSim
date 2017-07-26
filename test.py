from math import pi, fabs, tan, sqrt, cos, sin,\
    acos, atan, radians, degrees, hypot

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.factory import Factory
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from kivy.lang.builder import Builder

root = Builder.load_string("""
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

<R@Widget>:
    canvas:
        Line:
            rectangle: (0, 0, 50, 50)


<Car@RelativeLayout>:
    canvas:
        Rotate:
            angle: 25
    R:
    Label:
        text: str(self.pos) + " " + str(self.size)


FloatLayout:
    Label:
        canvas:
            PushMatrix:
            Translate:
                x: 100
            PopMatrix:
        text: "hola"
    Car:
""")


class TestApp(App):
    def build(self, **kwargs):
        return root


if __name__ == '__main__':
    TestApp().run()
