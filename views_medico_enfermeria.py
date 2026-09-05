"""
views_medico_enfermeria.py — Vista Command Center Clínico
Plano 2D vectorial (SVG) de habitaciones con múltiples camas realistas,
selección funcional de camas y resaltado verde agua para la cama activa.
"""

from datetime import datetime, timedelta
import streamlit as st
import streamlit.components.v1 as components
import time
import re

LATENCIA_BASELINE_H = 4.0
LATENCIA_CAMAI_H = 1.5

# Paleta de estados (misma convención que la leyenda del plano)
COLOR_LIBRE = "#22C55E"          # verde  -> libre y limpia
COLOR_OCUPADA = "#EF4444"        # rojo   -> ocupada
COLOR_LIMPIEZA = "#F59E0B"       # amarillo -> pendiente de desinfección
COLOR_SELECCIONADA = "#80E2D8"   # verde agua -> cama seleccionada
STROKE_SELECCIONADA = "#0F766E"
STROKE_OCUPADA = "#B91C1C"
STROKE_LIMPIEZA = "#B45309"
STROKE_LIBRE = "#15803D"
STROKE_DEFAULT = "#94A3B8"


# ---------------------------------------------------------------------------
# HELPERS DE FORMATO Y ESTADO
# ---------------------------------------------------------------------------
def _formatear_codigo(cama_id, prefijo="C"):
    if isinstance(cama_id, int):
        return f"{prefijo}-{cama_id:03d}"
    return f"{prefijo}-{str(cama_id).zfill(3)}"


def _color_estado(cama, activa=False):
    """Devuelve (fill, stroke) según el estado real de la cama, salvo que esté
    activa/seleccionada, en cuyo caso siempre prevalece el verde agua."""
    if activa:
        return COLOR_SELECCIONADA, STROKE_SELECCIONADA
    if cama.ocupada:
        return COLOR_OCUPADA, STROKE_OCUPADA
    if cama.necesita_limpieza:
        return COLOR_LIMPIEZA, STROKE_LIMPIEZA
    return COLOR_LIBRE, STROKE_LIBRE


def _calcular_layout(n_camas, bed_w=130, bed_h=62, gap_x=30, gap_y=26, margin=(30, 45)):
    """Calcula ancho/alto del plano y la posición (x, y) de cada cama, en
    cuadrícula de 1 o 2 columnas según la cantidad de camas."""
    columnas = 1 if n_camas <= 1 else 2
    filas = (n_camas + columnas - 1) // columnas
    margin_left, margin_top = margin
    extra_ancho = 30 if columnas > 1 else 0

    width = margin_left * 2 + columnas * bed_w + (columnas - 1) * gap_x + extra_ancho
    height = margin_top + filas * bed_h + (filas - 1) * gap_y + 90

    posiciones = []
    for idx in range(n_camas):
        fila = idx // columnas
        col = idx % columnas
        x = margin_left + bed_w / 2 + col * (bed_w + gap_x)
        y = margin_top + bed_h / 2 + fila * (bed_h + gap_y)
        posiciones.append({"x": x, "y": y})

    return width, height, posiciones


def _svg_cama(pos, c_code, fill_sabana, stroke_cama, stroke_width, glow=False, escala=1.0):
    """Dibuja una cama realista (cabecera, colchón, sábana, embozo, almohadas y
    etiqueta de código) en la posición indicada."""
    sombra = (
        'filter="drop-shadow(0px 0px 8px rgba(20, 184, 166, 0.8))"' if glow else ""
    )
    fs_code = max(7, int(9 * escala))
    return f"""
    <g transform="translate({pos['x']}, {pos['y']}) scale({escala})" {sombra}>
        <rect x="-58" y="-32" width="10" height="64" rx="2" fill="#8D5B4C" stroke="#5C3A2E" stroke-width="1"/>
        <rect x="-48" y="-31" width="96" height="62" rx="4" fill="#F8FAFC" stroke="{stroke_cama}" stroke-width="{stroke_width}"/>
        <rect x="-30" y="-27" width="74" height="54" rx="2" fill="{fill_sabana}" stroke="{stroke_cama}" stroke-width="1"/>
        <rect x="-30" y="-27" width="12" height="54" fill="#E2E8F0" opacity="0.6"/>
        <line x1="-18" y1="-27" x2="-18" y2="27" stroke="{stroke_cama}" stroke-width="1" stroke-dasharray="2,2"/>
        <rect x="-44" y="-22" width="16" height="20" rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
        <rect x="-44" y="2" width="16" height="20" rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>
        <rect x="6" y="-9" width="48" height="18" rx="4" fill="#FFFFFF" stroke="{stroke_cama}" stroke-width="1" opacity="0.95"/>
        <text x="30" y="4" font-size="{fs_code}" font-weight="bold" fill="{stroke_cama}" text-anchor="middle" font-family="system-ui">{c_code}</text>
    </g>
    """


# ---------------------------------------------------------------------------
# PLANO DETALLADO (habitación seleccionada)
# ---------------------------------------------------------------------------
def render_habitacion_completa_svg(camas_hab, cama_activa_id):
    """Dibuja la habitación completa con múltiples camas realistas en vista
    superior, orientadas de forma horizontal, dentro de un plano arquitectónico."""
    n_camas = len(camas_hab)
    width, height, posiciones = _calcular_layout(n_camas)

    svg_camas_html = ""
    for i, c in enumerate(camas_hab):
        if i >= len(posiciones):
            break
        pos = posiciones[i]
        es_activa = c.id == cama_activa_id
        c_code = _formatear_codigo(c.id)
        fill_sabana = COLOR_SELECCIONADA if es_activa else "#FFFFFF"
        stroke_cama = STROKE_SELECCIONADA if es_activa else STROKE_DEFAULT
        stroke_width = "3" if es_activa else "1.5"
        svg_camas_html += _svg_cama(
            pos, c_code, fill_sabana, stroke_cama, stroke_width, glow=es_activa
        )

    svg_raw = f"""
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="background:#FFFFFF; border:2px solid #334155; border-radius:12px;">
        <rect x="8" y="8" width="{width-16}" height="{height-16}" fill="#F1F5F9" stroke="#334155" stroke-width="4" rx="6"/>
        <rect x="{width*0.34:.1f}" y="4" width="{width*0.32:.1f}" height="8" fill="#BFDBFE" stroke="#1D4ED8" stroke-width="1.5"/>
        <line x1="{width*0.5:.1f}" y1="4" x2="{width*0.5:.1f}" y2="12" stroke="#1D4ED8" stroke-width="1"/>
        <g transform="translate(26, 24)">
            <rect x="0" y="0" width="24" height="18" rx="4" fill="#E2E8F0" stroke="#64748B" stroke-width="1.2"/>
            <rect x="0" y="0" width="24" height="5" rx="2" fill="#CBD5E1"/>
            <rect x="28" y="0" width="24" height="18" rx="4" fill="#E2E8F0" stroke="#64748B" stroke-width="1.2"/>
            <rect x="28" y="0" width="24" height="5" rx="2" fill="#CBD5E1"/>
        </g>
        <circle cx="{width-32}" cy="22" r="9" fill="none" stroke="#64748B" stroke-width="1.5"/>
        <line x1="{width-41}" y1="22" x2="{width-23}" y2="22" stroke="#64748B" stroke-width="1"/>
        <line x1="{width-32}" y1="13" x2="{width-32}" y2="31" stroke="#64748B" stroke-width="1"/>
        <rect x="{width-70}" y="{height-70}" width="60" height="60" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
        <rect x="{width-64}" y="{height-64}" width="18" height="12" rx="2" fill="#FFFFFF" stroke="#64748B" stroke-width="1.2"/>
        <circle cx="{width-40}" cy="{height-38}" r="12" fill="#FFFFFF" stroke="#64748B" stroke-width="1.5"/>
        <line x1="20" y1="{height-8}" x2="60" y2="{height-8}" stroke="#FFFFFF" stroke-width="6"/>
        <path d="M 20 {height-8} A 40 40 0 0 1 60 {height-48}" fill="none" stroke="#94A3B8" stroke-width="2" stroke-dasharray="3,3"/>
        {svg_camas_html}
    </svg>
    """

    svg_final = "".join(linea.strip() for linea in svg_raw.splitlines() if linea.strip())
    return svg_final, height


# ---------------------------------------------------------------------------
# MINI-PLANO VECTORIAL (vista general)
# ---------------------------------------------------------------------------
def render_mini_plano_habitacion(camas_hab, cama_activa_id):
    n_camas = len(camas_hab)
    width, height, posiciones = _calcular_layout(
        n_camas, bed_w=92, bed_h=46, gap_x=16, gap_y=14, margin=(18, 22)
    )

    svg_camas_html = ""
    for i, c in enumerate(camas_hab):
        if i >= len(posiciones):
            break
        pos = posiciones[i]
        es_activa = c.id == cama_activa_id
        c_code = _formatear_codigo(c.id)
        fill_cama, stroke_cama = _color_estado(c, activa=es_activa)
        stroke_width = "2.5" if es_activa else "1.3"
        svg_camas_html += _svg_cama(
            pos, c_code, fill_cama, stroke_cama, stroke_width, glow=es_activa, escala=0.72
        )

    svg_raw = f"""
    <svg width="100%" height="{height}" viewBox="0 0 {width} {height}" style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:10px;">
        <rect x="4" y="4" width="{width-8}" height="{height-8}" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="2" rx="6"/>
        <rect x="{width*0.36:.1f}" y="1" width="{width*0.28:.1f}" height="5" fill="#BFDBFE" stroke="#1D4ED8" stroke-width="1"/>
        <line x1="10" y1="{height-4}" x2="28" y2="{height-4}" stroke="#F8FAFC" stroke-width="4"/>
        <path d="M 10 {height-4} A 18 18 0 0 1 28 {height-22}" fill="none" stroke="#CBD5E1" stroke-width="1.3" stroke-dasharray="2,2"/>
        {svg_camas_html}
    </svg>
    """
    svg_final = "".join(l.strip() for l in svg_raw.splitlines() if l.strip())
    return svg_final, height


LEYENDA_HTML = """
<div class='plano-leyenda'>
    <span><i style="background:#22C55E"></i> Libre y limpia</span>
    <span><i style="background:#EF4444"></i> Ocupada</span>
    <span><i style="background:#F59E0B"></i> Pend. desinfección</span>
    <span><i style="background:#80E2D8"></i> Seleccionada</span>
</div>
<style>
.plano-leyenda{display:flex; gap:14px; flex-wrap:wrap; font-size:12px; color:#334155; margin:2px 0 10px 0;}
.plano-leyenda span{display:flex; align-items:center; gap:5px;}
.plano-leyenda i{width:10px; height:10px; border-radius:3px; display:inline-block;}
</style>
"""


# ============================================================
# FUNCIONES DE REGISTRO DIARIO DEL PACIENTE
# ============================================================
def inicializar_registro_diario(paciente_id):
    """Inicializa el registro diario del paciente si no existe"""
    if "registros_diarios" not in st.session_state:
        st.session_state.registros_diarios = {}
    
    if paciente_id not in st.session_state.registros_diarios:
        st.session_state.registros_diarios[paciente_id] = {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "desayuno": "N/A",
            "almuerzo": "N/A",
            "cena": "N/A",
            "evolucion": "N/A",
            "observaciones": "",
            "registros_previos": []
        }


def guardar_registro_diario(paciente_id, desayuno, almuerzo, cena, evolucion, observaciones):
    """Guarda el registro diario del paciente"""
    inicializar_registro_diario(paciente_id)
    
    # Crear registro actual
    registro_actual = {
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "desayuno": desayuno,
        "almuerzo": almuerzo,
        "cena": cena,
        "evolucion": evolucion,
        "observaciones": observaciones
    }
    
    # Agregar al historial
    st.session_state.registros_diarios[paciente_id]["registros_previos"].append(registro_actual)
    
    # Actualizar valores actuales
    st.session_state.registros_diarios[paciente_id]["desayuno"] = desayuno
    st.session_state.registros_diarios[paciente_id]["almuerzo"] = almuerzo
    st.session_state.registros_diarios[paciente_id]["cena"] = cena
    st.session_state.registros_diarios[paciente_id]["evolucion"] = evolucion
    st.session_state.registros_diarios[paciente_id]["observaciones"] = observaciones
    st.session_state.registros_diarios[paciente_id]["fecha"] = datetime.now().strftime("%d/%m/%Y")
    
    return True


def render_registro_paciente(paciente):
    """Renderiza el formulario de registro diario del paciente"""
    paciente_id = paciente.id
    inicializar_registro_diario(paciente_id)
    
    registros = st.session_state.registros_diarios[paciente_id]
    
    st.markdown("### 📋 Registro Diario del Paciente")
    st.caption(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Mostrar mensaje de éxito si se guardó
    if st.session_state.get(f"registro_guardado_{paciente_id}", False):
        st.success("✅ Registro guardado exitosamente")
        st.balloons()
        # Limpiar el flag después de mostrarlo
        st.session_state[f"registro_guardado_{paciente_id}"] = False
    
    # Formulario para el registro
    with st.form(key=f"registro_diario_form_{paciente_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Desayuno
            desayuno_opciones = ["Completo", "Parcial", "No consumió", "N/A"]
            desayuno_val = registros.get("desayuno", "N/A")
            desayuno_idx = desayuno_opciones.index(desayuno_val) if desayuno_val in desayuno_opciones else 3
            
            desayuno = st.selectbox(
                "🍳 Desayuno",
                options=desayuno_opciones,
                index=desayuno_idx,
                key=f"desayuno_{paciente_id}"
            )
            
            # Almuerzo
            almuerzo_opciones = ["Completo", "Parcial", "No consumió", "N/A"]
            almuerzo_val = registros.get("almuerzo", "N/A")
            almuerzo_idx = almuerzo_opciones.index(almuerzo_val) if almuerzo_val in almuerzo_opciones else 3
            
            almuerzo = st.selectbox(
                "🍝 Almuerzo",
                options=almuerzo_opciones,
                index=almuerzo_idx,
                key=f"almuerzo_{paciente_id}"
            )
        
        with col2:
            # Cena
            cena_opciones = ["Completo", "Parcial", "No consumió", "N/A"]
            cena_val = registros.get("cena", "N/A")
            cena_idx = cena_opciones.index(cena_val) if cena_val in cena_opciones else 3
            
            cena = st.selectbox(
                "🍽️ Cena",
                options=cena_opciones,
                index=cena_idx,
                key=f"cena_{paciente_id}"
            )
            
            # Evolución
            evolucion_opciones = ["Estable", "Mejorando", "Deterioro leve", "Deterioro significativo", "N/A"]
            evolucion_val = registros.get("evolucion", "N/A")
            evolucion_idx = evolucion_opciones.index(evolucion_val) if evolucion_val in evolucion_opciones else 4
            
            evolucion = st.selectbox(
                "📈 Evolución del día",
                options=evolucion_opciones,
                index=evolucion_idx,
                key=f"evolucion_{paciente_id}"
            )
        
        observaciones = st.text_area(
            "📝 Observaciones adicionales",
            value=registros.get("observaciones", ""),
            placeholder="Ej: Dolor leve, fiebre controlada, etc.",
            key=f"obs_{paciente_id}"
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Guardar Registro", type="primary", use_container_width=True)
        
        with col_btn2:
            ver_historial = st.form_submit_button("📋 Ver Historial", use_container_width=True)
    
    # Procesar fuera del formulario
    if submitted:
        if guardar_registro_diario(paciente_id, desayuno, almuerzo, cena, evolucion, observaciones):
            st.session_state[f"registro_guardado_{paciente_id}"] = True
            st.rerun()
    
    if ver_historial:
        st.session_state[f"ver_historial_{paciente_id}"] = not st.session_state.get(f"ver_historial_{paciente_id}", False)
        st.rerun()
    
    # Mostrar historial si se solicitó
    if st.session_state.get(f"ver_historial_{paciente_id}", False):
        with st.expander("📜 Historial de Registros", expanded=True):
            if registros["registros_previos"]:
                # Mostrar los registros más recientes primero
                for reg in reversed(registros["registros_previos"][-10:]):
                    st.markdown(f"""
                    **📅 {reg['fecha']}**
                    - 🍳 Desayuno: {reg['desayuno']}
                    - 🍝 Almuerzo: {reg['almuerzo']}
                    - 🍽️ Cena: {reg['cena']}
                    - 📈 Evolución: {reg['evolucion']}
                    - 📝 Observaciones: {reg['observaciones'] if reg['observaciones'] else 'Ninguna'}
                    ---
                    """)
                
                # Mostrar total de registros
                st.caption(f"📊 Total de registros: {len(registros['registros_previos'])}")
            else:
                st.info("📭 No hay registros previos")


# ============================================================
# FUNCIONES DE GESTIÓN DE DOCUMENTOS
# ============================================================
def render_gestion_documentos(paciente):
    """Renderiza la sección de gestión de documentos del paciente"""
    paciente_id = paciente.id
    
    if "documentos_paciente" not in st.session_state:
        st.session_state.documentos_paciente = {}
    
    if paciente_id not in st.session_state.documentos_paciente:
        st.session_state.documentos_paciente[paciente_id] = []
    
    st.markdown("### 📄 Documentos y Exámenes")
    
    # Subir nuevo documento
    with st.expander("📤 Subir Nuevo Documento", expanded=False):
        with st.form(key=f"subir_doc_{paciente_id}"):
            tipo_doc = st.selectbox(
                "Tipo de documento",
                options=["Examen de laboratorio", "Radiografía", "Tomografía", "Resonancia", "Otro"]
            )
            
            descripcion = st.text_input("Descripción del documento")
            
            archivo = st.file_uploader(
                "Seleccionar archivo (PDF, JPG, PNG)",
                type=["pdf", "jpg", "jpeg", "png"]
            )
            
            if st.form_submit_button("📤 Subir Documento", type="primary", use_container_width=True):
                if archivo and descripcion:
                    # Guardar referencia del documento
                    nuevo_doc = {
                        "tipo": tipo_doc,
                        "descripcion": descripcion,
                        "nombre_archivo": archivo.name,
                        "fecha_subida": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "contenido": archivo.read()
                    }
                    st.session_state.documentos_paciente[paciente_id].append(nuevo_doc)
                    st.success(f"✅ Documento '{descripcion}' subido exitosamente")
                    st.rerun()
                else:
                    st.warning("⚠️ Por favor complete todos los campos")
    
    # Listar documentos existentes
    if st.session_state.documentos_paciente[paciente_id]:
        st.markdown("**Documentos disponibles:**")
        for i, doc in enumerate(st.session_state.documentos_paciente[paciente_id]):
            col_doc1, col_doc2 = st.columns([4, 1])
            with col_doc1:
                st.info(f"""
                📄 **{doc['descripcion']}**
                - Tipo: {doc['tipo']}
                - Archivo: {doc['nombre_archivo']}
                - Subido: {doc['fecha_subida']}
                """)
            with col_doc2:
                if st.button(f"🗑️ Eliminar", key=f"del_doc_{paciente_id}_{i}", use_container_width=True):
                    st.session_state.documentos_paciente[paciente_id].pop(i)
                    st.rerun()
    else:
        st.info("No hay documentos subidos aún")


# ============================================================
# FUNCIONES DE PREDICCIÓN DE ALTA CON IA
# ============================================================
def obtener_ultimos_registros(paciente_id):
    """Obtiene los últimos registros diarios del paciente como texto"""
    if "registros_diarios" not in st.session_state:
        return "Sin registros"
    
    if paciente_id not in st.session_state.registros_diarios:
        return "Sin registros"
    
    registros = st.session_state.registros_diarios[paciente_id]
    if not registros["registros_previos"]:
        return "Sin registros"
    
    # Obtener los últimos 3 registros
    ultimos = registros["registros_previos"][-3:]
    texto = ""
    for reg in ultimos:
        texto += f"- {reg['fecha']}: Desayuno={reg['desayuno']}, Almuerzo={reg['almuerzo']}, "
        texto += f"Cena={reg['cena']}, Evolución={reg['evolucion']}, Observaciones={reg['observaciones']}\n"
    
    return texto


def predecir_alta_con_ia(paciente):
    """Usa IA para predecir la fecha de alta del paciente basada en sus datos"""
    
    # Verificar que tengamos la API key
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return None, "⚠️ No se encontró OPENROUTER_API_KEY en secrets.toml"
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key.strip(),
        )
        
        # Obtener signos vitales
        signos = getattr(paciente, 'signos_vitales', {})
        if not signos:
            signos = {"pa": "120/80", "fc": "78 bpm", "temp": "36.8 °C", "spo2": "97%"}
        
        # Obtener exámenes
        examenes = getattr(paciente, 'examenes', ['Hemograma: 11,200 /mm³', 'PCR: 24 mg/L'])
        if not examenes:
            examenes = ['Sin exámenes registrados']
        
        # Obtener medicamentos
        medicamentos = getattr(paciente, 'medicamentos', ['Ceftriaxona 1g EV c/12h', 'Paracetamol 500mg VO'])
        if not medicamentos:
            medicamentos = ['Sin medicamentos registrados']
        
        # Obtener registros diarios
        registros_texto = obtener_ultimos_registros(paciente.id)
        
        # Calcular días de hospitalización
        dias_hosp = 1
        if hasattr(paciente, 'hora_ingreso') and paciente.hora_ingreso:
            dias_hosp = (datetime.now() - paciente.hora_ingreso).days
            if dias_hosp < 1:
                dias_hosp = 1
        
        # Construir el prompt con los datos del paciente
        prompt = f"""
        Eres un asistente médico especializado en predicción de altas hospitalarias.
        Basado en los siguientes datos del paciente, estima en cuántos días podría ser dado de alta.

        DATOS DEL PACIENTE:
        - Nombre: {paciente.nombre}
        - Edad: {paciente.edad} años
        - Diagnóstico: {getattr(paciente, 'diagnostico', 'Neumonía')}
        - Días de hospitalización: {dias_hosp}
        - Complejidad: {getattr(paciente, 'complejidad', 'media')}
        
        SIGNOS VITALES:
        - Presión Arterial: {signos.get('pa', '120/80')}
        - Frecuencia Cardíaca: {signos.get('fc', '78 bpm')}
        - Temperatura: {signos.get('temp', '36.8 °C')}
        - Saturación O2: {signos.get('spo2', '97%')}
        
        EXÁMENES:
        {chr(10).join(['- ' + ex for ex in examenes])}
        
        MEDICAMENTOS:
        {chr(10).join(['- ' + med for med in medicamentos])}

        REGISTROS DIARIOS RECIENTES:
        {registros_texto if registros_texto != "Sin registros" else '- Sin registros diarios'}

        INSTRUCCIONES:
        1. Analiza todos los datos proporcionados
        2. Estima en cuántos DÍAS podría ser dado de alta el paciente
        3. Considera factores como: gravedad del diagnóstico, evolución, edad, signos vitales
        4. Da un rango de días (ej: "3-5 días") y una explicación breve
        5. Responde en español, con formato claro

        RESPUESTA (formato exacto):
        DÍAS ESTIMADOS: [número de días o rango]
        EXPLICACIÓN: [tu análisis breve]
        RECOMENDACIONES: [recomendaciones para acelerar el alta]
        """
        
        response = client.chat.completions.create(
            model="inclusionai/ling-3.0-flash-sante:free",
            messages=[
                {"role": "system", "content": "Eres un médico especialista en gestión hospitalaria. Proporciona predicciones precisas y útiles."},
                {"role": "user", "content": prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "CamAI"
            },
            timeout=30
        )
        
        if response.choices:
            prediccion = response.choices[0].message.content
            
            # Extraer días estimados del texto
            dias_match = re.search(r'DÍAS ESTIMADOS:\s*([0-9\-]+)', prediccion)
            if dias_match:
                dias_texto = dias_match.group(1)
                # Calcular fecha estimada
                if '-' in dias_texto:
                    # Rango: tomar el promedio
                    partes = dias_texto.split('-')
                    try:
                        dias = (int(partes[0].strip()) + int(partes[1].strip())) // 2
                    except:
                        dias = int(partes[0].strip())
                else:
                    try:
                        dias = int(dias_texto.strip())
                    except:
                        dias = 3
                
                fecha_estimada = datetime.now() + timedelta(days=dias)
                return fecha_estimada, prediccion
            else:
                # Si no encuentra el formato, devuelve la predicción completa
                return None, prediccion
        
        return None, "No se pudo obtener una respuesta de la IA"
        
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            return None, "⚠️ Error de autenticación con OpenRouter. Verifica tu API key."
        elif "402" in error_msg:
            return None, "⚠️ Sin créditos en OpenRouter. Revisa tu saldo."
        else:
            return None, f"⚠️ Error: {error_msg}"


# ============================================================
# FUNCIÓN PARA AGREGAR A COLA DE LIMPIEZA
# ============================================================
def agregar_a_cola_limpieza(cama_id, pabellon):
    """Agrega una cama a la cola de limpieza (integración con views_limpieza.py)"""
    if "cola_limpieza" not in st.session_state:
        st.session_state.cola_limpieza = []
    
    # Verificar si ya está en cola
    if not any(item["cama_id"] == cama_id and item["estado"] == "pendiente" 
               for item in st.session_state.cola_limpieza):
        st.session_state.cola_limpieza.append({
            "cama_id": cama_id,
            "pabellon": pabellon,
            "hora_retiro": datetime.now().strftime("%H:%M"),
            "estado": "pendiente",
            "tiempo_estimado": None,
            "hora_disponible": None
        })
        return True
    return False


# ============================================================
# VISTA PRINCIPAL
# ============================================================
def render_vista():
    # CSS para los estilos
    st.markdown("""
    <style>
    .kpi-container {
        display: flex;
        gap: 20px;
        background: #f8fafc;
        padding: 15px 20px;
        border-radius: 10px;
        margin: 10px 0 20px 0;
        border: 1px solid #e2e8f0;
    }
    .kpi-card {
        flex: 1;
        text-align: center;
        padding: 5px;
    }
    .kpi-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin: 2px 0;
    }
    .kpi-sub {
        font-size: 14px;
        color: #64748b;
    }
    .pabellon-bar {
        background: #f1f5f9;
        padding: 8px 15px;
        border-radius: 8px;
        margin: 10px 0 15px 0;
        font-weight: 600;
        color: #1e293b;
        border-left: 4px solid #3b82f6;
    }
    .room-box {
        background: white;
        border-radius: 10px;
        padding: 12px 15px;
        margin: 8px 0;
        border: 1px solid #e2e8f0;
    }
    .room-header {
        font-weight: 600;
        color: #1e293b;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 10px;
    }
    .plano-leyenda {
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        font-size: 12px;
        color: #334155;
        margin: 2px 0 10px 0;
    }
    .plano-leyenda span {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .plano-leyenda i {
        width: 10px;
        height: 10px;
        border-radius: 3px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # HEADER CON TÍTULO
    # ============================================================
    st.markdown(
        "<div class='command-header'>🏥 CAMAI — Command Center Clínico</div>",
        unsafe_allow_html=True,
    )

    # ============================================================
    # KPIs
    # ============================================================
    ocupadas = sum(1 for c in st.session_state.camas.values() if c.ocupada)
    limpieza = sum(1 for c in st.session_state.camas.values() if c.necesita_limpieza)
    libres = len(st.session_state.camas) - ocupadas - limpieza
    en_cola = len([i for i in st.session_state.cola_limpieza if i["estado"] == "pendiente"]) if "cola_limpieza" in st.session_state else 0

    st.markdown(
        f"""
    <div class='kpi-container'>
        <div class='kpi-card'>
            <div class='kpi-label'>Camas Ocupadas</div>
            <div class='kpi-value'>{ocupadas}</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Camas Libres</div>
            <div class='kpi-value'>{libres}</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Habitaciones en Limpieza</div>
            <div class='kpi-value'>{limpieza}</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-label'>Horas-Cama Ganadas</div>
            <div class='kpi-value'>{st.session_state.horas_recuperadas:.1f}</div>
            <div class='kpi-sub'>h</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # BARRA DE SIMULACIÓN Y FECHA
    # ============================================================
    col_sim, col_fecha = st.columns([2, 1])
    with col_sim:
        st.markdown("""
        <div style='display:flex; gap:10px; align-items:center; background:#f1f5f9; padding:8px 15px; border-radius:8px;'>
            <span style='font-weight:600;'>⚡ Simulación Swarm Engine</span>
            <span style='background:#3b82f6; color:white; padding:2px 12px; border-radius:12px; font-size:12px;'>Simulator +1 Hora</span>
        </div>
        """, unsafe_allow_html=True)
    with col_fecha:
        st.markdown(f"""
        <div style='text-align:right; background:#f1f5f9; padding:8px 15px; border-radius:8px; font-weight:500;'>
            📅 Fecha y Hora: {datetime.now().strftime('%d/%m/%Y - %H:%M')}
        </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # SELECTOR DE PABELLÓN
    # ============================================================
    tab_pab = st.radio(
        "Seleccione Pabellón:",
        st.session_state.pabellones,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown(f"<div class='pabellon-bar'>📍 {tab_pab}</div>", unsafe_allow_html=True)

    # ============================================================
    # LAYOUT PRINCIPAL: MAPA IZQUIERDA | DETALLES DERECHA
    # ============================================================
    col_mapa, col_detalles = st.columns([1.6, 1.4])
    
    camas_pab = [c for c in st.session_state.camas.values() if c.pabellon == tab_pab]

    # ---------------------------------------------------------------------------
    # COLUMNA IZQUIERDA: MAPA DE CAMAS
    # ---------------------------------------------------------------------------
    with col_mapa:
        st.markdown(f"#### 🗺️ Plano de Camas — {tab_pab}")
        st.markdown(LEYENDA_HTML, unsafe_allow_html=True)

        # Distribución de habitaciones
        distribucion_habitaciones = [
            {"nombre": "HABITACIÓN 101 (Privada - 1 Cama)", "capacidad": 1},
            {"nombre": "HABITACIÓN 102 (Doble - 2 Camas)", "capacidad": 2},
            {"nombre": "HABITACIÓN 103 (Cuádruple - 4 Camas)", "capacidad": 4},
            {"nombre": "HABITACIÓN 104 (Múltiple - 6 Camas)", "capacidad": 6},
        ]

        cursor_camas = 0

        for hab in distribucion_habitaciones:
            if cursor_camas >= len(camas_pab):
                break
            cap = hab["capacidad"]
            camas_chunk = camas_pab[cursor_camas : cursor_camas + cap]
            cursor_camas += cap

            if not camas_chunk:
                continue

            # Mostrar habitación
            st.markdown(
                f"<div class='room-box'><div class='room-header'>🏥 {hab['nombre']}</div>",
                unsafe_allow_html=True,
            )

            # Plano vectorial (SVG) real de la habitación
            svg_mini, alto_mini = render_mini_plano_habitacion(
                camas_chunk, st.session_state.cama_seleccionada
            )
            components.html(svg_mini, height=alto_mini + 10, scrolling=False)

            # Selector funcional: botones por cama
            cols_count = min(len(camas_chunk), 4)
            btn_cols = st.columns(cols_count)

            for i, cama in enumerate(camas_chunk):
                with btn_cols[i % cols_count]:
                    cama_code = _formatear_codigo(cama.id, prefijo="C-C")
                    es_activa = cama.id == st.session_state.cama_seleccionada

                    icono = "🔴" if cama.ocupada else "🟡" if cama.necesita_limpieza else "🟢"
                    btn_label = f"✨ {cama_code}" if es_activa else f"{icono} {cama_code}"

                    if st.button(btn_label, key=f"btn_{cama.id}", use_container_width=True):
                        st.session_state.cama_seleccionada = cama.id
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------------
    # COLUMNA DERECHA: DETALLES DEL PACIENTE / CAMA
    # ---------------------------------------------------------------------------
    with col_detalles:
        cid = st.session_state.cama_seleccionada
        cama_activa = st.session_state.camas.get(cid) if cid else None
        
        if cama_activa and cama_activa.ocupada and cama_activa.paciente_id:
            paciente = st.session_state.pacientes.get(cama_activa.paciente_id)
            
            if paciente:
                # Banner de cama activa
                cama_code = _formatear_codigo(cama_activa.id, prefijo="#C-C")
                st.markdown(f"""
                <div style='background:#dbeafe; padding:12px 15px; border-radius:10px; border-left:4px solid #3b82f6; margin-bottom:15px;'>
                    <strong>🛏️ Cama Activa: {cama_code} ({cama_activa.pabellon})</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # Tabs para organizar la información del paciente
                tab_paciente, tab_registro, tab_documentos = st.tabs([
                    "👤 Datos",
                    "📋 Registro",
                    "📄 Documentos"
                ])
                
                with tab_paciente:
                    st.markdown(f"""
                    <div style='background:#f0fdf4; padding:15px; border-radius:10px; border-left:4px solid #22c55e;'>
                        <h4>👤 {paciente.nombre}</h4>
                        <p><b>Edad:</b> {paciente.edad} años | <b>DNI:</b> {getattr(paciente, 'dni', 'No registrado')}</p>
                        <p><b>Diagnóstico:</b> {getattr(paciente, 'diagnostico', 'Pendiente')}</p>
                        <p><b>Médico:</b> {getattr(paciente, 'medico_cargo', 'Dr. Asignado')}</p>
                        <p><b>Ingreso:</b> {paciente.hora_ingreso.strftime('%d/%m %H:%M') if hasattr(paciente, 'hora_ingreso') else 'Pendiente'}</p>
                        <p><b>Alta estimada:</b> {paciente.hora_alta_prevista.strftime('%d/%m %H:%M') if hasattr(paciente, 'hora_alta_prevista') else 'Pendiente'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # ============================================================
                    # BOTÓN DE PREDICCIÓN DE ALTA CON IA
                    # ============================================================
                    col_pred1, col_pred2 = st.columns([2, 1])
                    with col_pred1:
                        if st.button("🤖 Predecir Alta con IA", type="secondary", use_container_width=True):
                            with st.spinner("🧠 Analizando datos del paciente..."):
                                fecha_predicha, prediccion_texto = predecir_alta_con_ia(paciente)
                                st.session_state[f"prediccion_alta_{paciente.id}"] = {
                                    "fecha": fecha_predicha,
                                    "texto": prediccion_texto,
                                    "timestamp": datetime.now().strftime("%H:%M")
                                }
                                st.rerun()
                    
                    with col_pred2:
                        if st.button("📊 Ver Análisis", use_container_width=True):
                            st.session_state[f"ver_analisis_{paciente.id}"] = not st.session_state.get(f"ver_analisis_{paciente.id}", False)
                            st.rerun()
                    
                    # Mostrar predicción si existe
                    if f"prediccion_alta_{paciente.id}" in st.session_state:
                        pred = st.session_state[f"prediccion_alta_{paciente.id}"]
                        if pred["fecha"]:
                            dias_restantes = (pred["fecha"] - datetime.now()).days
                            st.markdown(f"""
                            <div style='background:#dbeafe; padding:15px; border-radius:10px; border-left:4px solid #3b82f6; margin-top:10px;'>
                                <strong>🤖 Predicción de Alta</strong><br>
                                📅 <b>Fecha estimada:</b> {pred["fecha"].strftime('%d/%m/%Y')} ({dias_restantes} días)<br>
                                🕐 <b>Generado:</b> {pred["timestamp"]}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info(f"🤖 Análisis generado:\n\n{pred['texto']}")
                    
                    # Mostrar análisis detallado
                    if st.session_state.get(f"ver_analisis_{paciente.id}", False) and f"prediccion_alta_{paciente.id}" in st.session_state:
                        with st.expander("📊 Análisis Detallado de la IA", expanded=True):
                            pred = st.session_state[f"prediccion_alta_{paciente.id}"]
                            st.markdown(pred["texto"])
                            
                            # Botón para actualizar la fecha de alta
                            if pred["fecha"]:
                                if st.button("📝 Actualizar Alta Estimada", type="primary", use_container_width=True):
                                    paciente.hora_alta_prevista = pred["fecha"]
                                    st.success(f"✅ Fecha de alta actualizada a {pred['fecha'].strftime('%d/%m/%Y')}")
                                    st.rerun()
                    
                    # ============================================================
                    # BOTÓN RETIRAR PACIENTE
                    # ============================================================
                    col_retiro1, col_retiro2 = st.columns(2)
                    with col_retiro1:
                        if st.button("🚪 Retirar Paciente", type="primary", use_container_width=True):
                            # Guardar referencia al paciente antes de limpiar
                            paciente_a_retirar = paciente
                            
                            # 1. Liberar la cama
                            cama_activa.ocupada = False
                            cama_activa.necesita_limpieza = True
                            cama_activa.hora_liberada = datetime.now()
                            
                            # 2. Limpiar la referencia al paciente en la cama
                            if hasattr(cama_activa, 'paciente_actual'):
                                cama_activa.paciente_actual = None
                            cama_activa.paciente_id = None
                            
                            # 3. Actualizar el estado del paciente
                            if paciente_a_retirar:
                                paciente_a_retirar.estado = "dado_de_alta"
                                paciente_a_retirar.hora_alta = datetime.now()
                            
                            # 4. Agregar a cola de limpieza
                            if agregar_a_cola_limpieza(cama_activa.id, cama_activa.pabellon):
                                st.success(f"✅ Paciente {paciente_a_retirar.nombre if paciente_a_retirar else ''} retirado de Cama #{cama_activa.id}")
                                st.info(f"📢 Notificación enviada al equipo de limpieza")
                                
                                # 5. Limpiar selección y recargar
                                st.session_state.cama_seleccionada = None
                                st.rerun()
                    
                    with col_retiro2:
                        if st.button("📋 Ver Historial Completo", use_container_width=True):
                            st.info(f"📜 Historial completo de {paciente.nombre}")
                
                with tab_registro:
                    render_registro_paciente(paciente)
                
                with tab_documentos:
                    render_gestion_documentos(paciente)
        
        elif cama_activa and cama_activa.necesita_limpieza:
            cama_code = _formatear_codigo(cama_activa.id, prefijo="#C-C")
            st.markdown(f"""
            <div style='background:#fffbeb; padding:15px; border-radius:10px; border-left:4px solid #f59e0b;'>
                <h4>🟡 Cama {cama_code}</h4>
                <p>Pendiente de desinfección</p>
                <p>🕐 Liberada a las {cama_activa.hora_liberada.strftime('%H:%M') if hasattr(cama_activa, 'hora_liberada') else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar cola de limpieza
            st.markdown("### 🧹 Cola de Limpieza")
            for item in st.session_state.cola_limpieza:
                if item["cama_id"] == cama_activa.id and item["estado"] == "pendiente":
                    st.info(f"🕐 En cola desde: {item['hora_retiro']}")
                    
                    tiempo_estimado = st.selectbox(
                        "⏱️ Tiempo estimado:",
                        options=[0.5, 1, 1.5, 2, 2.5, 3, 4],
                        format_func=lambda x: f"{x} hora{'s' if x > 1 else ''}" if x >= 1 else "30 min",
                        key=f"tiempo_quick_{cama_activa.id}"
                    )
                    
                    if st.button("✅ Confirmar Limpieza", type="primary", use_container_width=True):
                        # Marcar cama como limpia
                        cama_activa.necesita_limpieza = False
                        
                        # Actualizar cola
                        for i in st.session_state.cola_limpieza:
                            if i["cama_id"] == cama_activa.id and i["estado"] == "pendiente":
                                i["estado"] = "completado"
                                i["tiempo_estimado"] = tiempo_estimado
                                hora_fin = datetime.now() + timedelta(hours=tiempo_estimado)
                                i["hora_disponible"] = hora_fin.strftime("%H:%M")
                                break
                        
                        # Guardar en historial
                        if "historial_limpiezas" not in st.session_state:
                            st.session_state.historial_limpiezas = []
                        
                        st.session_state.historial_limpiezas.append({
                            "cama_id": cama_activa.id,
                            "pabellon": cama_activa.pabellon,
                            "tiempo_estimado": tiempo_estimado,
                            "hora_inicio": datetime.now().strftime("%H:%M"),
                            "hora_fin_estimada": hora_fin.strftime("%H:%M"),
                            "fecha": datetime.now().strftime("%d/%m/%Y")
                        })
                        
                        # Limpiar cola
                        st.session_state.cola_limpieza = [
                            i for i in st.session_state.cola_limpieza 
                            if not (i["cama_id"] == cama_activa.id and i["estado"] == "completado")
                        ]
                        
                        st.success(f"✅ Cama #{cama_activa.id} limpia y disponible")
                        st.rerun()
        
        elif cama_activa and not cama_activa.ocupada and not cama_activa.necesita_limpieza:
            cama_code = _formatear_codigo(cama_activa.id, prefijo="#C-C")
            st.markdown(f"""
            <div style='background:#f0fdf4; padding:15px; border-radius:10px; border-left:4px solid #22c55e;'>
                <h4>🟢 Cama {cama_code}</h4>
                <p>Cama libre y disponible para asignación inmediata</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("➕ Asignar Paciente", type="primary", use_container_width=True):
                st.info("🔄 Redirigiendo al registro de paciente...")
                st.session_state.pagina_actual = "registro_paciente"
                st.rerun()
        
        else:
            st.info("👆 Selecciona una cama del mapa para ver los detalles")