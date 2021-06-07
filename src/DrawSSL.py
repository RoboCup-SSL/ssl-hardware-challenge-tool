import turtle

turtle.delay(0)
turtle.tracer(False)

FIELD_LINE_PEN_SZ = 10
DEFAULT_PEN_SZ = 2


class DrawSSL(object):

    def __init__(self):
        self.draw = turtle.Turtle()
        self.window = turtle.Screen()
        self.window.bgcolor('green')
        self.window.title('SSL Hardware Challenge Check Tool')

        self.field_size = (800, 600)
        self.center_circle_radius = 100
        self.draw.pen(pensize=DEFAULT_PEN_SZ)
        self.draw.speed('fastest')
        self.draw.hideturtle()
        self.current_callback = None

# =============================================================================

    def __del__(self):
        self.window.exitonclick()

# =============================================================================

    def set_key_callback(self, callback_fn=None):
        self.window.onkey(callback_fn, 'q')
        self.current_callback = callback_fn
        self.window.listen()

# =============================================================================

    def start_draw(self):
        self.window.tracer(False)
        self.draw.penup()

# =============================================================================

    def finish_draw(self):
        #          self.window.tracer(True)
        self.window.update()
        self.draw.hideturtle()
        self.draw.pen(pensize=DEFAULT_PEN_SZ, pencolor='black')
        self.draw.penup()

# =============================================================================

    def set_field_size(self, new_size: (int, int)):
        self.field_size = new_size
        self.window.setworldcoordinates(-new_size[0]/2, -new_size[1]/2,
                                        new_size[0]/2, new_size[1]/2)

# =============================================================================

    def set_center_circle_radius(self, radius: int):
        self.center_circle_radius = radius

# =============================================================================

    def clear(self):
        self.window.clear()

        if self.current_callback != None:
            self.window.onkey(self.current_callback, 'q')

# =============================================================================

    def draw_field(self):
        sz = self.field_size
        self.start_draw()
        self.window.bgcolor('green')
        self.draw.pen(pensize=FIELD_LINE_PEN_SZ, pencolor='black')

        self.draw.goto(-sz[0]/2, sz[1]/2)

        self.draw.pendown()
        self.draw.goto(-sz[0]/2, -sz[1]/2)
        self.draw.goto(sz[0]/2, -sz[1]/2)
        self.draw.goto(sz[0]/2, sz[1]/2)
        self.draw.goto(-sz[0]/2, sz[1]/2)

        self.draw.goto(0, sz[1]/2)
        self.draw.goto(0, -sz[1]/2)
        self.draw.goto(0, -self.center_circle_radius)
        self.draw.circle(self.center_circle_radius)

        self.draw.pen(pensize=DEFAULT_PEN_SZ)
        self.finish_draw()

# =============================================================================

    def draw_robot(self, pos: (int, int), team: str):
        self.draw.pen(pencolor=team)

        if len(pos) == 2:
            self.start_draw()

            self.draw.goto(*pos)
            self.draw.pendown()
            self.draw.dot(18)

            self.finish_draw()

# =============================================================================

    def draw_ball(self, pos: (int, int)):
        self.draw.pen(pencolor='orange')

        if len(pos) == 2:
            self.start_draw()

            self.draw.goto(*pos)
            self.draw.pendown()
            self.draw.dot(10)

            self.finish_draw()

# =============================================================================
