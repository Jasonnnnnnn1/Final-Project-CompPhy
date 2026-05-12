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
# Real table size
REAL_TABLE_W_CM = 254
REAL_TABLE_H_CM = 127

# Calculate the scale pixel/cm
SCALE = SCREEN_TABLE_W / REAL_TABLE_W_CM 

# Derive everything else from the calculated scale
BALL_RADIUS          = int((5.72  / 2) * SCALE)
CORNER_POCKET_LENGTH = int(11.4 * SCALE)
SIDE_POCKET_LENGTH   = int(13.0 * SCALE)
RAIL_W               = int(12.7 * SCALE)
CUSHION_WIDTH        = int(5.1 * SCALE)

# Ball mass in KG
BALL_MASS = 0.16

'''Physics'''
MIN_FORCE = 1
MAX_FORCE = 3000
BALL_FRICTION = 1.7
CUSHION_RESTITUTION = 0.81  # Coefficient of restitution for ball-cushion collision (energy loss)