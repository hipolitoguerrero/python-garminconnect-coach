#!/usr/bin/env python3
"""
Lightweight script to extract Readiness, HRV, and Sleep metrics.
"""
import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from garminconnect import Garmin

# Load environment variables from .env
load_dotenv()

def get_readiness_metrics():
    tokenstore = str(Path("~/.garminconnect").expanduser())
    
    # Attempt login
    try:
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        
        if not email or not password:
            print("Error: EMAIL and PASSWORD environment variables must be set.")
            return

        api = Garmin(email, password, prompt_mfa=lambda: input("MFA code: ").strip())
        api.login(tokenstore)
        
        today = date.today().isoformat()
        
        print(f"\n--- RECOVERY METRICS FOR {today} ---")
        
        # Readiness
        readiness = api.get_training_readiness(today)
        r_score = readiness[0].get("score") if isinstance(readiness, list) else readiness.get("score")
        r_level = readiness[0].get("level") if isinstance(readiness, list) else readiness.get("level")
        print(f"Readiness Score: {r_score} ({r_level})")
        
        # HRV
        hrv = api.get_hrv_data(today)
        hrv_summary = hrv.get("hrvSummary", {}) if hrv else {}
        hrv_val = hrv_summary.get("last_night_avg", "N/A")
        hrv_status = hrv_summary.get("status", "N/A")
        print(f"HRV: {hrv_val} ({hrv_status})")
        
        # Sleep
        sleep = api.get_sleep_data(today)
        # Garmin API returns sleep data in a complex structure
        sleep_score = sleep.get("dailySleepDTO", {}).get("sleepScore", "N/A") if sleep else "N/A"
        print(f"Sleep Score: {sleep_score}")
        
        # Training Status & Load Balance
        ts = api.get_training_status(today)
        # Load Status (ACWR)
        ts_data = ts.get("mostRecentTrainingStatus", {}).get("latestTrainingStatusData", {})
        device_data = next(iter(ts_data.values())) if ts_data else {}
        acute_load_dto = device_data.get("acuteTrainingLoadDTO", {})
        
        print(f"Acute Load: {acute_load_dto.get('dailyTrainingLoadAcute', 'N/A')}")
        print(f"Status (ACWR): {acute_load_dto.get('acwrStatus', 'N/A')}")
        
        # Load Balance
        lb = ts.get("mostRecentTrainingLoadBalance", {}).get("metricsTrainingLoadBalanceDTOMap", {})
        lb_data = next(iter(lb.values())) if lb else {}
        
        print("\n--- LOAD BALANCE (Monthly) ---")
        print(f"Aerobic Low:   {lb_data.get('monthlyLoadAerobicLow', 'N/A'):.1f}")
        print(f"Aerobic High:  {lb_data.get('monthlyLoadAerobicHigh', 'N/A'):.1f}")
        print(f"Anaerobic:     {lb_data.get('monthlyLoadAnaerobic', 'N/A'):.1f}")
        print(f"Feedback:      {lb_data.get('trainingBalanceFeedbackPhrase', 'N/A')}")
        
        # VO2 Max (Profile)
        profile = api.get_user_profile()
        vo2_max_profile = profile.get("userData", {}).get("vo2MaxRunning", "N/A")
        print(f"\nVO2 Max (Running - Profile): {vo2_max_profile}")
        
        # Lactate Threshold
        lt = api.get_lactate_threshold(latest=True)
        lt_data = lt.get("speed_and_heart_rate", {}) if lt else {}
        lt_hr = lt_data.get("heartRate", "N/A")
        lt_speed_ms = lt_data.get("speed") # Speed in m/s
        
        lt_pace = "N/A"
        if lt_speed_ms and lt_speed_ms > 0:
            pace_min_km = (1000 / lt_speed_ms) / 60
            minutes = int(pace_min_km)
            seconds = int((pace_min_km - minutes) * 60)
            lt_pace = f"{minutes}:{seconds:02d} min/km"
            
        print(f"Lactate Threshold HR: {lt_hr} bpm")
        print(f"Lactate Threshold Pace: {lt_pace}")

        # Heart Rate
        hr_data = api.get_heart_rates(today)
        resting_hr = hr_data.get("restingHeartRate", "N/A")
        print(f"Resting Heart Rate: {resting_hr}")

        # Body Battery
        bb_data = api.get_body_battery(today)
        bb_val = "N/A"
        if bb_data:
            # Body battery data is typically a list, we take the last entry
            bb_val = bb_data[-1].get("bodyBatteryValue", "N/A") if isinstance(bb_data, list) else bb_data.get("bodyBatteryValue", "N/A")
        print(f"Body Battery: {bb_val}")
        
        # All Day Stress
        stress = api.get_all_day_stress(today)
        stress_val = stress.get("avgStressLevel", "N/A") if stress else "N/A"
        print(f"Average Stress Level: {stress_val}")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    get_readiness_metrics()
