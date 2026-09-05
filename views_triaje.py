import streamlit as st
import requests
import json
import re
from datetime import datetime, timedelta
from data_gen import Paciente

MODELO_OPENROUTER = "inclusionai/ling-3.0-flash-sante:free"

def consultar_riesgo_openrouter(diagnostico, edad, complejidad, pa, fc, temp, spo2, animo):
    """
    Pide la evaluación de riesgo directamente al modelo de OpenRouter.
    """
    api_key = st.secrets.get("OPENROUTER_API_KEY", "")
    
    if not api_key:
        return calcular_riesgo_respaldo(diagnostico, edad, complejidad, pa, fc, temp, spo2, animo)

    prompt = f"""
    Eres un motor de triaje médico con inteligencia artificial.
    Evalúa la siguiente información del paciente:
    - Edad: {edad} años
    - Diagnóstico Presuntivo: {diagnostico}
    - Severidad Clínica: {complejidad}
    - Signos Vitales: PA {pa}, FC {fc} bpm, Temp {temp} °C, SpO2 {spo2}%
    - Estado de Conciencia/Ánimo: {animo}

    Basado en consensos de triaje hospitalario (MIMIC-IV / eICU / NEWS2):
    Estima el Porcentaje de Riesgo de Requiere Internación Hospitalaria.
    Responde ÚNICAMENTE con un número entero entre 5 y 98. No agregues texto adicional ni explicaciones.
    """

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://camai-app.com",
                "X-Title": "CamAI Hospital Engine"
            },
            data=json.dumps({
                "model": MODELO_OPENROUTER,
                "messages": [
                    {"role": "system", "content": "Eres un asistente médico de triaje preciso que solo responde con números enteros."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }),
            timeout=6
        )
        
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            match = re.search(r'\d+', content)
            if match:
                score = int(match.group())
                return min(max(score, 5), 98)
    except Exception:
        pass

    return calcular_riesgo_respaldo(diagnostico, edad, complejidad, pa, fc, temp, spo2, animo)


def calcular_riesgo_respaldo(diagnostico, edad, complejidad, pa_str, fc_str, temp_str, spo2_str, animo):
    score = 15
    diag_clean = str(diagnostico).lower()
    
    if any(p in diag_clean for p in ["sepsis", "infarto", "acv", "hemorragia", "paro", "shock", "tep"]):
        score += 35
    elif any(p in diag_clean for p in ["neumonía", "neumonia", "apendicitis", "fractura", "infección", "asma"]):
        score += 18

    if edad >= 75: score += 20
    elif edad >= 60: score += 15
    elif edad >= 45: score += 8

    comp_map = {"baja": 5, "media": 20, "alta": 35}
    score += comp_map.get(str(complejidad).lower(), 15)

    try:
        val_spo2 = float(str(spo2_str).replace('%', '').strip())
        if val_spo2 < 90: score += 25
        elif val_spo2 < 95: score += 12
    except ValueError:
        pass

    if "Soporoso" in animo or "Decaído" in animo: score += 15
    elif "dolor" in animo.lower() or "ansioso" in animo.lower(): score += 8

    return min(max(score, 5), 98)


def render_vista():
    st.markdown("<div class='command-header'>📥 Módulo de Admisión & Triaje Inteligente (OpenRouter Ling 3.0)</div>", unsafe_allow_html=True)
    col_form, col_list = st.columns([1.2, 1])

    with col_form:
        st.markdown("### 👤 Evaluar Paciente")
        with st.form("form_triaje"):
            f_dni = st.text_input("DNI", value="75849302")
            f_nombre = st.text_input("Nombre Completo", value="María Elena Rojas")
            f_edad = st.number_input("Edad", min_value=0, max_value=110, value=54)
            f_diag = st.text_input("Diagnóstico Presuntivo", value="Neumonía adquirida en la comunidad")
            f_complejidad = st.selectbox("Severidad Clínica", ["baja", "media", "alta"])
            
            st.markdown("#### 🩺 Signos Vitales y Estado")
            c1, c2, c3, c4 = st.columns(4)
            f_pa = c1.text_input("PA", "120/80")
            f_fc = c2.text_input("FC", "78")
            f_temp = c3.text_input("Temp", "36.8")
            f_spo2 = c4.text_input("SpO2", "97")

            f_animo = st.selectbox("Estado de Ánimo / Conciencia", [
                "Lúcido y colaborador / Tranquilo", "Ansioso / Con dolor", "Decaído / Soporoso"
            ])

            if st.form_submit_button("🧠 Calcular Probabilidad de Internación", use_container_width=True):
                with st.spinner("Consultando modelo IA via OpenRouter..."):
                    score = consultar_riesgo_openrouter(
                        diagnostico=f_diag,
                        edad=f_edad,
                        complejidad=f_complejidad,
                        pa=f_pa,
                        fc=f_fc,
                        temp=f_temp,
                        spo2=f_spo2,
                        animo=f_animo
                    )
                
                los_map = {"baja": 3.0, "media": 5.0, "alta": 7.0}
                f_los_base = los_map.get(f_complejidad, 5.0)

                nuevo_p = Paciente(
                    id=len(st.session_state.pacientes) + 101,
                    diagnostico=f_diag.strip(),
                    complejidad=f_complejidad,
                    los_base_dias=f_los_base,
                    hora_ingreso=datetime.now()
                )
                
                nuevo_p.nombre, nuevo_p.edad, nuevo_p.dni = f_nombre, f_edad, f_dni
                nuevo_p.signos_vitales = {"pa": f_pa, "fc": f"{f_fc} bpm", "temp": f"{f_temp} °C", "spo2": f"{f_spo2}%"}
                nuevo_p.estado_animo = f_animo
                nuevo_p.probabilidad_internar = score
                nuevo_p.examenes, nuevo_p.medicamentos = ["En evaluación"], ["Suero Fisiológico 0.9%"]
                nuevo_p.hora_alta_prevista = datetime.now() + timedelta(days=int(f_los_base))

                st.session_state.pacientes[nuevo_p.id] = nuevo_p
                st.success(f"✅ Evaluación Completa (IA Ling 3.0). Probabilidad de Requiere Cama: **{score}%**")
                st.rerun()

    with col_list:
        st.markdown("### 📊 Pacientes Recientes en Triaje")
        for p in list(st.session_state.pacientes.values())[-4:]:
            diag_text = p.diagnostico[0] if isinstance(p.diagnostico, (tuple, list)) else p.diagnostico
            prob = getattr(p, 'probabilidad_internar', 50)
            v = getattr(p, 'signos_vitales', {'pa':'120/80', 'fc':'78 bpm', 'temp':'36.8 °C', 'spo2':'97%'})
            
            st.markdown(f"""
            <div class='room-box'>
                <b>{p.nombre}</b> (DNI: {getattr(p, 'dni', 'S/D')})<br>
                <small>Diagnóstico: {diag_text} | Ánimo: {getattr(p, 'estado_animo', 'Estable')}</small><br>
                <small><b>SV:</b> PA {v['pa']} | FC {v['fc']} | SpO2 {v['spo2']}</small><br>
                <div style='margin-top:5px; font-weight:bold; color:#034E51;'>Riesgo Internación: {prob}%</div>
            </div>
            """, unsafe_allow_html=True)