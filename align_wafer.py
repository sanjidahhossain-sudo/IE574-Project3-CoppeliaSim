# Install Remote API Client in Terminal using line below
# pip install coppeliasim-zmqremoteapi-client

import numpy as np
import cv2
import torch
import torch.nn as nn
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Model definition
class NotchCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 16, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(16, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),
        )
        self.fc = nn.Sequential(
            nn.Linear(64 * 45, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 2)
        )
    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

# Edge extraction 
def extract_edge_profile(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print('No contours found')
        return None
    
    wafer = max(contours, key=cv2.contourArea)
    M = cv2.moments(wafer)
    if M['m00'] == 0:
        return None
    
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    _, radius = cv2.minEnclosingCircle(wafer)
    sample_radius = int(radius * 0.95)
    
    profile = []
    for i in range(360):
        angle = np.radians(i)
        x = int(cx + sample_radius * np.cos(angle))
        y = int(cy + sample_radius * np.sin(angle))
        x = np.clip(x, 0, img.shape[1] - 1)
        y = np.clip(y, 0, img.shape[0] - 1)
        profile.append(gray[y, x] / 255.0)
    
    return np.array(profile, dtype=np.float32)

# Inference
def predict_rotation(model, img):
    profile = extract_edge_profile(img)
    if profile is None:
        return 0.0
    
    model.eval()
    with torch.no_grad():
        x = torch.tensor(profile).unsqueeze(0)
        output = model(x)
        notch_angle = torch.atan2(output[0, 0], output[0, 1]).item()
    
    delta = -notch_angle
    while delta >  np.pi: delta -= 2 * np.pi
    while delta < -np.pi: delta += 2 * np.pi
    
    print(f'Notch at {np.degrees(notch_angle):.1f}° → rotate {np.degrees(delta):.1f}°')
    return delta

# Image conversion 
def coppeliasim_img_to_numpy(img_bytes, w, h):
    img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    img_np = img_np.reshape((h, w, 3))
    img_np = cv2.flip(img_np, 0)
    img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    return img_np

# Setup
MODEL_PATH = r'C:\Users\metro\OneDrive\Desktop\IE574\Project 3\notch_model.pth' # IMPORTANT!! UPDATE MODEL PATH TO WHERE YOU SAVED IT

print('Loading model...')
model = NotchCNN()
model.load_state_dict(torch.load(MODEL_PATH, map_location='cpu'))
model.eval()

print('Connecting to CoppeliaSim...')
client = RemoteAPIClient()
sim    = client.getObject('sim')

camera = sim.getObject('/Moscow/Aligner_Camera')
motor  = sim.getObject('/Moscow/Aligner_Motor')
print('Waiting for alignment trigger...')

# Main loop 
while True:
    trigger = sim.getInt32Signal('align_trigger')
    
    if trigger is not None and trigger == 1:
        print('\nTrigger received! Capturing image...')
        sim.clearInt32Signal('align_trigger')
        
        # Capture image
        sim.handleVisionSensor(camera)
        img_bytes, resolution = sim.getVisionSensorImg(camera)
        w, h = resolution[0], resolution[1]
        img_np = coppeliasim_img_to_numpy(img_bytes, w, h)
        
        # Run inference
        rotation_needed = predict_rotation(model, img_np)
        
        # Command motor
        current_angle = sim.getJointPosition(motor)
        target_angle  = current_angle + rotation_needed
        
        sim.setJointTargetVelocity(motor, 0.3)
        sim.setJointTargetPosition(motor, target_angle)
        
        # Wait for motor to reach target
        tolerance = np.radians(1)
        while True:
            current = sim.getJointPosition(motor)
            if abs(current - target_angle) < tolerance:
                break
            time.sleep(0.05)
        
        sim.setJointTargetVelocity(motor, 0)
        sim.setInt32Signal('align_done', 1)
        print('Alignment complete!')
    
    time.sleep(0.05)