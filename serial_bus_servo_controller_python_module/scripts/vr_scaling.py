import numpy as np

# Define the VR space range (example values)
vr_x_min, vr_x_max = 0.0, 0.532
vr_z_min, vr_z_max = -0.5, 0.453

# Define the arm operational range
arm_x_min, arm_x_max = 0.0, 29.8
arm_z_min, arm_z_max = -29.8, 29.8

def clamp(val, min_val, max_val):
    return max(min(val, max_val), min_val)

def scale_vr_to_arm(vr_x, vr_z):
    """
    Scales VR controller (x, z) input into robot arm's operational (x, z) range.
    """
    
    # Clamp raw input just in case
    vr_x = max(min(vr_x, vr_x_max), vr_x_min)
    vr_z = max(min(vr_z, vr_z_max), vr_z_min)
    
    arm_x = np.interp(vr_x, [vr_x_min, vr_x_max], [arm_x_min, arm_x_max])
    arm_z = np.interp(vr_z, [vr_z_min, vr_z_max], [arm_z_min, arm_z_max])
    print(f"Scaled X: {arm_x}, Scaled Z: {arm_z}")
    return arm_x, arm_z

def polar_arc_mapping(vr_x):
    """
    Optional: Maps VR x position into angle and calculates robot arm position on a circular arc.
    """
    angle_deg = np.interp(vr_x, [vr_x_min, vr_x_max], [90, 0])
    radius = 29.8
    x = radius * np.cos(np.radians(angle_deg))
    z = radius * np.sin(np.radians(angle_deg))
    return x, z

# ~ vr_x = 0.001
# ~ vr_z = 0.475
# ~ scaled_x, scaled_z = scale_vr_to_arm(vr_x, vr_z)
# ~ print(f"Scaled X: {scaled_x}, Scaled Z: {scaled_z}")
