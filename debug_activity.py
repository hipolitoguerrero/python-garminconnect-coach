from services.data_service import GarminDataService
import json

def get_real_activity_details(activity_id):
    service = GarminDataService()
    # Usamos el método que ya existe en la API (basado en garminconnect/client.py)
    details = service.client.get_activity_details(activity_id)
    return details

if __name__ == "__main__":
    # ID de tu Maratón según tu user_profile.json
    activity_id = "22665900279"
    details = get_real_activity_details(activity_id)
    
    with open("activity_details_debug.json", "w", encoding="utf-8") as f:
        json.dump(details, f, indent=4)
    
    # Extraemos solo lo relevante para validación
    summary = details.get('summaryDTO', {})
    print(f"Nombre actividad: {summary.get('activityName')}")
    print(f"Duración (s): {summary.get('duration')}")
    print(f"Distancia (m): {summary.get('distance')}")
