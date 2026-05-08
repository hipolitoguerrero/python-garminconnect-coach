import json
from pathlib import Path
from core.auth import GarminSessionManager
from models.athlete import AthleteProfile
from datetime import date

class CoachEngine:
    def __init__(self):
        self.session_manager = GarminSessionManager()
        self.memory_path = Path("memory/athlete_data.json")
        self.persona_path = Path("memory/coach_persona.md")
        self.persona = self.persona_path.read_text() if self.persona_path.exists() else "Coach IA"
        self.profile = self._load_profile()
        # Sincronización automática al inicio de la conversación
        try:
            self.synchronize_athlete_profile()
        except Exception as e:
            print(f"Aviso: No se pudo sincronizar con Garmin al inicio ({e}). Usando datos locales.")

    def _load_profile(self) -> AthleteProfile:
        if self.memory_path.exists() and self.memory_path.stat().st_size > 0:
            try:
                return AthleteProfile.model_validate_json(self.memory_path.read_text())
            except Exception:
                return self.synchronize_athlete_profile()
        return self.synchronize_athlete_profile()

    def _translate_status(self, status: str) -> str:
        """Traduce códigos técnicos de Garmin a lenguaje natural."""
        translations = {
            "PRODUCTIVE_3": "Entrenamiento Productivo",
            "MAINTAINING_AEROBIC_FITNESS_1": "Manteniendo condición aeróbica",
            "LACTATE_THRESHOLD": "Umbral de Lactato",
            "AEROBIC_BASE": "Base Aeróbica",
            "TEMPO": "Ritmo Tempo",
            "OVERREACHING_17": "Sobreentrenando (Carga alta)"
        }
        return translations.get(status, status)

    def synchronize_athlete_profile(self, training_plan_data=None) -> AthleteProfile:
        """Autentica y extrae datos completos desde Garmin para poblar la memoria."""
        api = self.session_manager.get_client()
        today = date.today()
        
        # 1. Perfil y métricas estáticas
        profile_raw = api.get_user_profile()
        user_data = profile_raw.get("userData", {})
        
        # 2. Umbral de lactato
        lt = api.get_lactate_threshold(latest=True)
        lt_data = lt.get("speed_and_heart_rate", {}) if lt else {}
        
        # 3. Carga de entrenamiento
        ts = api.get_training_status(today.isoformat())
        ts_data = ts.get("mostRecentTrainingStatus", {}).get("latestTrainingStatusData", {})
        device_data = next(iter(ts_data.values())) if ts_data else {}
        acute_load_dto = device_data.get("acuteTrainingLoadDTO", {})

        # 4. Próximos eventos
        events_raw = api.get_scheduled_workouts(today.year, today.month)
        upcoming = [
            {"title": e.get("title"), "date": e.get("date"), "isRace": e.get("isRace", False)}
            for e in events_raw.get("calendarItems", [])
            if e.get("itemType") == "event"
        ]

        # 5. Métricas de Salud y Readiness (Nueva sección)
        readiness_raw = api.get_training_readiness(today.isoformat())
        hrv_raw = api.get_hrv_data(today.isoformat())
        sleep_raw = api.get_sleep_data(today.isoformat())
        bb_raw = api.get_body_battery(today.isoformat())
        stress_raw = api.get_all_day_stress(today.isoformat())

        current_health = {
            "date": today.isoformat(),
            "readiness_score": (readiness_raw[0].get("score") if isinstance(readiness_raw, list) else readiness_raw.get("score")) if readiness_raw else "N/A",
            "hrv_last_night": hrv_raw.get("hrvSummary", {}).get("last_night_avg", "N/A") if hrv_raw else "N/A",
            "sleep_score": sleep_raw.get("dailySleepDTO", {}).get("sleepScore", "N/A") if sleep_raw else "N/A",
            "body_battery": (bb_raw[-1].get("bodyBatteryValue", "N/A") if isinstance(bb_raw, list) else bb_raw.get("bodyBatteryValue", "N/A")) if bb_raw else "N/A",
            "stress_avg": stress_raw.get("avgStressLevel", "N/A") if stress_raw else "N/A"
        }

        # Actualizar historial de salud sin duplicados por día
        health_history = self.profile.health_history
        if not any(h.get("date") == today.isoformat() for h in health_history):
            health_history.append(current_health)
        else:
            # Actualizar el registro de hoy si ya existe
            for i, h in enumerate(health_history):
                if h.get("date") == today.isoformat():
                    health_history[i] = current_health
                    break

        # 6. Récords Personales (Nueva sección)
        prs_raw = api.get_personal_record()
        pr_mapping = {
            1: "1 km",
            2: "1 Milla",
            3: "5 km",
            4: "10 km",
            5: "Media Maratón",
            6: "Maratón",
            7: "Distancia más larga"
        }
        
        personal_records = []
        for pr in prs_raw:
            type_id = pr.get("typeId")
            if type_id in pr_mapping:
                value = pr.get("value") # En segundos para tiempo, metros para distancia (tipo 7)
                formatted_value = ""
                if type_id == 7:
                    formatted_value = f"{value/1000:.2f} km"
                else:
                    # Formatear segundos a HH:MM:SS
                    m, s = divmod(int(value), 60)
                    h, m = divmod(m, 60)
                    formatted_value = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
                
                personal_records.append({
                    "distancia": pr_mapping[type_id],
                    "marca": formatted_value,
                    "fecha": pr.get("actStartDateTimeInGMTFormatted", "").split("T")[0] if pr.get("actStartDateTimeInGMTFormatted") else "N/A",
                    "actividad": pr.get("activityName")
                })

        # 7. Pronósticos de Carrera (Bitácora Evolutiva)
        race_pred_raw = api.get_race_predictions()
        def fmt_sec(s):
            m, s = divmod(int(s), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

        current_preds = {
            "date": today.isoformat(),
            "5k": fmt_sec(race_pred_raw.get("time5K", 0)),
            "10k": fmt_sec(race_pred_raw.get("time10K", 0)),
            "half_marathon": fmt_sec(race_pred_raw.get("timeHalfMarathon", 0)),
            "marathon": fmt_sec(race_pred_raw.get("timeMarathon", 0))
        }
        
        race_history = self.profile.race_predictions_history
        if not any(p.get("date") == today.isoformat() for p in race_history):
            race_history.append(current_preds)
        else:
            for i, p in enumerate(race_history):
                if p.get("date") == today.isoformat():
                    race_history[i] = current_preds
                    break

        # 8. Historial de Estado de Entrenamiento
        status_label = self._translate_status(device_data.get("trainingStatusFeedbackPhrase", "Desconocido"))
        current_status_entry = {
            "date": today.isoformat(),
            "status": status_label,
            "acute_load": acute_load_dto.get("dailyTrainingLoadAcute")
        }
        
        status_history = self.profile.training_status_history
        if not any(s.get("date") == today.isoformat() for s in status_history):
            status_history.append(current_status_entry)
        else:
            for i, s in enumerate(status_history):
                if s.get("date") == today.isoformat():
                    status_history[i] = current_status_entry
                    break

        # 9. Historial de VO2 Max
        current_vo2 = user_data.get("vo2MaxRunning")
        vo2_history = self.profile.vo2_max_history
        if current_vo2 and not any(v.get("date") == today.isoformat() for v in vo2_history):
            vo2_history.append({"date": today.isoformat(), "vo2_max": current_vo2})

        # 10. Historial de Umbral de Lactato
        # Convertir velocidad (m/s) a ritmo (min/km)
        lt_speed = lt_data.get("speed") # m/s
        lt_pace = "N/A"
        if lt_speed and lt_speed > 0:
            pace_decimal = 1000 / (lt_speed * 60)
            lt_pace = f"{int(pace_decimal)}:{int((pace_decimal%1)*60):02d}"

        current_lt = {
            "date": today.isoformat(),
            "hr": lt_data.get("heartRate", "N/A"),
            "pace": lt_pace
        }
        
        lt_history = self.profile.lactate_threshold_history
        if current_lt["hr"] != "N/A" and not any(l.get("date") == today.isoformat() for l in lt_history):
            lt_history.append(current_lt)

        # Mapeo robusto
        # El nombre debe obtenerse directamente por el método del cliente
        name = api.get_full_name()
        weight = user_data.get("weight")

        new_profile = AthleteProfile(
            name=name,
            weight_kg=float(weight / 1000) if weight else None,
            vo2_max_running=current_vo2,
            lactate_threshold_hr=current_lt["hr"] if isinstance(current_lt["hr"], int) else None,
            lactate_threshold_pace=lt_pace,
            acute_training_load=acute_load_dto.get("dailyTrainingLoadAcute"),
            training_status=status_label,
            upcoming_races=upcoming,
            training_plan=training_plan_data if training_plan_data else self.profile.training_plan,
            training_history=self.profile.training_history,
            health_history=health_history,
            personal_records=personal_records,
            race_predictions_history=race_history,
            training_status_history=status_history,
            vo2_max_history=vo2_history,
            lactate_threshold_history=lt_history
        )
        new_profile.save(str(self.memory_path))
        self.profile = new_profile
        return new_profile

    def get_realtime_metrics(self):
        api = self.session_manager.get_client()
        today = date.today().isoformat()
        
        # Obtener datos frescos
        readiness = api.get_training_readiness(today)
        ts = api.get_training_status(today)
        
        return {
            "readiness": readiness[0].get("score") if isinstance(readiness, list) else readiness.get("score"),
            "status": "Optimal" # Simplified for demo
        }

    def save_session_analysis(self, activity_id: int, analysis: dict):
        """Persiste el análisis técnico para no volver a consultar a Garmin."""
        new_session = {
            "activity_id": activity_id,
            "date": date.today().isoformat(),
            "km_splits": analysis
        }
        self.profile.training_history.append(new_session)
        self.profile.save(str(self.memory_path))
    
    def audit_training_week(self):
        """Auditoría profunda: extrae, analiza y guarda los splits detallados."""
        api = self.session_manager.get_client()
        activities = api.get_activities(0, 5) # Últimas 5
        
        report = "--- AUDITORÍA DETALLADA: DESGLOSE TÉCNICO ---\n"
        for act in activities:
            activity_id = act.get("activityId")
            name = act.get("activityName", "Sin nombre")
            report += f"\n\n=== {name} ==="
            
            # Garmin devuelve splits en splitSummaries, pero los datos técnicos
            # están dentro de cada objeto split.
            splits = act.get("splitSummaries", [])
            analysis = []
            if not splits:
                report += "\n  (No hay datos de splits detallados disponibles)"
                continue
                
            for i, split in enumerate(splits):
                dist_m = split.get("distance", 0)
                duration_min = split.get("duration", 0) / 60
                pace = (duration_min / (dist_m/1000)) if dist_m > 0 else 0
                
                # Datos técnicos
                hr = split.get("averageHR", "N/A")
                cadence = split.get("averageRunCadence", "N/A")
                power = split.get("averagePower", "N/A")
                split_type = split.get("splitType", "Desconocido")
                
                split_data = {
                    "split_type": split_type,
                    "dist_km": dist_m / 1000,
                    "pace_min_km": f"{int(pace)}:{int((pace%1)*60):02d}",
                    "hr": hr,
                    "cadence": cadence,
                    "power": power
                }
                analysis.append(split_data)
                
                report += f"\n  Segmento ({split_type}):"
                report += f" Ritmo: {split_data['pace_min_km']} min/km | FC: {hr} bpm | Cad: {cadence} spm | Pot: {power} W"
            
            # Guardamos el análisis
            self.save_session_analysis(activity_id, analysis)
        return report
