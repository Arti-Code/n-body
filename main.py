"""
Compute shader with buffers
"""
import random
import math
from array import array

import arcade
from arcade.gl import BufferDescription

# Size of performance graphs and distance between them
GRAPH_WIDTH = 200
GRAPH_HEIGHT = 120
GRAPH_MARGIN = 5

arcade.enable_timings()


class MyWindow(arcade.Window):

    def __init__(self):
        # Call parent constructor
        super().__init__(2300, 1300, "Compute Shader", gl_version=(4, 3), resizable=True)
        self.center_window()

        # --- Class instance variables
        # How long we have been running, in seconds
        self.run_time = 0
        # Number of balls to move
        self.num_balls = 40000

        # This has something to do with how we break the calculations up
        # and parallelize them.
        self.group_x = 256
        self.group_y = 1

        # --- Create buffers

        # Format of the buffer data.
        # 4f = position and size -> x, y, z, radius
        # 4x4 = Four floats used for calculating velocity. Not needed for visualization.
        # 4f = color -> rgba
        buffer_format = "4f 4x4 4f"
        # Generate the initial data that we will put in buffer 1.
        initial_data = self.gen_initial_data()

        # Create data buffers for the compute shader
        # We ping-pong render between these two buffers
        # ssbo = shader storage buffer object
        self.ssbo_1 = self.ctx.buffer(data=array('f', initial_data))
        self.ssbo_2 = self.ctx.buffer(reserve=self.ssbo_1.size)

        # Attribute variable names for the vertex shader
        attributes = ["in_vertex", "in_color"]
        self.vao_1 = self.ctx.geometry(
            [BufferDescription(self.ssbo_1, buffer_format, attributes)],
            mode=self.ctx.POINTS,
        )
        self.vao_2 = self.ctx.geometry(
            [BufferDescription(self.ssbo_2, buffer_format, attributes)],
            mode=self.ctx.POINTS,
        )

        # --- Create shaders

        # Load in the shader source code
        file = open("shaders/compute_shader2.glsl")
        compute_shader_source = file.read()
        file = open("shaders/vertex_shader.glsl")
        vertex_shader_source = file.read()
        file = open("shaders/fragment_shader.glsl")
        fragment_shader_source = file.read()
        file = open("shaders/geometry_shader.glsl")
        geometry_shader_source = file.read()

        # Create our compute shader
        compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_X", str(self.group_x))
        compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_Y", str(self.group_y))
        self.compute_shader = self.ctx.compute_shader(source=compute_shader_source)

        # Program for visualizing the balls
        self.program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            geometry_shader=geometry_shader_source,
            fragment_shader=fragment_shader_source,
        )

        # Create a sprite list to put the performance graph into
        self.perf_graph_list = arcade.SpriteList()

        # Create the FPS performance graph
        graph = arcade.PerfGraph(GRAPH_WIDTH, GRAPH_HEIGHT, graph_data="FPS")
        graph.center_x = GRAPH_WIDTH / 2
        graph.center_y = self.height - GRAPH_HEIGHT / 2
        self.perf_graph_list.append(graph)

    def on_draw(self):
        self.clear()
        self.ctx.enable(self.ctx.BLEND)

        # Change the force
        force = math.sin(self.run_time / 10) / 2, math.cos(self.run_time / 10) / 2
        force = 0.0, 0.0

        # Bind buffers
        self.ssbo_1.bind_to_storage_buffer(binding=0)
        self.ssbo_2.bind_to_storage_buffer(binding=1)

        # Set input variables for compute shader
        # self.compute_shader["screen_size"] = self.get_size()
        # self.compute_shader["force"] = force
        # self.compute_shader["frame_time"] = self.run_time

        # Run compute shader
        self.compute_shader.run(group_x=self.group_x, group_y=self.group_y)

        # Draw the balls
        self.vao_2.render(self.program)

        # Swap the buffers around (we are ping-ping rendering between two buffers)
        self.ssbo_1, self.ssbo_2 = self.ssbo_2, self.ssbo_1
        # Swap what geometry we draw
        self.vao_1, self.vao_2 = self.vao_2, self.vao_1

        # Draw the graphs
        self.perf_graph_list.draw()

        # Get FPS for the last 60 frames
        text = f"FPS: {arcade.get_fps(60):5.1f}"
        arcade.draw_text(text, 10, 10, arcade.color.BLACK, 22)

    def on_update(self, delta_time: float):
        self.run_time = delta_time

    def gen_initial_data(self):
        for i in range(self.num_balls):
            # Position/radius
            yield random.randrange(0, self.width)
            yield random.randrange(0, self.height)
            yield 0.0  # z (padding)
            yield 6.0

            # Velocity
            v = 0.001
            angle = (i / self.num_balls) * math.pi * 2.0
            yield math.cos(angle) * v  # vx
            yield math.sin(angle) * v  # vy
            # yield 0.0  # vz (padding)
            # yield 0.0  # vw (padding)
            yield 0.0  # vz (padding)
            yield 0.0  # vw (padding)

            # Color
            # yield 1.0 * random.random()  # r
            # yield 1.0 * random.random()  # g
            # yield 1.0 * random.random()  # b
            # colors = "#68632e", "#FFFFFF", "#c9d1fc", "#c9d1fc"
            # hex_color = random.choice(colors)
            hex_color = "#FFFFFF"
            color_b = arcade.color_from_hex_string(hex_color)
            color_f = arcade.get_four_float_color(color_b)
            yield color_f[0]
            yield color_f[1]
            yield color_f[2]

            # yield 1.0  # a
            # yield 1.0  # a
            # yield 1.0  # a
            yield 1.0  # a


app = MyWindow()
arcade.run()
