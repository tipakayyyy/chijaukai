"""views_paciente.py — Portal del paciente con Gemini vía OpenRouter"""

import streamlit as st

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def render_vista():
    st.markdown(
        "<div class='command-header'>📱 Portal del Paciente — Mi Estadía"
        " CamAI</div>",
        unsafe_allow_html=True,
    )

    paciente = (
        list(st.session_state.pacientes.values())[0]
        if hasattr(st.session_state, "pacientes")
        and st.session_state.pacientes
        else None
    )

    if not paciente:
        st.warning("No hay información de paciente cargada en el sistema.")
        return

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Definición explícita de columnas
    col_perfil, col_chat = st.columns([1.3, 1])

    # =========================================================================
    # COLUMNA IZQUIERDA: PERFIL Y VITALES
    # =========================================================================
    with col_perfil:
        st.markdown(
            f"""
            <div class='room-box'>
                <h2>Hola, {paciente.nombre} 👋</h2>
                <p><b>DNI:</b> {getattr(paciente, 'dni', '71234567')} | <b>Edad:</b> {paciente.edad} años | <b>Género:</b> {getattr(paciente, 'genero', 'Masculino')}</p>
                <hr style='margin: 8px 0;'>
                <p><b>Diagnóstico Activo:</b> {getattr(paciente, 'diagnostico', 'Neumonía')}</p>
                <p><b>Médico Tratante:</b> {getattr(paciente, 'medico_cargo', 'Dr. Roberto Silva')}</p>
                <p><b>Estimación de Alta Médica:</b> {paciente.hora_alta_prevista.strftime('%d/%m a las %H:%M') if hasattr(paciente, 'hora_alta_prevista') and paciente.hora_alta_prevista else 'Pendiente'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_triaje, tab_examenes, tab_kardex = st.tabs([
            "🩺 Triaje y Vitales",
            "🔬 Exámenes Médicos",
            "💊 Plan Médico y Meds",
        ])

        with tab_triaje:
            v = getattr(
                paciente,
                "signos_vitales",
                {"pa": "120/80", "fc": "78 bpm", "temp": "36.8 °C", "spo2": "97%"},
            )
            st.markdown("**Signos Vitales del Ingreso**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("P. Arterial", v.get("pa", "120/80"))
            c2.metric("Pulso", v.get("fc", "78 bpm"))
            c3.metric("Temp", v.get("temp", "36.8 °C"))
            c4.metric("Oxígeno", v.get("spo2", "97%"))

            st.markdown("---")
            st.markdown("**Datos del Triaje Clínico**")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.write(
                    f"• **Clasificación:**"
                    f" {getattr(paciente, 'nivel_triaje', 'Prioridad II (Urgente)')}"
                )
                st.write(
                    f"• **Peso / Talla:**"
                    f" {getattr(paciente, 'peso_talla', '72 kg / 1.70 m')}"
                )
            with col_t2:
                st.write(
                    f"• **Alergias:**"
                    f" {getattr(paciente, 'alergias', 'Sin alergias conocidas')}"
                )
                st.write(
                    f"• **Estado de Ánimo:**"
                    f" {getattr(paciente, 'estado_animo', 'Lúcido y colaborador')}"
                )

        with tab_examenes:
            st.markdown("**Resultados de Exámenes e Imágenes**")
            examenes = getattr(
                paciente,
                "examenes",
                [
                    "Hemograma Completo (Leucocitos: 11,200 /mm³ - Leve elevación)",
                    "PCR Cuantitativo (24 mg/L - Proceso inflamatorio)",
                    (
                        "Radiografía de Tórax (Infiltrado basal derecho compatible"
                        " con neumonía)"
                    ),
                ],
            )
            for ex in examenes:
                st.info(f"📄 **Examen:** {ex}")

        with tab_kardex:
            st.markdown("**Tratamiento e Indicaciones Médicas**")
            meds = getattr(
                paciente,
                "medicamentos",
                [
                    "Ceftriaxona 1g EV cada 12 horas",
                    "Paracetamol 500mg VO si presenta fiebre > 38°C",
                    "Nebulización con Salbutamol cada 8 horas",
                ],
            )
            for med in meds:
                st.success(f"💊 {med}")

    # =========================================================================
    # COLUMNA DERECHA: CHAT CON IA (OPENROUTER)
    # =========================================================================
    with col_chat:
        st.markdown("### 🤖 Asistente Virtual CamAI")

        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        user_query = st.chat_input("Escribe tu duda...")

        if user_query:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_query}
            )
            q_lower = user_query.lower()

            palabras_alarma = [
                "dolor de pecho",
                "no puedo respirar",
                "me ahogo",
                "sangre",
                "desmayo",
                "urgencia",
            ]
            if any(p in q_lower for p in palabras_alarma):
                resp = (
                    "🚨 **ALERTA CRÍTICA REGISTRADA:** Detecté síntomas de alarma."
                    " Notifiqué inmediatamente a enfermería."
                )
            else:
                if not HAS_OPENAI:
                    resp = (
                        "⚠️ *Falta instalar la librería. Ejecuta `pip install openai`"
                        " en tu consola.*"
                    )
                else:
                    try:
                        api_key = st.secrets.get("OPENROUTER_API_KEY")

                        if not api_key:
                            resp = (
                                "⚠️ *Falta configurar `OPENROUTER_API_KEY` en"
                                " `secrets.toml`.*"
                            )
                        else:
                            client = OpenAI(
                                base_url="https://openrouter.ai/api/v1",
                                api_key=api_key.strip(),
                            )

                            examenes_str = ", ".join(getattr(paciente, "examenes", []))
                            meds_str = ", ".join(getattr(paciente, "medicamentos", []))

                            system_prompt = f"""
                            Eres CamAI, un asistente médico virtual amigable, claro y empático.
                            Atiendes al paciente {paciente.nombre} ({paciente.edad} años).

                            DATOS CLÍNICOS:
                            - Diagnóstico: {getattr(paciente, 'diagnostico', 'Neumonía')}
                            - Signos Vitales: PA {v.get('pa')}, FC {v.get('fc')}, Temp {v.get('temp')}, SpO2 {v.get('spo2')}
                            - Exámenes: {examenes_str}
                            - Medicamentos: {meds_str}

                            REGLAS:
                            1. Explica sus exámenes, tratamiento o enfermedad de forma clara y sencilla.
                            2. Responde en máximo 2 párrafos cortos.
                            3. No recetes fármacos ni alteres dosis.
                            4. Usa un tono empático y profesional.
                            """

                            # ============================================================
                            # MODELO MÉDICO ESPECIALIZADO Y GRATUITO
                            # ============================================================
                            # inclusionai/ling-3.0-flash-sante:free está diseñado para:
                            # - Razonamiento médico y seguridad clínica
                            # - Recuperación de evidencia médica
                            # - Tareas médicas de largo alcance
                            # - Totalmente gratuito
                            model_name = "inclusionai/ling-3.0-flash-sante:free"

                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_query},
                                ],
                                extra_headers={
                                    "HTTP-Referer": "http://localhost:8501",
                                    "X-Title": "CamAI",
                                },
                                timeout=30,
                            )

                            if not response.choices:
                                resp = (
                                    "⚠️ *OpenRouter no devolvió una respuesta. Revisa que el"
                                    " modelo esté disponible en tu cuenta.*"
                                )
                            else:
                                resp = response.choices[0].message.content

                    except Exception as e:
                        error_txt = str(e)
                        if "401" in error_txt or "auth" in error_txt.lower():
                            resp = (
                                "⚠️ **Error de autenticación con OpenRouter (401).**"
                                " Verifica que `OPENROUTER_API_KEY` en `secrets.toml`"
                                " sea una key válida generada en"
                                " https://openrouter.ai/keys, sin comillas ni espacios"
                                " extra, y que reiniciaste Streamlit por completo"
                                " (`Ctrl+C` y volver a correr `streamlit run`) para que"
                                " recargue el archivo de secretos."
                            )
                        elif "402" in error_txt or "credit" in error_txt.lower():
                            resp = (
                                "⚠️ **Sin créditos en OpenRouter (402).** Revisa tu saldo"
                                " en https://openrouter.ai/credits."
                            )
                        else:
                            resp = f"⚠️ **Error:** `{error_txt}`"

            st.session_state.chat_history.append(
                {"role": "assistant", "content": resp}
            )
            st.rerun()