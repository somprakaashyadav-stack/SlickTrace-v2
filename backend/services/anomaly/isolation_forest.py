from sklearn.ensemble import IsolationForest
import numpy as np

def run_isolation_forest(features: list) -> float:
    """
    Runs Isolation Forest on a 1D feature vector for a single vessel.
    In a real system, the forest would be trained on historical AIS tracks.
    For this prototype, we fit the model dynamically on a synthetic 
    distribution mimicking 'normal' behavior to score this vessel.
    
    features: [speed_variance, heading_variance, gap_frequency, origin_proximity_factor]
    Returns: trajectory_anomaly_score (0.0 to 1.0)
    """
    
    # Generate synthetic baseline "normal" data (100 samples)
    # normal speed variance ~ low, normal heading var ~ low, zero gaps, low origin prox
    np.random.seed(42)
    baseline_data = np.column_stack((
        np.random.normal(loc=1.0, scale=0.5, size=100),   # speed_variance
        np.random.normal(loc=5.0, scale=2.0, size=100),   # heading_variance
        np.zeros(100),                                    # gap_frequency
        np.random.normal(loc=0.1, scale=0.1, size=100)    # origin_proximity
    ))
    
    # Inject our target vessel's feature vector
    target = np.array(features).reshape(1, -1)
    
    X = np.vstack([baseline_data, target])
    
    # Train Isolation Forest
    clf = IsolationForest(n_estimators=50, max_samples='auto', contamination=0.1, random_state=42)
    clf.fit(X)
    
    # Get anomaly score (negative is more anomalous, standard scale is ~ -0.5 to 0.5)
    # We want to scale it from 0.0 (normal) to 1.0 (highly anomalous)
    scores = clf.decision_function(target)
    raw_score = scores[0]
    
    # decision_function returns > 0 for inliers, < 0 for outliers
    # Let's map raw_score to 0-1
    if raw_score >= 0:
        return 0.0  # Normal
    else:
        # Scale negative score to positive 0-1
        return min(1.0, abs(raw_score) * 2.0)
