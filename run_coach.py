import json
import os
from datetime import date
from services.data_service import GarminDataService
from services.analysis_service import AnalysisService

def run_coach_session(force_refresh: bool = False):
    # 1. Load configuration and user profile
    with open("config/coach_personality.json", "r", encoding="utf-8") as f:
        personality = json.load(f)
    
    service = GarminDataService()
    
    # Initialize User Profile if needed
    profile_filename = "user_profile.json"
    if not os.path.exists(profile_filename) or force_refresh:
        print("Obteniendo perfil de usuario...")
        service.export_user_profile(filename=profile_filename)
        
    with open(profile_filename, "r", encoding="utf-8") as f:
        user_profile = json.load(f)
    
    athlete_name = user_profile['summary'].get('displayName', 'Atleta')
    
    print(f"--- Iniciando sesión con {personality['name']} ---")
    print(f"Hola {athlete_name}, vamos a revisar tu rendimiento.")
    print(f"Objetivo: {personality['goal']}\n")

    # 2. Manage Data
    filename = "temp_data.json"
    if not os.path.exists(filename) or force_refresh:
        print("Descargando datos frescos de Garmin...")
        service.export_snapshot(days_back=30, filename=filename)
    else:
        print("Usando datos cacheados...")

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 3. Analyze
    analysis = AnalysisService(data)
    todays_analysis = analysis.analyze_todays_training()

    # 4. Generate Report
    print("--- Análisis del Coach IA ---")
    print(f"Estado de hoy: {todays_analysis['message']}")
    
    # Show activities for today
    today_str = date.today().isoformat()
    today_data = next((item for item in data['daily_metrics'] if item.get('date') == today_str), {})
    
    # Correctly access nested activity structure
    activities_container = today_data.get('activities', {})
    activities_payload = activities_container.get('ActivitiesForDay', {}).get('payload', [])
    
    if activities_payload:
        print("\nActividades realizadas hoy:")
        for act in activities_payload:
            name = act.get('activityName', 'Desconocido')
            duration = act.get('duration', 0) / 60
            dist = act.get('distance', 0) / 1000
            print(f"- {name}: {dist:.2f} km en {duration:.1f} min")
    else:
        print("\nNo hay actividades registradas hoy en el payload.")


if __name__ == "__main__":
    import sys
    refresh = "--refresh" in sys.argv
    run_coach_session(force_refresh=refresh)
