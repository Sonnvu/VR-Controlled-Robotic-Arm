# coding: utf-8
import serial
import time
import numpy as np
import vr_scaling

class SBS_Controller:
    def __init__(self, dev, baud_rate=9600):
        """
        SBS_Controller: Serial Bus Servo controller class.
                        By using this class, you can control servos with Serial Bus Servo Controller.
                        Serial Bus Servo Controller (https://www.hiwonder.hk/products/serial-bus-servo-controller)
        functions:
            cmd_servo_move
            cmd_get_battery_voltage
            cmd_mult_servo_unload
            cmd_mult_servo_pos_read
        Prameters:
            dev: string
                e.g. dev = "/dev/ttyUSB0"
            baud_rate: int
                e.g. baud_rate = 9600 
                (note. Serial bus servo communication Baud Rate is 115200 baud.
                       On the other hand, LSC Series Servo Controller communication Baud Rate is 9600 baud.
                       For this reason, You have to select 9600 baud.
                       Don't get confused.)
        """
        self.ser = serial.Serial(dev, baud_rate)

    def cmd_servo_move(self, servo_id, angle_position, time):
        """
        Description: Control the rotation of any servo.
                     The rotation time of all servos commanded by this function will be the same.
        Parameters: 
            servo_id: list
                e.g. servo_id = [1, 2, 3, 4]   
            angle_position: list
                e.g. angle_position = [1000, 2000, 1000, 2000]  
                (note. The number of elements must be the same as servo_id)
            time: int (ms)
                e.g. time = 1000    
        return:
        """
        buf = bytearray(b'\x55\x55')                # header 
        buf.extend([0xff & (len(servo_id)*3+5)])    # length (the number of control servo * 3 + 5)
        buf.extend([0x03])                          # command value

        buf.extend([0xff & len(servo_id)])          # The number of servo to be controlled
        
        time = 0xffff & time
        buf.extend([(0xff & time), (0xff & (time >> 8))])   # Lower and Higher 8 bits of time value

        for i in range(len(servo_id)):
            p_val = 0xffff & angle_position[i]
            buf.extend([0xff & servo_id[i]])    # servo id
            buf.extend([(0xff & p_val), (0xff & (p_val >> 8))])   # Lower and Higher 8 bits of angle posiotion value

        self.ser.write(buf)

    def cmd_get_battery_voltage(self):
        """
        Description: Get the servo controller's battery voltage in unit millivolts.
        return: 
            battery_voltage: float (V)
        """
        # transmit
        buf = bytearray(b'\x55\x55')    # header 
        buf.extend([0x02])              # length
        buf.extend([0x0F])              # command value
        # Empty the contents of the cache in preparation for receiving data.
        count = self.ser.inWaiting()    # Check receive cache.
        if count != 0:
            _ = self.ser.read(count)    # Read out data
        # Send command.
        self.ser.write(buf)

        # Receive
        count = 0
        recv_cmd_len = 6
        while count != recv_cmd_len:        # Waiting for reception to finish.
            count = self.ser.inWaiting()
        recv_data = self.ser.read(count)    # Read the received byte data.
        if count == recv_cmd_len:                      # Check if the number of bytes of data received is correct as a response to this command.
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[3] == 0x0F : # Check if the received data is a response to a command.
                battery_voltage = 0xffff & (recv_data[4] | (0xff00 & (recv_data[5] << 8))) # Read battery  voltage
                battery_voltage = battery_voltage / 1000.0

        return battery_voltage

    def cmd_mult_servo_unload(self, servo_id):
        """
        Description: Power off multiple servos and its motors, after sending this command.
        Parameters: 
            servo_id: list
                e.g. servo_id = [1, 2, 3, 4]     
        return:
        """
        buf = bytearray(b'\x55\x55')                # header 
        buf.extend([0xff & (len(servo_id)+3)])      # length (the number of control servo + 3)
        buf.extend([0x14])                          # command value

        buf.extend([0xff & len(servo_id)])          # The number of servo to be controlled.

        for i in range(len(servo_id)):
            buf.extend([0xff & servo_id[i]])    # servo id

        self.ser.write(buf)      

    def cmd_mult_servo_pos_read(self, servo_id):
        """
        Description: Read a angle position values of multiple servos.
        Parameters: 
            servo_id: list
                e.g. servo_id = [1, 2, 3, 4]   
        return: 
            angle_pos_values: list 
                note. The list size is the same as the number of servos you want to get values.
        """
        # transmit
        buf = bytearray(b'\x55\x55')            # header 
        buf.extend([0xff & (len(servo_id)+3)])  # length (the number of control servo + 3)
        buf.extend([0x15])                      # command value
        buf.extend([0xff & len(servo_id)])          # The number of servo to be controlled.

        for i in range(len(servo_id)):
            buf.extend([0xff & servo_id[i]])    # servo id

        # Empty the contents of the cache in preparation for receiving data.
        count = self.ser.inWaiting()    # Check receive cache.
        if count != 0:
            _ = self.ser.read(count)    # Read out data
        # Send command.
        self.ser.write(buf)

        # Receive
        count = 0
        recv_cmd_len = len(servo_id) * 3 + 5
        angle_pos_values = servo_id.copy()  # Create a list whose size is the same as the number of servos you want to get values from.
        while count != recv_cmd_len:        # Waiting for reception to finish.
            count = self.ser.inWaiting()
        recv_data = self.ser.read(count)    # Read the received byte data.
        if count == recv_cmd_len:           # Check if the number of bytes of data received is correct as a response to this command.
            if recv_data[0] == 0x55 and recv_data[1] == 0x55 and recv_data[3] == 0x15:  # Check if the received data is a response to a command.
                for i in range(len(servo_id)):
                    angle_pos_values[i] = 0xffff & (recv_data[6+3*i] | (0xff00 & (recv_data[7+3*i] << 8))) # Read battery  voltage

        return angle_pos_values
     
    def angle_to_servo(self, angle, min_angle, max_angle, min_pos, max_pos):
        return int(np.interp(angle, [min_angle, max_angle], [min_pos, max_pos]))
        
    def angle_to_val(self, angle):
        return int(1000/(210 + 315) * angle)
        
    def clamp_angle(self, angle, min_val, max_val):
        return max(min(angle, max_val), min_val)
        
    def cmd_move_with_angle(self, theta_6, theta_1, theta_2, theta_3, wrist, grip, duration):
        servo_ranges = {
            6: {"angle_min": -90, "angle_max": 90, "pos_min": 100, "pos_max":860},
            5: {"angle_min": 0, "angle_max": 180, "pos_min": 250, "pos_max": 690},
            4: {"angle_min": -135, "angle_max": 127, "pos_min": 1000, "pos_max": 0},
            3: {"angle_min": -103, "angle_max": 120, "pos_min": 75, "pos_max": 1000},
            2: {"angle_min": 0, "angle_max": 180, "pos_min": 900, "pos_max": 20}
        }  
        
        # Check if Joint Angles are valid
        angles = {
            6: theta_6,
            5: theta_1,
            4: theta_2,
            3: theta_3,
            2: wrist
        }
        
        for servo_id, angle in angles.items():
            min_angle = servo_ranges[servo_id]["angle_min"]
            max_angle = servo_ranges[servo_id]["angle_max"]
            clamped_angle = self.clamp_angle(angle, min_angle, max_angle)
            
            if clamped_angle != angle:
                print(f"[ANGLE_ERROR]: Servo {servo_id}: angle {angle} out of range ({min_angle} to {max_angle}) | Map Servo {servo_id} = {clamped_angle}")
                
            angles[servo_id] = clamped_angle
        
        servo_6_pos = self.angle_to_servo(angles[6], servo_ranges[6]["angle_min"], servo_ranges[6]["angle_max"], servo_ranges[6]["pos_min"], servo_ranges[6]["pos_max"])
        servo_5_pos = self.angle_to_servo(angles[5], servo_ranges[5]["angle_min"], servo_ranges[5]["angle_max"], servo_ranges[5]["pos_min"], servo_ranges[5]["pos_max"])
        servo_4_pos = self.angle_to_servo(angles[4], servo_ranges[4]["angle_min"], servo_ranges[4]["angle_max"], servo_ranges[4]["pos_min"], servo_ranges[4]["pos_max"])
        servo_3_pos = self.angle_to_servo(angles[3], servo_ranges[3]["angle_min"], servo_ranges[3]["angle_max"], servo_ranges[3]["pos_min"], servo_ranges[3]["pos_max"])
        servo_2_pos = self.angle_to_servo(angles[2], servo_ranges[2]["angle_min"], servo_ranges[2]["angle_max"], servo_ranges[2]["pos_min"], servo_ranges[2]["pos_max"])
        
        self.cmd_servo_move([6, 5, 4, 3, 2, 1], [servo_6_pos, servo_5_pos, servo_4_pos, servo_3_pos, servo_2_pos, grip], duration)
      
    
    def move_end_effector(self, x3, y3, z3, p, wrist, grip, t):
        # Length of arm segments in cm
        l1 = 10
        l2 = 9.9
        l3 = 10.2
        
        # ~ x3, y3 = vr_scaling.scale_vr_to_arm(x3, y3)
	
        phi = np.deg2rad(p)
        #Calculate the horizontal distance to the targeton XY plane
        r3 = np.sqrt(x3**2 + y3**2)
	
        # Calculate theta_base 
        theta_base = np.arctan2(y3, x3)
	
        # Get r2 and z2
        r2 = r3 - l3*np.cos(phi)
        z2 = z3 - l3*np.sin(phi)
        
        # ~ max_reach = l1 + l2
        # ~ current_distance = np.sqrt(r2**2 + z2**2)
	
        # ~ if current_distance > max_reach:
            # ~ scale_factor = max_reach / current_distance
            # ~ r2 *= scale_factor
            # ~ z2 *= scale_factor
            # ~ print(f"Target out of reach. Moving to closest reachable point: ({r2:.2f}, {z2:.2f})")
	
        c2 = (r2**2 + z2**2 - l1**2 - l2**2)/(2*l1*l2)
        c2 = np.clip(c2, -1.0, 1.0)
        s2 = -np.sqrt(1-c2**2)
        theta_2 = np.arctan2(s2, c2)
	
        s1 = ((l1 + l2*c2)*z2 - l2*s2*r2)/(r2**2 + z2**2)
        c1 = ((l1 + l2*c2)*r2 + l2*s2*z2)/(r2**2 + z2**2)
        theta_1 = np.arctan2(s1, c1)
	
        theta_3 = phi - theta_1 - theta_2
	
        # ~ print('theta_base: ', np.rad2deg(theta_base))
        # ~ print('theta_1: ', np.rad2deg(theta_1))
        # ~ print('theta_2: ', np.rad2deg(theta_2))
        # ~ print('theta_3: ', np.rad2deg(theta_3)) 
        print(f"[Servo_6]: {np.rad2deg(theta_base)}; [Servo_5]: {np.rad2deg(theta_1)}; [Servo_4]: {np.rad2deg(theta_2)}; [theta_3]: {np.rad2deg(theta_3)}")
	
        self.cmd_move_with_angle(np.rad2deg(theta_base), np.rad2deg(theta_1), np.rad2deg(theta_2), np.rad2deg(theta_3), wrist, grip, t)    
        print("Movement Executed Successfully\n")
