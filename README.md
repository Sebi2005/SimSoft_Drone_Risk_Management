# 🛡️ SimSoft: Rogue Drone Early Warning System
​Real-time Airspace Monitoring & AI Trajectory Prediction
​SimSoft is a tactical 3D radar console designed to detect, track, and predict the movement of unauthorized drones. Using a Stacked LSTM neural network, the system projects drone flight paths 10 steps into the future, identifying potential breaches of restricted zones before they occur.
​
## 🚀 Core Features
​
- Tactical 3D Visualization: Built with Streamlit and Pydeck for high-society geospatial rendering.

​- AI Trajectory Engine: A TensorFlow-based LSTM model trained on 10,000+ synthetic flight paths.

​- Intrusion Detection: Real-time risk assessment against 1,200+ restricted airspace zones in Romania.

​- Multi-Behavior Tracking: Specialized handling for Straight, Curve, and Zig-Zag flight maneuvers.

​- Incident Logging: Automated CSV persistence for historical flight analysis.
​
## 🛠️ Project Architecture
​
- radar.py: The central engine for data fusion and synthetic drone generation.
​
- ui.py: The Streamlit-based frontend for the tactical dashboard.
​
- ai_predictor.py: Inference engine that converts raw GPS history into 3D future vectors.
​
- drone_model.py: Neural network architecture and training logic.
  
​- risk_calculator.py: Geometry-based engine for detecting zone violations.

​- airspace_manager.py: Handler for loading and rendering restricted geo-polygons.

## ​📦 Setup & Installation
1. Clone the repository:

git clone https://github.com/[YOUR-USERNAME]/SimSoft.git

cd SimSoft

2. Environment setup
python -m venv .venv

source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
3. Run the Console
streamlit run ui.py


## 🧠 AI Training Pipeline

​To retrain the "Brain" or test the tracking logic:

​Generate Data: python generate_training_data.py (Generates 10k normalized samples).

​Train Model: python train_model.py (Produces drone_model.h5).

​Verify Logic: python visualize_ai.py (Displays the 10-drone stress test grid).

## 🤝 Collaboration
​Branching: Always create a feature branch for AI symmetry fixes.

​Model Sync: Note that drone_model.h5 is a binary file; ensure you are using the latest version shared in the team repository.
