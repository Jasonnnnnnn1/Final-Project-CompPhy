'''9-foot american pool table'''
'''Screen values'''
# Screen size
SCREEN_W = 1200
SCREEN_H = 700
# FPS
FPS = 60
# Margin between screen and the table edge
MARGIN = 80
# The entire table width and height in the screen
SCREEN_TABLE_W = SCREEN_W - (MARGIN * 2)
SCREEN_TABLE_H = SCREEN_H - (MARGIN * 2)

'''Real life values of billiard things'''
# Real table size in SI units
TABLE_LENGTH_M = 2.54
TABLE_WIDTH_M = 1.27

# Pixel scale used only for rendering and pixel-space motion
PX_PER_M = SCREEN_TABLE_W / TABLE_LENGTH_M
M_PER_PX = 1.0 / PX_PER_M

# Real dimensions in SI units
BALL_DIAMETER_M = 0.06
BALL_RADIUS_M = BALL_DIAMETER_M / 2.0
CORNER_POCKET_LENGTH_M = 0.114
SIDE_POCKET_LENGTH_M = 0.130
RAIL_WIDTH_M = 0.127
CUSHION_WIDTH_M = 0.051

# Pixel-space render values derived from SI measurements
BALL_RADIUS = int(round(BALL_RADIUS_M * PX_PER_M))
CORNER_POCKET_LENGTH = int(round(CORNER_POCKET_LENGTH_M * PX_PER_M))
SIDE_POCKET_LENGTH = int(round(SIDE_POCKET_LENGTH_M * PX_PER_M))
RAIL_W = int(round(RAIL_WIDTH_M * PX_PER_M))
CUSHION_WIDTH = int(round(CUSHION_WIDTH_M * PX_PER_M))

# Ball mass in kilograms
BALL_MASS = 0.170

'''Physics'''
# Cue force in newtons (N)
MIN_FORCE = 50.0
MAX_FORCE = 1000.0
INIT_FORCE = 500.0

# Approximate cue-ball contact time in seconds
CUE_CONTACT_TIME_S = 0.001

# Ball-to-cloth sliding friction coefficient
SLIDING_FRICTION = 0.18

# Rolling resistance coefficient
ROLLING_FRICTION = 0.02
CUSHION_RESTITUTION = 0.98  # Coefficient of restitution for ball-cushion collision (energy loss)
BALL_RESTITUTION = 0.95  # Coefficient of restitution for ball-ball collision

# Gravity in SI units
GRAVITY_MPS2 = 9.81


'''Drawing'''

# Make the value higher for larger hitbox radius, make it smaller for a smaller hitbox radius
# Basically this value will be multiplied by the pocket length, normally to get radius is length / 2
# We can modify this by changing the values to bigger or smaller
HITBOX_STRICTNESS = 0.55

def generate_8ball_layout():
    # Calculate the exact vertical center of the playable table surface
    play_top = MARGIN + RAIL_W
    play_bottom = (MARGIN + SCREEN_TABLE_H) - RAIL_W
    center_y = play_top + (play_bottom - play_top) // 2
    
    # Calculate spots: 8 ball at 75%, Cue ball at 25%
    play_left = MARGIN + RAIL_W
    play_right = (MARGIN + SCREEN_TABLE_W) - RAIL_W
    playable_length = play_right - play_left
    
    foot_spot_x = play_left + int(playable_length * 0.75)
    head_spot_x = play_left + int(playable_length * 0.25)

    # Geometry variables
    diameter = BALL_RADIUS * 2
    row_spacing_x = int(diameter * 0.866) 
    row_step_y = BALL_RADIUS 

    # We start with just the Cue Ball
    layout = [
        {"x": head_spot_x, "y": center_y, "color": (240, 240, 240), "is_cue": True, "img": "Assets/cue.png"}
    ]

    # Structure of the 5 triangle rows (number of balls per row)
    rows_structure = [1, 2, 3, 4, 5]
    
    # Track which pool ball number we are on (1 to 15)
    # The 8-ball needs to be hardcoded in the 5th position of the array
    # while ball number 1 needs to be on top and the rest can be random
    ball_order = [
        1,       # Row 1
        2, 9,    # Row 2
        3, 8, 10, # Row 3 
        4, 11, 5, 12, # Row 4
        6, 13, 14, 7, 15 # Row 5
    ]
    
    order_index = 0

    # Build the triangle grid
    for row_idx, num_balls in enumerate(rows_structure):
        row_x = foot_spot_x + (row_idx * row_spacing_x)
        
        # Calculate the starting top-most Y position for this row
        start_y = center_y - (row_idx * row_step_y)
        
        for ball_idx in range(num_balls):
            ball_y = start_y + (ball_idx * diameter)
            ball_number = ball_order[order_index]
            
            layout.append({
                "x": row_x,
                "y": ball_y,
                "color": (20, 20, 20) if ball_number == 8 else (200, 50, 50), # any other color
                "is_black": ball_number == 8,
                "img": f"Assets/ball_{ball_number}.png" # Generates ball_1.png to ball_15.png sprites
            })
            order_index += 1
    return layout

# Initialize layout
INITIAL_LAYOUT = generate_8ball_layout()
print(INITIAL_LAYOUT)