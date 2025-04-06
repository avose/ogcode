################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds code for representing and manipulating G-Code.
'''
################################################################################################

import sys
from typing import Optional, List
import numpy as np

# Example G-Code lines.
'''
G90
G20
G17 G64 P0.001
M3 S16
F2.00
G0 Z0.2500
G0 X-126.4004 Y239.6813
G1 Z-0.0050
G1 X-126.4004 Y239.6813
G1 X-126.1612 Y239.5639
G1 X-125.9311 Y239.4294
[...]
G1 X-222.2960 Y37.9260
G0 Z0.2500
M5
M2
'''

# Supported G-Code commands.
'''
F            # Feed rate
G0 <X> <Y>   # Non-cutting rapid positioning
G1 <X> <Y>   # Linear interpolation
G17          # XY plane selection
G20          # Units in inches
G21          # Units in mm
G64 <P>      # Path blending with tolerance P
G90          # Absolute distance mode
M3 <S>       # Start laser with power S
M5           # Stop laser
M2           # End of program
'''

################################################################################################

class gcParam():
    '''Represents a single G-Code parameter.'''

    def __init__(self, name: Optional[str] = None, value: Optional[float] = None,
                 text: Optional[str] = None):
        # Initialize either from name/value or a text string.
        if ((text is None and (name is None or value is None)) or
            (text is not None and (name is not None or value is not None))):
            raise ValueError("ERROR: Constructor requires either name and value or text.")
        if name is not None and not isinstance(name, str):
            raise ValueError("ERROR: 'name' must be None or string.")
        if text is not None:
            if not isinstance(text, str):
                raise ValueError("ERROR: 'text' must be None or string.")
            try:
                name = text[0:1]
                value = float(text[1:])
            except:
                raise ValueError(f"ERROR: Could not parse G-Code parameter: '{text}'")
        try:
            self.name = str(name)
            self.value = float(value)
        except:
            raise ValueError(f"ERROR: Invalid G-Code parameter: '{name}={value}'")
        return

    def __str__(self):
        value = int(self.value) if self.value == int(self.value) else self.value
        return f"{self.name}{value}"

################################################################################################

class gcCommand():
    '''Represents a single G-Code command composed of parameters (e.g., G1 X10 Y20).'''

    def __init__(self, params: Optional[List[gcParam]] = None, text: Optional[str] = None):
        # Initialize from parameter list or raw command text.
        if (params is None and text is None) or (params is not None and text is not None):
            raise ValueError("ERROR: Constructor requires either parameters list or text.")
        if params is not None:
            if (not isinstance(params, list) or len(params) == 0 or
                not isinstance(params[0], gcParam)):
                raise ValueError("ERROR: 'params' must be None or non-empty list of gcParam.")
        if text is not None:
            if not isinstance(text, str):
                raise ValueError("ERROR: 'text' must be None or string.")
            try:
                params = [ gcParam(text=word) for word in text.split() ]
            except:
                raise ValueError(f"ERROR: Failed to create G-Code parameters from: '{text}'")
            if len(params) == 0:
                raise ValueError(f"ERROR: No G-Code parameters found in: '{text}'")
        self.params = params
        self.code = params[0]
        self.args = params[1:]
        return

    def __str__(self):
        return " ".join([str(param) for param in self.params])

################################################################################################

class gcScript():
    '''Represents a complete G-Code script composed of gcCommand objects.'''

    _coord_min = -sys.float_info.max
    _coord_max = sys.float_info.max

    ################################################################
    def __init__(self,
                 commands: Optional[List[gcCommand]] = None,
                 text: Optional[str] = None,
                 lines: Optional[np.ndarray] = None,
                 laser_power: float = 16.0,
                 size_in: float = 1024,
                 size_out: float = 220):
        # Save settings.
        self.size_in = size_in
        self.size_out = size_out
        self.laser_power = laser_power
        # Construct G-Code script from one of: command list, raw text, or line segments.
        if sum([commands is not None, text is not None, lines is not None]) != 1:
            raise ValueError("ERROR: Provide exactly one of commands, text, or lines.")
        if commands is not None:
            self._init_from_commands(commands)
        elif text is not None:
            self._init_from_text(text)
        elif lines is not None:
            self._init_from_lines(lines)
        self.bounds = self._bounds()
        return

    def _init_from_commands(self, commands: List[gcCommand]):
        # Use provided list of gcCommand objects.
        if (not isinstance(commands, list) or len(commands) == 0 or
            not isinstance(commands[0], gcCommand)):
            raise ValueError("ERROR: 'commands' must be non-empty list of gcCommand.")
        self.commands = commands
        return

    def _init_from_text(self, text: str):
        # Parse raw G-code text into commands.
        if not isinstance(text, str):
            raise ValueError("ERROR: 'text' must be a string.")
        commands = []
        for ndx, line in enumerate(text.splitlines()):
            try:
                commands.append(gcCommand(text=line))
            except:
                raise ValueError(f"ERROR: Failed to create G-Code command from line {ndx}: '{line}'")
        if len(commands) == 0:
            raise ValueError(f"ERROR: No G-Code commands found in: '{text}'")
        self.commands = commands
        return

    def _init_from_lines(self, lines: np.ndarray):
        # Convert numpy array of line segments into G-Code commands.
        if not isinstance(lines, np.ndarray) or lines.ndim != 3 or lines.shape[1:] != (2, 2):
            raise ValueError("ERROR: 'lines' must be a numpy array with shape (N, 2, 2).")

        # Use the full known image coordinate space to preserve aspect ratio.
        in_w, in_h = self.size_in
        out_w, out_h = self.size_out
        # Compute scale based on the known input size and output target.
        scale_w = out_w / in_w
        scale_h = out_h / in_h
        scale = min(scale_w, scale_h)
        scaled_w = in_w * scale
        scaled_h = in_h * scale
        # Compute offset to center drawing in the output space.
        offset_x = (out_w - scaled_w) / 2
        offset_y = (out_h - scaled_h) / 2

        # Collect G-Code commands.
        self.commands = [
            # Absolute positioning.
            gcCommand([gcParam('G', 90)]),
            # Units in mm.
            gcCommand([gcParam('G', 20)]),
            # XY plane, path blending.
            gcCommand([gcParam('G', 17), gcParam('G', 64), gcParam('P', 0.001)]),
            # Feed rate.
            gcCommand([gcParam('F', 2.00)]),
            # Start at origin off the work surface (laser off).
            gcCommand([gcParam('G', 0), gcParam('X', 0.0), gcParam('Y', 0.0)]),
            gcCommand([gcParam('G', 0), gcParam('Z', 0.25)]),
            # Laser on.
            gcCommand([gcParam('M', 3), gcParam('S', self.laser_power)]),
        ]
        last_end = None
        for line in lines:
            # Scale and center input coordinates from known image coordinate space.
            x0, y0 = line[0] * scale + [offset_x, offset_y]
            x1, y1 = line[1] * scale + [offset_x, offset_y]
            if last_end is None or np.linalg.norm(line[0] - last_end) > 1.0:
                # Lift and reposition if far from previous line.
                self.commands.append(gcCommand([gcParam('G', 0), gcParam('Z', 0.25)]))
                self.commands.append(gcCommand([gcParam('G', 0), gcParam('X', x0), gcParam('Y', y0)]))
                self.commands.append(gcCommand([gcParam('G', 1), gcParam('Z', -0.005)]))
            self.commands.append(gcCommand([gcParam('G', 1), gcParam('X', x1), gcParam('Y', y1)]))
            last_end = line[1]

        # Final lift.
        self.commands.append(gcCommand([gcParam('G', 0), gcParam('Z', 0.25)]))
        # Laser off.
        self.commands.append(gcCommand([gcParam('M', 5)]))
        # End program.
        self.commands.append(gcCommand([gcParam('M', 2)]))
        return

    ################################################################
    def __str__(self):
        # Render G-code as string.
        return "\n".join([str(command) for command in self.commands])

    ################################################################
    def to_lines(self, size: int) -> np.ndarray:
        # Convert G-code motion into drawable line segments.
        # Only movements with laser-on (Z < 0) are considered.
        # Returns a single numpy array of lines with shape (N, 2, 2),
        # scaled and centered within a square of the given size.
        lines = []
        current_pos = None
        z_value = None

        # Loop over all G-Code commands.
        for command in self.commands:
            if command.code.name != 'G':
                continue

            # Extract position parameters if available.
            x = y = z = None
            for arg in command.args:
                if arg.name == 'X':
                    x = arg.value
                elif arg.name == 'Y':
                    y = arg.value
                elif arg.name == 'Z':
                    z = arg.value
            if z is not None:
                z_value = z

            # Compute next position based on X/Y values.
            if x is not None or y is not None:
                next_pos = None
                if current_pos is not None:
                    next_pos = np.array([
                        x if x is not None else current_pos[0],
                        y if y is not None else current_pos[1]
                    ])
                elif x is not None and y is not None:
                    next_pos = np.array([x, y])
                if next_pos is not None:
                    if z_value is not None and z_value < 0:
                        lines.append(np.array([current_pos, next_pos]))
                    current_pos = next_pos

        # Finalize lines array.
        if not lines:
            return np.empty((0, 2, 2), dtype=float)
        lines = np.stack(lines)

        # Compute bounding box of the lines.
        min_coords = lines.reshape(-1, 2).min(axis=0)
        max_coords = lines.reshape(-1, 2).max(axis=0)
        span = max_coords - min_coords
        # Uniform scale so aspect ratio is preserved.
        max_span = max(span)
        scale = size / max_span if max_span > 0 else 1.0
        # Centering offset to put the drawing in the middle of the canvas.
        center_offset = (np.array([size, size]) - span * scale) / 2.0

        # Normalize and scale.
        lines = (lines - min_coords) * scale + center_offset
        # Store new bounds of the scaled lines.
        new_min = lines.reshape(-1, 2).min(axis=0)
        new_max = lines.reshape(-1, 2).max(axis=0)
        self.bounds = (tuple(new_min), tuple(new_max))
        return lines

    ################################################################
    def get_laser_power(self, default: int = 16) -> int:
        # Return the first laser power (S value) found in the G-code as an integer.
        for command in self.commands:
            if command.code.name == 'M' and command.code.value == 3:
                for arg in command.args:
                    if arg.name == 'S':
                        return int(round(arg.value))
        return default

    ################################################################
    def _bounds(self):
        # Compute bounding box of G-code motion.
        x_valid, y_valid = False, False
        x_min, x_max = self._coord_max, self._coord_min
        y_min, y_max = x_min, x_max
        for command in self.commands:
            if command.code.name == 'G' and command.code.value in [0, 1]:
                x, y = None, None
                for arg in command.args:
                    if arg.name == 'X':
                        x = arg.value
                    elif arg.name == 'Y':
                        y = arg.value
                if x is not None:
                    x_valid = True
                    x_min, x_max = min(x_min, x), max(x_max, x)
                if y is not None:
                    y_valid = True
                    y_min, y_max = min(y_min, y), max(y_max, y)
        if not x_valid:
            x_min = x_max = 0
        if not y_valid:
            y_min = y_max = 0
        return (x_min, y_min), (x_max, y_max)

################################################################################################
