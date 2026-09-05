import streamlit as st
from datetime import datetime, timedelta

def render_vista():
    st.markdown("<div class='command-header'>🧹 CamAI Operations — Cola de Desinfección</div>", unsafe_allow_html=True)
    
    # Inicializar el estado de tiempos si no existe
    if "tiempos_limpieza" not in st.session_state:
        st.session_state.tiempos_limpieza = {}
    
    # Inicializar cola de limpieza si no existe (integración con Command Center)
    if "cola_limpieza" not in st.session_state:
        st.session_state.cola_limpieza = []
    
    # Obtener camas que necesitan limpieza (de la fuente principal)
    camas_limpieza = [c for c in st.session_state.camas.values() if c.necesita_limpieza]
    
    # Sincronizar con la cola de limpieza
    sincronizar_cola_limpieza(camas_limpieza)

    if not camas_limpieza:
        st.success("✨ ¡No hay camas pendientes de desinfección!")
        # Mostrar estadísticas de limpiezas completadas
        mostrar_estadisticas()
        # Mostrar historial de limpiezas recientes
        mostrar_historial_reciente()
    else:
        # Mostrar resumen rápido
        col_total, col_estimado, col_cola = st.columns(3)
        with col_total:
            st.metric("🧹 Camas por limpiar", len(camas_limpieza))
        with col_estimado:
            tiempos = [st.session_state.tiempos_limpieza.get(c.id, 0) for c in camas_limpieza]
            tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
            st.metric("⏱️ Tiempo promedio", f"{tiempo_promedio:.1f} hrs" if tiempo_promedio > 0 else "No estimado")
        with col_cola:
            en_cola = len([i for i in st.session_state.cola_limpieza if i["estado"] == "pendiente"])
            st.metric("📋 En cola", en_cola)
        
        st.divider()
        
        # Mostrar cada cama con opciones de tiempo
        for idx, c in enumerate(camas_limpieza):
            with st.container():
                # Verificar si la cama está en la cola
                item_cola = next((i for i in st.session_state.cola_limpieza 
                                 if i["cama_id"] == c.id and i["estado"] == "pendiente"), None)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Mostrar información de la cama con estado de cola
                    tiempo_espera = ""
                    if item_cola:
                        tiempo_espera = f"🕐 En cola desde: {item_cola['hora_retiro']}"
                    
                    st.markdown(f"""
                    <div class='room-box'>
                        <h4>🟨 Cama #C-C-{c.id:03d} — {c.pabellon}</h4>
                        <p>Estado: Liberada por el equipo médico. Requiere higienización completa.</p>
                        <p style='font-size: 0.9em; color: #666;'>{tiempo_espera}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Selector de tiempo estimado
                    tiempo_actual = st.session_state.tiempos_limpieza.get(c.id, 1)
                    
                    # Opciones de tiempo: 0.5 a 8 horas (más precisión)
                    opciones_tiempo = [0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8]
                    
                    nuevo_tiempo = st.selectbox(
                        "⏱️ Tiempo estimado",
                        options=opciones_tiempo,
                        index=opciones_tiempo.index(tiempo_actual) if tiempo_actual in opciones_tiempo else 1,
                        format_func=lambda x: f"{x} hora{'s' if x > 1 else ''}" if x >= 1 else "30 minutos",
                        key=f"tiempo_{c.id}_{idx}",
                        label_visibility="collapsed"
                    )
                    
                    # Guardar el tiempo seleccionado
                    st.session_state.tiempos_limpieza[c.id] = nuevo_tiempo
                
                # Botones de acción
                col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([2, 1, 1, 1])
                
                with col_btn1:
                    if st.button(
                        f"🧼 Confirmar Limpieza #{c.id}",
                        key=f"clean_{c.id}_{idx}",
                        use_container_width=True,
                        type="primary"
                    ):
                        # Registrar tiempo real de limpieza
                        tiempo_real = st.session_state.tiempos_limpieza.get(c.id, 1)
                        hora_inicio = datetime.now()
                        hora_fin = hora_inicio + timedelta(hours=tiempo_real)
                        
                        # Marcar cama como limpia
                        c.necesita_limpieza = False
                        
                        # Guardar registro de limpieza
                        if "historial_limpiezas" not in st.session_state:
                            st.session_state.historial_limpiezas = []
                        
                        st.session_state.historial_limpiezas.append({
                            "cama_id": c.id,
                            "pabellon": c.pabellon,
                            "tiempo_estimado": tiempo_real,
                            "hora_inicio": hora_inicio.strftime("%H:%M"),
                            "hora_fin_estimada": hora_fin.strftime("%H:%M"),
                            "fecha": datetime.now().strftime("%d/%m/%Y"),
                            "hora_completa": hora_inicio.strftime("%H:%M")
                        })
                        
                        # Actualizar la cola de limpieza
                        actualizar_cola_limpieza(c.id, tiempo_real, hora_fin)
                        
                        # Eliminar tiempo guardado
                        if c.id in st.session_state.tiempos_limpieza:
                            del st.session_state.tiempos_limpieza[c.id]
                        
                        st.toast(f"✅ Cama #{c.id} limpiada en {tiempo_real} hora{'s' if tiempo_real > 1 else ''}!", icon="🟢")
                        st.balloons()
                        st.rerun()
                
                with col_btn2:
                    if st.button(
                        f"⏰ Reprogramar",
                        key=f"reprogramar_{c.id}_{idx}",
                        use_container_width=True
                    ):
                        # Resetear tiempo a 1 hora
                        st.session_state.tiempos_limpieza[c.id] = 1
                        st.toast(f"⏱️ Tiempo de limpieza reiniciado para cama #{c.id}", icon="🔄")
                        st.rerun()
                
                with col_btn3:
                    if st.button(
                        f"📝 Nota",
                        key=f"nota_{c.id}_{idx}",
                        use_container_width=True
                    ):
                        # Mostrar diálogo para nota rápida
                        st.info(f"📌 Cama #{c.id}: Limpieza estimada en {st.session_state.tiempos_limpieza.get(c.id, 1)} horas")
                
                with col_btn4:
                    if st.button(
                        f"⏭️ Urgente",
                        key=f"urgente_{c.id}_{idx}",
                        use_container_width=True
                    ):
                        # Marcar como urgente (tiempo reducido a 30 min)
                        st.session_state.tiempos_limpieza[c.id] = 0.5
                        st.warning(f"⚡ Cama #{c.id} marcada como URGENTE - 30 minutos estimados")
                        st.rerun()
                
                st.divider()
        
        # Mostrar resumen de tiempos estimados
        with st.expander("📊 Resumen de tiempos estimados", expanded=False):
            datos_tabla = []
            for c in camas_limpieza:
                tiempo = st.session_state.tiempos_limpieza.get(c.id, 1)
                hora_fin = datetime.now() + timedelta(hours=tiempo)
                item_cola = next((i for i in st.session_state.cola_limpieza 
                                 if i["cama_id"] == c.id and i["estado"] == "pendiente"), None)
                
                datos_tabla.append({
                    "Cama": f"C-C-{c.id:03d}",
                    "Pabellón": c.pabellon,
                    "Tiempo estimado": f"{tiempo} hora{'s' if tiempo > 1 else ''}" if tiempo >= 1 else "30 min",
                    "Finalización estimada": hora_fin.strftime("%H:%M"),
                    "En cola desde": item_cola['hora_retiro'] if item_cola else "N/A"
                })
            
            if datos_tabla:
                st.dataframe(
                    datos_tabla,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Cama": "Cama",
                        "Pabellón": "Pabellón",
                        "Tiempo estimado": "⏱️ Tiempo",
                        "Finalización estimada": "⏰ Finaliza",
                        "En cola desde": "🕐 En cola"
                    }
                )
        
        # Mostrar estadísticas históricas
        mostrar_estadisticas()
        mostrar_historial_reciente()


def sincronizar_cola_limpieza(camas_limpieza):
    """Sincroniza la cola de limpieza con las camas que necesitan limpieza"""
    # Agregar camas que no están en la cola
    for c in camas_limpieza:
        if not any(item["cama_id"] == c.id and item["estado"] == "pendiente" 
                   for item in st.session_state.cola_limpieza):
            st.session_state.cola_limpieza.append({
                "cama_id": c.id,
                "pabellon": c.pabellon,
                "hora_retiro": datetime.now().strftime("%H:%M"),
                "estado": "pendiente",
                "tiempo_estimado": None,
                "hora_disponible": None
            })
    
    # Eliminar camas que ya no necesitan limpieza
    ids_camas_limpieza = [c.id for c in camas_limpieza]
    st.session_state.cola_limpieza = [
        item for item in st.session_state.cola_limpieza 
        if not (item["estado"] == "pendiente" and item["cama_id"] not in ids_camas_limpieza)
    ]


def actualizar_cola_limpieza(cama_id, tiempo_estimado, hora_fin):
    """Actualiza la cola de limpieza cuando se completa una limpieza"""
    for item in st.session_state.cola_limpieza:
        if item["cama_id"] == cama_id and item["estado"] == "pendiente":
            item["estado"] = "completado"
            item["tiempo_estimado"] = tiempo_estimado
            item["hora_disponible"] = hora_fin.strftime("%H:%M")
            break


def mostrar_estadisticas():
    """Muestra estadísticas de limpiezas realizadas"""
    if "historial_limpiezas" not in st.session_state or not st.session_state.historial_limpiezas:
        return
    
    with st.expander("📈 Estadísticas de limpieza", expanded=False):
        historial = st.session_state.historial_limpiezas[-20:]  # Últimas 20 limpiezas
        
        # Calcular estadísticas
        tiempos = [h["tiempo_estimado"] for h in historial]
        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
        tiempo_min = min(tiempos) if tiempos else 0
        tiempo_max = max(tiempos) if tiempos else 0
        
        # Contar por pabellón
        pabellones = {}
        for h in historial:
            pabellon = h.get("pabellon", "Desconocido")
            pabellones[pabellon] = pabellones.get(pabellon, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🧹 Total limpiezas", len(historial))
        with col2:
            st.metric("⏱️ Promedio tiempo", f"{tiempo_promedio:.1f} hrs")
        with col3:
            st.metric("⚡ Más rápido", f"{tiempo_min:.1f} hrs" if tiempo_min >= 1 else "30 min")
        with col4:
            st.metric("🐢 Más lento", f"{tiempo_max:.1f} hrs")
        
        # Mostrar distribución por pabellón
        st.markdown("**📊 Distribución por pabellón:**")
        cols_pab = st.columns(min(len(pabellones), 4))
        for i, (pab, count) in enumerate(pabellones.items()):
            with cols_pab[i % 4]:
                st.metric(f"🏥 {pab}", count)


def mostrar_historial_reciente():
    """Muestra el historial reciente de limpiezas"""
    if "historial_limpiezas" not in st.session_state or not st.session_state.historial_limpiezas:
        return
    
    with st.expander("📋 Historial de limpiezas recientes", expanded=False):
        historial = st.session_state.historial_limpiezas[-10:]  # Últimas 10
        
        # Crear tabla de historial
        datos_historial = []
        for h in reversed(historial):  # Mostrar más recientes primero
            tiempo_str = f"{h['tiempo_estimado']} hora{'s' if h['tiempo_estimado'] > 1 else ''}" if h['tiempo_estimado'] >= 1 else "30 min"
            datos_historial.append({
                "🛏️ Cama": f"C-C-{h['cama_id']:03d}",
                "🏥 Pabellón": h.get("pabellon", "N/A"),
                "⏱️ Tiempo": tiempo_str,
                "🕐 Inicio": h.get("hora_inicio", h.get("hora_completa", "N/A")),
                "⏰ Final": h.get("hora_fin_estimada", "N/A"),
                "📅 Fecha": h.get("fecha", "N/A")
            })
        
        if datos_historial:
            st.dataframe(
                datos_historial,
                use_container_width=True,
                hide_index=True
            )
        
        # Mostrar resumen del día
        hoy = datetime.now().strftime("%d/%m/%Y")
        limpiezas_hoy = [h for h in st.session_state.historial_limpiezas if h.get("fecha") == hoy]
        if limpiezas_hoy:
            st.info(f"📊 **Resumen del día:** {len(limpiezas_hoy)} limpiezas realizadas hoy")
            
            # Tiempo promedio del día
            tiempos_hoy = [h["tiempo_estimado"] for h in limpiezas_hoy]
            prom_hoy = sum(tiempos_hoy) / len(tiempos_hoy) if tiempos_hoy else 0
            st.caption(f"⏱️ Tiempo promedio hoy: {prom_hoy:.1f} horas")


# Función para que el Command Center pueda llamar a limpieza
def agregar_a_cola_limpieza(cama_id, pabellon):
    """Agrega una cama a la cola de limpieza (llamada desde Command Center)"""
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