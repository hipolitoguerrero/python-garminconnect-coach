from pydantic import BaseModel, Field
from typing import Optional, List

class AthleteProfile(BaseModel):
    # Identificación básica
    name: Optional[str] = None
    weight_kg: Optional[float] = None
    vo2_max_running: Optional[float] = None
    lactate_threshold_hr: Optional[int] = None
    lactate_threshold_pace: Optional[str] = None
    
    # Métricas de carga
    acute_training_load: Optional[float] = None
    training_load_focus: Optional[str] = None
    training_status: Optional[str] = None
    
    # Objetivos y Plan
    active_goals: List[dict] = []
    upcoming_races: List[dict] = []
    training_plan: List[dict] = []
    training_history: List[dict] = []
    health_history: List[dict] = [] # Historial de Readiness, HRV, Sueño, etc.
    personal_records: List[dict] = [] # Mejores marcas (1k, 5k, 10k, etc.)
    race_predictions_history: List[dict] = [] # Evolución de pronósticos (5k, 10k, etc.)
    training_status_history: List[dict] = [] # Evolución del estado (Productivo, Peaking, etc.)
    vo2_max_history: List[dict] = [] # Historial de VO2 Max
    lactate_threshold_history: List[dict] = [] # Historial de Umbral de Lactato (FC y Ritmo)
    equipment: List[dict] = [] # Equipamiento (Calzado, sensores, etc.)
    nutrition_standard: dict = {"gel_carbs_g": 23}
    
    def save(self, path: str):
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=4))
