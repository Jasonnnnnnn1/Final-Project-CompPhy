'''9-foot american pool table'''
'''Screen values'''
# Screen size
SCREEN_LENGTH = 1200
SCREEN_HEIGHT = 700
# FPS
FPS = 60
# Margin between screen and the table edge
MARGIN = 80
# The entire table length and height in the screen
SCREEN_TABLE_LENGTH = SCREEN_LENGTH - (MARGIN * 2)
SCREEN_TABLE_HEIGHT = SCREEN_HEIGHT - (MARGIN * 2)

'''Real life values of billiard things'''
# Real table size in SI units
TABLE_LENGTH_M = 2.54
TABLE_HEIGHT_M = 1.27

# Pixel scale used only for rendering and pixel-space motion
# Screen length which is pixel / real world table length which is meters
PX_PER_M = SCREEN_TABLE_LENGTH / TABLE_LENGTH_M
M_PER_PX = 1.0 / PX_PER_M

# Real dimensions in SI units
BALL_DIAMETER_M = 0.06
BALL_RADIUS_M = BALL_DIAMETER_M / 2.0
CORNER_POCKET_LENGTH_M = 0.114
SIDE_POCKET_LENGTH_M = 0.130
RAIL_WIDTH_M = 0.127
CUSHION_WIDTH_M = 0.051

# Convert the SI to pixel
BALL_RADIUS = BALL_RADIUS_M * PX_PER_M
CORNER_POCKET_LENGTH = CORNER_POCKET_LENGTH_M * PX_PER_M
SIDE_POCKET_LENGTH = SIDE_POCKET_LENGTH_M * PX_PER_M
RAIL_W = RAIL_WIDTH_M * PX_PER_M
CUSHION_WIDTH = CUSHION_WIDTH_M * PX_PER_M

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
ROLLING_FRICTION = 0.03
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
    play_bottom = (MARGIN + SCREEN_TABLE_HEIGHT) - RAIL_W
    center_y = play_top + (play_bottom - play_top) // 2
    
    # Calculate spots: 8 ball at 75%, Cue ball at 25%
    play_left = MARGIN + RAIL_W
    play_right = (MARGIN + SCREEN_TABLE_LENGTH) - RAIL_W
    playable_length = play_right - play_left
    
    foot_spot_x = play_left + int(playable_length * 0.75)
    head_spot_x = play_left + int(playable_length * 0.25)

    # Spacing for triangle rack: x uses 86.6% of diameter (equilateral triangle geometry = cos(30)), y uses radius
    diameter = BALL_RADIUS * 2
    row_spacing_x = int(diameter * 0.866) 
    row_step_y = BALL_RADIUS 

    # lets start with just the cue ball first
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

    # Let's trace ball 1 to see this code in action 
    # ball trace: enumerate gives row_idx=0, num_balls=1 (first item in rows_structure)
    for row_idx, num_balls in enumerate(rows_structure):
        # ball trace: row_x = foot_spot_x + (0 * row_spacing_x) = foot_spot_x, so for ball 1 no x shift
        row_x = foot_spot_x + (row_idx * row_spacing_x)
        # ball trace: start_y = center_y - (0 * row_step_y) = center_y, again for ball 1 no y offset
        start_y = center_y - (row_idx * row_step_y)
        
        # ball trace: num_balls=1 so this inner loop only runs once, ball_idx=0
        for ball_idx in range(num_balls):
            # ball trace: ball_y = center_y + (0 * diameter) = center_y, dead center
            ball_y = start_y + (ball_idx * diameter)
            # ball trace: order_index=0 so ball_order[0] = 1, thats our ball
            ball_number = ball_order[order_index]
            
            layout.append({
                # ball trace: final position is (foot_spot_x, center_y), top of the rack
                "x": row_x,
                "y": ball_y,
                "color": (20, 20, 20) if ball_number == 8 else (200, 50, 50),
                "is_black": ball_number == 8,
                "img": f"Assets/ball_{ball_number}.png"
            })
            order_index += 1
    return layout

# Initialize layout
INITIAL_LAYOUT = generate_8ball_layout()
print(INITIAL_LAYOUT)