from coppeliasim_zmqremoteapi_client import RemoteAPIClient

print('Connecting to CoppeliaSim...')
client = RemoteAPIClient()
sim = client.getObject('sim')
print('Connected!')

# Get simulation state
state = sim.getSimulationState()
print(f'Simulation state: {state}')
# 0 = stopped, 1 = running, 2 = paused

# Try getting an object handle
try:
    camera = sim.getObject('/Moscow/Aligner_Camera')
    print(f'Camera handle: {camera}')
except Exception as e:
    print(f'Camera error: {e}')

try:
    motor = sim.getObject('/Moscow/Aligner_Motor')
    print(f'Motor handle: {motor}')
except Exception as e:
    print(f'Motor error: {e}')

print('Done')