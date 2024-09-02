import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D

# Example pitch data dictionary
pitch_data = {
    "startSpeed": 89.8,
    "endSpeed": 83.3,
    "strikeZoneTop": 3.63,
    "strikeZoneBottom": 1.75,
    "coordinates": {
        "aY": 24.192402588488775,
        "aZ": -24.953563295291566,
        "pfxX": 8.135390543201204,
        "pfxZ": 4.122800109581617,
        "pX": 0.8174363213600242,
        "pZ": 2.007015129059137,
        "vX0": -6.744064447181318,
        "vY0": -130.6190151902887,
        "vZ0": -4.924543372971678,
        "x": 85.84,
        "y": 184.59,
        "x0": 2.35971254815119,
        "y0": 50.00029581099369,
        "z0": 5.762964984175854,
        "aX": 14.236765924399077,
    },
    "breaks": {
        "breakAngle": 7.2,
        "breakVertical": -26.9,
        "breakVerticalInduced": 6.7,
        "breakHorizontal": -13.4,
        "spinRate": 2376,
        "spinDirection": 140,
    },
    "zone": 9,
    "plateTime": 0.4172825244686411,
    "extension": 6.44999365230156,
}

# Time parameters
t = np.linspace(0, pitch_data['plateTime'], 100)  # Time from release to plate

# Calculate the trajectory
vX0 = pitch_data['coordinates']['vX0']
vY0 = pitch_data['coordinates']['vY0']
vZ0 = pitch_data['coordinates']['vZ0']
aX = pitch_data['coordinates']['aX']
aY = pitch_data['coordinates']['aY']
aZ = pitch_data['coordinates']['aZ']

x = vX0 * t + 0.5 * aX * t**2
y = vY0 * t + 0.5 * aY * t**2  # Pitch travels forward to the plate
z = vZ0 * t + 0.5 * aZ * t**2

# Create a 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Set limits for the plot
ax.set_xlim([-1, 1])  # x range for horizontal break
ax.set_ylim([0, 60])  # y range from pitcher's hand to the plate
ax.set_zlim([0, 6])   # z range for height above ground

# Create the ball plot object
ball, = ax.plot([], [], [], 'o', color='red')

# Function to update the animation at each frame
def update(frame):
    ball.set_data(x[frame], y[frame])
    ball.set_3d_properties(z[frame])
    return ball,

# Create the animation
ani = animation.FuncAnimation(fig, update, frames=len(t), interval=20, blit=True)

# Show the animation
plt.show()
