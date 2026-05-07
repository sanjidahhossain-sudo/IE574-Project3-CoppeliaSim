Instructions and Debugging to Run Simulation

- Ensure all files in the same folder to run
- Install Remote API Client in Terminal to ensure Python can communicate with Simulation
	- pip install coppeliasim-zmqremoteapi-client
	- To test connection, run test_connection.py followed by test_signals.py
- Run Python Script align_wafer.py Before Running CoppeliaSim
	- Leave Python script running while running CoppeliaSim but kill script and restart if you switch between simulations, only have one simulation open and running to avoid hang ups
- Update path for model in line #98 in align_wafer.py to properly load CNN model
- No need to retrain model unless wafer changes made or camera changes made
- If retraining required
	- Disable Cairo Script in CoppeliaSim and Enable Camera Training Script 
	- Update loaction for where to save images in script and run simulation
	- Update location for saved imaged and where to save model in train.ipynb
	- run train.ipynb