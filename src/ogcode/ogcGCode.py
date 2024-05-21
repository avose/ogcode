################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds code for representing and manipulating G-Code.
'''
################################################################################################

from typing import Optional, List

# Example G-Code lines.
'''
G90
G20
G17 G64 P0.001 M3 S16
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

################################################################################################
class gcParam():
    
    def __init__(self, name: Optional[str] = None, value: Optional[float] = None,
                 text: Optional[str] = None):
        # Validate arguments.
        if ((text is None and (name is None or value is None)) or
            (text is not None and (name is not None or value is not None))):
            raise ValueError("ERROR: Constructor requires either name and value or text.")
        if name is not None:
            if not isinstance(name, str):
                raise ValueError("ERROR: 'name' must be None or string.")
        if text is not None:
            if not isinstance(text, str):
                raise ValueError("ERROR: 'text' must be None or string.")
        # Parse text if needed.
        if text is not None:
            try:
                name = text[0:1]
                value = float(text[1:])
            except:
                raise ValueError(f"ERROR: Could not parse G-Code parameter: '{text}'")
        # Set G-Code parameter's name and value.
        try:
            self.name = str(name)
            self.value = float(value)
        except:
            raise ValueError(f"ERROR: Invalid G-Code parameter: '{name}={value}'")
        return

################################################################################################
class gcCommand():
    
    def __init__(self, params: Optional[List[gcParam]] = None, text: Optional[str] = None):
        # Validate arguments.
        if (params is None and text is None) or (params is not None and text is not None):
            raise ValueError("ERROR: Constructor requires either parameters list or text.")
        if params is not None:
            if (not isinstance(params, list) or len(params) == 0 or
                not isinstance(params[0], gcParam)):
                raise ValueError("ERROR: 'params' must be None or non-empty list of gcParam.")
        if text is not None:
            if not isinstance(text, str):
                raise ValueError("ERROR: 'text' must be None or string.")
        # Parse text if needed.
        if text is not None:
            try:
                params = [ gcParam(word) for word in text.split() ]
            except:
                raise ValueError(f"ERROR: Failed to create G-Code parameters from: '{text}'")
            if len(params) == 0:
                raise ValueError(f"ERROR: No G-Code parameters found in: '{text}'")
        # Set G-Code command's parameters.
        self.params = params
        self.code = params[0]
        self.args = params[1:]
        return

################################################################################################
class gcScript():
    
    def __init__(self, commands: Optional[List[gcCommand]] = None, text: Optional[str] = None):
        # Validate arguments.
        if (commands is None and text is None) or (commands is not None and text is not None):
            raise ValueError("ERROR: Constructor requires either command list or text.")
        if commands is not None:
            if (not isinstance(commands, list) or len(commands) == 0 or
                not isinstance(commands[0], gcCommand)):
                raise ValueError("ERROR: 'commands' must be None or non-empty list of gcCommand.")
        if text is not None:
            if not isinstance(text, str):
                raise ValueError("ERROR: 'text' must be None or string.")
        # Parse text if needed.
        if text is not None:
            commands = []
            for ndx, line in enumerate(text.splitlines()):
                try:
                    commands.append(gcCommand(line))
                except:
                    raise ValueError(f"ERROR: Failed to create G-Code command from line {ndx}: '{line}'")
            if len(commands) == 0:
                raise ValueError(f"ERROR: No G-Code commands found in: '{text}'")
        # Set G-Code script's commands.
        self.commands = commands
        return

################################################################################################
