# Prompt para continuar el desarrollo con Claude Code / Gemini

Copia y pega esto (ajustando lo que necesites) para que la IA entienda el contexto completo del repo sin que tengas que explicarlo de nuevo.

---

```
Estoy trabajando en CamAI, un MVP para un hackathon de salud. El repo ya tiene
código funcional, no lo reescribas desde cero salvo que te lo pida explícitamente.

CONTEXTO DEL PROYECTO:
CamAI es un sistema multiagente de IA que orquesta la gestión de camas
hospitalarias, reduciendo la latencia entre el alta médica y la disponibilidad
real de la cama (de 4.0h a 1.5h en el modelo de negocio). Arquitectura:

  Agente Triage/Ingreso -> Agente Predictor de Alta (Motor LOS)
      -> Agente Orquestador de Camas (algoritmo húngaro real, scipy)
      -> Agente de Limpieza (cola priorizada)

ESTRUCTURA ACTUAL DEL REPO:
- data_gen.py: genera camas y pacientes sintéticos (200 camas, 85% ocupación, ~34 altas/día)
- agents.py: las 4 clases de agentes. El Motor LOS es una heurística (NO ML real,
  es intencional para el MVP). El Orquestador SÍ usa scipy.optimize.linear_sum_assignment
  (algoritmo húngaro real) — este es el componente técnico más creíble del proyecto,
  no lo simplifiques ni lo reemplaces por una heurística.
- app.py: dashboard Streamlit con botón "Simular siguiente hora" que avanza la
  simulación paso a paso. Tiene 4 tabs: Gestor de Camas, Paciente/Familia,
  Cola de Limpieza, Impacto y Negocio.
- README.md: contexto completo de negocio, tomado de la propuesta original.

IMPORTANTE — bug ya corregido que no debes reintroducir:
El Motor LOS predice la hora de alta UNA sola vez por paciente (cuando
p.hora_alta_prevista es None) y NO la recalcula cada hora. Si se recalcula
cada hora hacia adelante, la predicción nunca se cumple y nadie recibe el alta.

LO QUE NECESITO AHORA:
[[ Describe aquí la tarea puntual, por ejemplo: ]]
- "Agrega un gráfico de líneas con la evolución de camas ocupadas/libres por hora"
- "Agrega una vista de 'línea de tiempo' del paciente en el tab de Paciente/Familia"
- "El log de actividad se ve feo, mejóralo con iconos y colores por tipo de evento"
- "Agrega un botón para simular 8 horas de una sola vez (para no clickear tanto en la demo)"
- "Revisa que no haya errores si se llega a 0 pacientes en espera o 0 camas libres"

Antes de tocar código, corre `python -m py_compile app.py agents.py data_gen.py`
para asegurarte de que sigue compilando, y prueba con `streamlit run app.py`.
```

---

## Ideas de mejoras rápidas si les sobra tiempo (ordenadas por impacto/esfuerzo)

1. **Botón "simular 8 horas de una vez"** — para no estar clickeando 20 veces en la demo en vivo.
2. **Gráfico de líneas** (camas ocupadas vs. libres vs. limpieza a lo largo del tiempo simulado) — usar `st.line_chart` con un historial que ya guarden en `session_state`.
3. **Comparación lado a lado "sin CamAI vs. con CamAI"** en el tab de Impacto — correr la misma simulación con `LATENCIA_CAMAI_H = 4.0` (escenario manual) y mostrar la diferencia acumulada de horas-cama.
4. **Manejo de bordes**: qué pasa si `cola_espera_nuevos` está vacía o si no hay camas disponibles por muchas horas seguidas (debería acumularse la cola, no romperse — ya debería funcionar, pero vale la pena probarlo a propósito).
5. **Despliegue público**: si quieren un link en vivo (no solo el repo), Streamlit Community Cloud (streamlit.io/cloud) permite desplegar directo desde un repo de GitHub gratis en minutos — conecten el repo, apunten a `app.py`, y listo.
