import json
from datetime import date, timedelta
from typing import Any, Dict, List
from garminconnect import Garmin
from core.auth import init_garmin_client

class GarminDataService:
    """
    Service class to handle data extraction from Garmin Connect.
    Provides parametric methods for fetching health and activity data.
    """
    
    def __init__(self, client: Garmin = None):
        self.client = client or init_garmin_client()

    def get_daily_metrics(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Fetches daily health and activity metrics for a specified date range.

        Args:
            start_date (date): Start of the date range.
            end_date (date): End of the date range.

        Returns:
            List[Dict[str, Any]]: A list containing daily snapshots of metrics.
        """
        metrics = []
        current_date = start_date
        while current_date <= end_date:
            cdate = current_date.isoformat()
            print(f"Fetching data for {cdate}...")
            day_data = {
                "date": cdate,
                "readiness": self.client.get_training_readiness(cdate),
                "morning_readiness": self.client.get_morning_training_readiness(cdate),
                "training_status": self.client.get_training_status(cdate),
                "hrv": self.client.get_hrv_data(cdate),
                "sleep": self.client.get_sleep_data(cdate),
                "body_battery": self.client.get_body_battery(cdate),
                "stress": self.client.get_stress_data(cdate),
                "activities": self.client.get_activities_fordate(cdate)
            }
            metrics.append(day_data)
            current_date += timedelta(days=1)
        return metrics

    def get_user_profile(self) -> Dict[str, Any]:
        """Fetches the current user's profile information."""
        return self.client.get_user_summary(date.today().isoformat())

    def get_personal_records(self) -> Dict[str, Any]:
        """Fetches personal bests and records."""
        return self.client.get_personal_record()

    def get_training_plans(self) -> Dict[str, Any]:
        """Fetches available training plans."""
        return self.client.get_training_plans()

    def export_user_profile(self, filename: str = "user_profile.json") -> None:
        """
        Extracts and persists static user data (profile, PRs, plans).
        """
        profile = {
            "summary": self.get_user_profile(),
            "personal_records": self.get_personal_records(),
            "training_plans": self.get_training_plans()
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)
        print(f"User profile saved to {filename}")

    def export_snapshot(self, days_back: int = 30, filename: str = "garmin_snapshot.json") -> None:
        """
        Extracts metrics for the last N days and saves them to a JSON file.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        snapshot = {
            "metadata": {
                "period": f"{start_date} to {end_date}",
                "days": days_back
            },
            "daily_metrics": self.get_daily_metrics(start_date, end_date)
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)
        print(f"Data successfully exported to {filename}")

if __name__ == "__main__":
    service = GarminDataService()
    service.export_snapshot(days_back=30, filename="garmin_30d_snapshot.json")
