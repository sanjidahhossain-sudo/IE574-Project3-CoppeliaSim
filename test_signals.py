from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import time

client = RemoteAPIClient()
sim = client.getObject('sim')
print('Connected!')

# Start simulation first
sim.startSimulation()
print('Simulation started')
time.sleep(1)

# Test setting and reading a signal
sim.setInt32Signal('test_signal', 42)

value = sim.getInt32Signal('test_signal')
print(f'Read back signal value: {value}')  # should print 42

# Test clearing
sim.clearInt32Signal('test_signal')
value = sim.getInt32Signal('test_signal')
print(f'After clear: {value}')  # should print None

# Test motor handle
motor = sim.getObject('/Moscow/Aligner_Motor')
pos = sim.getJointPosition(motor)
print(f'Motor position: {pos} radians ({round(pos * 57.2958, 2)} degrees)')

# Test camera capture
camera = sim.getObject('/Moscow/Aligner_Camera')
sim.handleVisionSensor(camera)
img_bytes, resolution = sim.getVisionSensorImg(camera)
print(f'Image captured: {resolution[0]}x{resolution[1]} pixels')
print(f'Image data length: {len(img_bytes)} bytes')

sim.stopSimulation()
print('Done')