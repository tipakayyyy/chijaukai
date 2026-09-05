"""
app.py — CamAI Router & Login
"""

from datetime import datetime, timedelta
import os
import random
import streamlit as st

import views_limpieza as vl
import views_medico_enfermeria as vm
import views_paciente as vp
import views_triaje as vt
from data_gen import DIAGNOSTICOS, Paciente, generar_camas, generar_pacientes

# Configuración de página
st.set_page_config(
    page_title="CamAI · Command Center Clínico",
    layout="wide",
    page_icon="🏥",
    initial_sidebar_state="expanded",
)

# Estilos CSS
st.markdown(
    """
<style>
    .stApp { background-color: #F8FAFC; font-family: 'Segoe UI', system-ui, sans-serif; color: #1E293B; }
    .command-header { background-color: #034E51; color: #FFFFFF; padding: 18px 24px; border-radius: 8px; font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; }
    .kpi-container { display: flex; gap: 15px; margin-bottom: 22px; }
    .kpi-card { background-color: #99E6E6; border-radius: 12px; padding: 14px 20px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .kpi-label { font-size: 0.78rem; font-weight: 600; color: #034E51; text-transform: capitalize; display: flex; justify-content: space-between; }
    .kpi-value { font-size: 1.9rem; font-weight: 800; color: #03393C; margin-top: 4px; }
    .pabellon-bar { background-color: #034E51; padding: 8px 14px; border-radius: 6px; color: white; font-size: 0.85rem; font-weight: 600; margin-bottom: 16px; }
    .room-box { background: #E8F7F7; border: 1px solid #BCE5E5; border-radius: 12px; padding: 14px 16px; margin-bottom: 14px; }
    .room-header { font-size: 0.85rem; font-weight: 700; color: #08676B; letter-spacing: 0.5px; margin-bottom: 10px; }
    .active-banner { background-color: #CCFBF1; border-left: 5px solid #14B8A6; padding: 10px 14px; border-radius: 6px; color: #0F766E; font-weight: 700; margin-bottom: 12px; }
    .section-pill { background-color: #B2F5EA; color: #004D40; font-weight: 700; font-size: 0.95rem; padding: 8px 12px; border-radius: 6px; margin-top: 14px; margin-bottom: 8px; }
</style>
""",
    unsafe_allow_html=True,
)


def obtener_ruta_logo():
  rutas = [
      "assets/logo_camai.png",
      "assets/logo_camai.jpg",
      "assets/136218.jpg",
      "logo_camai.png",
      "136218.jpg",
  ]
  for r in rutas:
    if os.path.exists(r):
      return r
  return None


RUTA_LOGO = obtener_ruta_logo()

# Inicialización de Datos en Session State
PABELLONES = [
    "Pabellón A (Urgencias)",
    "Pabellón B (Medicina Interna / Cirugía)",
    "Pabellón C (Cuidados Críticos)",
]
NOMBRES = [
    "Carlos Mendoza",
    "Lucía Fernández",
    "Mateo Alarcón",
    "Valeria Gómez",
    "Esteban Ruiz",
]

if "inicializado" not in st.session_state:
  hora_actual = datetime(2026, 1, 1, 8, 0)
  camas = generar_camas(n_camas=24, ocupacion=0.75)
  pacientes = generar_pacientes(camas, hora_actual)

  for idx, c in enumerate(camas):
    c.pabellon = PABELLONES[idx // 8]

  for idx, p in enumerate(pacientes):
    p.nombre = NOMBRES[idx % len(NOMBRES)]
    p.edad = random.randint(28, 78)
    p.dni = f"7{random.randint(1000000, 9999999)}"
    p.examenes = [
        "PCR Cuantitativo: 24 mg/L",
        "Tomografía de Tórax: Infiltrados basales resueltos",
    ]
    p.medicamentos = ["Atorvastatina 20mg VO noche", "Ceftriaxona 1g c/12h EV"]
    p.signos_vitales = {
        "pa": "120/80",
        "fc": "78 bpm",
        "temp": "36.8 °C",
        "spo2": "97%",
    }
    p.estado_animo = "Lúcido y colaborador"
    p.hora_alta_prevista = hora_actual + timedelta(days=2)

  st.session_state.hora_actual = hora_actual
  st.session_state.camas = {c.id: c for c in camas}
  st.session_state.pacientes = {p.id: p for p in pacientes}
  st.session_state.cama_seleccionada = 6
  st.session_state.horas_recuperadas = 18.5
  st.session_state.pabellones = PABELLONES
  st.session_state.diagnosticos = DIAGNOSTICOS
  st.session_state.chat_history = []
  st.session_state.inicializado = True

if "auth_user" not in st.session_state:
  st.session_state.auth_user = None
if "auth_role" not in st.session_state:
  st.session_state.auth_role = None

# ---------------------------------------------------------------------------
# LOGIN VIEW (RENDER DIRECTO)
# ---------------------------------------------------------------------------
if not st.session_state.auth_user:
  st.markdown(
      "<h1 style='text-align:center; color:#034E51;'>🏥 CAMAI COMMAND"
      " CENTER</h1>",
      unsafe_allow_html=True,
  )

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    if RUTA_LOGO:
      st.image(RUTA_LOGO, use_container_width=True)

    st.markdown("### Acceso al Sistema")
    usuario = st.text_input("Usuario / Identificación", value="dra_mendoza")
    rol = st.selectbox("Ventana de Acceso:", [
        "Command Center (Médico / Enfermería)",
        "Módulo de Admisión & Triaje",
        "Operaciones de Limpieza",
        "Portal del Paciente",
    ])

    if st.button("Ingresar a Ventana", use_container_width=True, type="primary"):
      st.session_state.auth_user = usuario
      st.session_state.auth_role = rol
      st.rerun()

# ---------------------------------------------------------------------------
# RUTEO A VISTAS
# ---------------------------------------------------------------------------
else:
  with st.sidebar:
    if RUTA_LOGO:
      st.image(RUTA_LOGO, use_container_width=True)
    st.markdown(f"👤 **Usuario:** `{st.session_state.auth_user}`")
    st.markdown(f"💼 **Ventana:** `{st.session_state.auth_role}`")
    if st.button("Cerrar Sesión", use_container_width=True):
      st.session_state.auth_user = None
      st.session_state.auth_role = None
      st.rerun()

  if "Command Center" in st.session_state.auth_role:
    vm.render_vista()
  elif "Triaje" in st.session_state.auth_role:
    vt.render_vista()
  elif "Limpieza" in st.session_state.auth_role:
    vl.render_vista()
  elif "Paciente" in st.session_state.auth_role:
    vp.render_vista()