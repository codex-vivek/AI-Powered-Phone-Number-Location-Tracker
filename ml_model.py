import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import random

class SafetyModel:
    def __init__(self):
        # We'll simulate a trained model here. 
        # In a real app, this would be loaded from a pickle file.
        # For this interactive demo, we'll create a simple logic-based "AI" 
        # that mimics behavioral analysis.
        pass

    def analyze_behavior(self, tactical_data):
        """Analyzes tactical metadata for registry-level integrity."""
        score = 98
        alerts = []
        
        # Registry Integrity Check
        registry = tactical_data.get('registry', 'UNKNOWN')
        if registry == "HLR_LOCAL_CACHE":
            alerts.append("Data Source: Sovereign HLR Registry (Verified).")
        
        # Signal Protocol Analysis
        signal = tactical_data.get('signal', '')
        if "ENCRYPTED" in signal:
            alerts.append("Protocol: End-to-End GSM Encryption Active.")
        else:
            score -= 5
            
        # Uptime / Persistence Check
        uptime = tactical_data.get('uptime', '0')
        if uptime == "CONTINUOUS":
            alerts.append("Service Status: Always-On Node detected.")
        else:
            try:
                up_val = int(str(uptime).split(' ')[0])
                if up_val > 500:
                    alerts.append("Long-duration session persistence detected.")
            except:
                pass

        return {
            "threat_score": score,
            "alerts": alerts if alerts else ["No integrity anomalies detected."]
        }

    def predict_safety(self, phone_number):
        """
        Predicts a safety score and category based on 'features' of the phone number.
        """
        num_str = str(phone_number.national_number)
        length = len(num_str)
        
        digit_counts = {}
        for d in num_str:
            digit_counts[d] = digit_counts.get(d, 0) + 1
        max_freq = max(digit_counts.values()) if digit_counts else 0
        unique_digits = len(set(num_str))
        
        score = 100
        reasons = []

        if length < 8 or length > 12:
            score -= 20
            reasons.append("Irregular MSISDN bit-length.")
        
        if max_freq > (length / 2):
            score -= 30
            reasons.append("Automated pattern detected (Repetitive bits).")
        
        if unique_digits < 4:
            score -= 15
            reasons.append("Low entropy digital signature.")

        # Simulate Neural Network Confidence
        score -= random.randint(0, 5)
        score = max(5, min(100, score))

        if score > 80:
            category = "CLEAN / LOW RISK"
        elif score > 50:
            category = "NEUTRAL / MONITORING"
        else:
            category = "CRIMINAL / SPOOFED"

        return {
            "score": score,
            "category": category,
            "reasons": reasons if reasons else ["Clear communication signal."]
        }
