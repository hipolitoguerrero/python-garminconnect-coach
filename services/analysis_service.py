from typing import Dict, Any, List
from datetime import date

class AnalysisService:
    """
    Engine to analyze training performance, comparing planned vs. actual data.
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        self.daily_metrics = data.get("daily_metrics", [])

    def get_performance_summary(self) -> str:
        """
        Generates a summary of training performance for the AI to interpret.
        """
        return "Resumen de rendimiento basado en los últimos 30 días..."

    def analyze_compliance(self) -> Dict[str, Any]:
        """
        Calculates compliance: (Completed Activities / Planned Activities).
        """
        return {"compliance_rate": 0.0}

    def analyze_todays_training(self) -> Dict[str, Any]:
        """
        Analyzes today's activities against recovery metrics to provide real-time coaching feedback.
        """
        today_str = date.today().isoformat()
        today_entry = next((item for item in self.daily_metrics if item.get("date") == today_str), {})
        
        if not today_entry:
            return {"status": "No data", "message": "No hay datos registrados para hoy todavía."}
            
        activities = today_entry.get("activities", [])
        battery = today_entry.get("body_battery", {})
        
        # Simple analysis
        battery_score = 100
        if isinstance(battery, list) and len(battery) > 0:
            battery_score = battery[0].get("bodyBatteryHighestValue", 100)
        
        if not activities:
            return {"status": "Rest", "message": "Hoy es día de descanso o aún no has registrado actividad."}
            
        # Analyze load if activities exist
        activity_count = len(activities)
        if battery_score < 30:
            return {
                "status": "Warning",
                "message": f"Has registrado {activity_count} actividad(es) con el Body Battery bajo ({battery_score}). Considera reducir la intensidad."
            }
        
        return {
            "status": "Good",
            "message": f"Has registrado {activity_count} actividad(es). Tus niveles de recuperación parecen adecuados para el entrenamiento realizado."
        }
