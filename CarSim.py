from math import pi, fabs, tan, sqrt, acos, radians, degrees, hypot

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.properties import NumericProperty, ObjectProperty
from kivy.core.window import Window

from Canvas2D import Canvas2D, Widget2D, \
    transform_vector_2D, transform_point_2D, \
    Rectangle2D, Arc2D


class TurnCircle(Arc2D):
    circle: ObjectProperty((0, 0, 0))


class Car(Widget2D):

    heading = NumericProperty(0)
    steering = NumericProperty(0)
    turning_center = ObjectProperty(None, allownone=True)

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

    def calc_turning_center(self):
        angle = - radians(self.steering)
        return (- self.wheelbase / 2 / tan(angle), - self.wheelbase / 2)

    def turn(self, s_input):
        self.steering = self.steering + s_input
        if fabs(self.steering) > 0.1:
            if self.turning_center is None:

                tc = Rectangle2D()
                coords = tc.coords = self.calc_turning_center()
                tc.size = (0.1, 0.1)
                self.add_widget(tc)
                self.turning_center = tc

                w = TurnCircle()
                w.coords = coords
                w.circle = (0, 0, coords[0])
                self.add_widget(w)
                self.turn_circle = w

            coords = self.calc_turning_center()
            self.turning_center.coords = coords
            self.turn_circle.coords = coords
            self.turn_circle.circle = (0, 0, coords[0])

        elif self.turning_center is not None:
            self.remove_widget(self.turn_circle)
            del(self.turn_circle)
            self.remove_widget(self.turning_center)
            self.turning_center = None

    def on_heading(self, widget, heading):
        self.heading = self.heading % 360
        self.rotation = - radians(self.heading)
        self.update()

    def on_touch_down(self, touch):
        print("Car touch")
        print(type(self))
        if (self.ids['body'].collide_point(*touch.pos)):
            touch.grab(self)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return

        vector = self.inv_transform_vector(touch.dpos)
        print(touch.profile)

        if 'button' in touch.profile:
            b = touch.button
        else:
            tp = True  # Touchpad
        if tp or (b == 'left'):
            self.turn(float(vector[0]))
            self.roll(float(vector[1]))
        elif b == 'right':
            self.move(vector)
        elif b == 'middle':
            self.heading = self.heading + touch.dpos[0]

        return True


class CarSimApp(App):

    car = ObjectProperty()

    def timer(self, *largs):
        pass

    def on_start(self, **kwargs):
        Clock.schedule_interval(self.timer, 1)
        self.car = Car()
        self.root.add_widget(self.car)
        self.car.heading = 270

        # self.root.bind(on_touch_down=self.on_touch_down)
        # self.root.bind(on_touch_move=self.on_touch_move)

        Window.bind(on_keyboard=self.on_keypress)

        Config.set('input', 'mouse', 'mouse,disable_multitouch')

    def on_keypress(self, window, keycode1, keycode2, text, modifiers):
        print("%s: on_keypress k1: %s, k2: %s, text: %s, mod: %s" % (
            "CarSim", keycode1, keycode2, text, modifiers))
        d, a = 1, 5
        if keycode1 == 273:  # UP
            self.car.roll(d)
        elif keycode1 == 274:  # DOWN
            self.car.roll(-d)
        elif keycode1 == 275:  # RIGHT
            self.car.turn(5)
        elif keycode1 == 276:  # LEFT
            self.car.turn(-5)

        return False

    def on_touch_down(self, widget, touch):
        super(Canvas2D, self.root).on_touch_down(touch)
        print("Canvas touch")
        if 'button' in touch.profile:
            if touch.button == 'scrolldown':
                self.root.scale *= 1.1
            elif touch.button == 'scrollup':
                self.root.scale *= 1 / 1.1
            if touch.button == 'left':
                touch.grab(self.root)
                return True

    def on_touch_move(self, widget, touch):
        super(Canvas2D, self.root).on_touch_move(touch)
        if touch.grab_current is not self.root:
            return
        print(widget.coords)
        x, y, dx, dy = list(self.root.coords) + list(touch.coords)
        self.root.coords = (x + dx, y + dy)
        print(widget.coords)
        self.root.update()


if __name__ == '__main__':
    CarSimApp().run()
