<<<<<<< HEAD
# CamAI — Sistema Multiagente de Orquestación de Camas Hospitalariasbest team del brodt hackathon
=======
# CamAI — Sistema Multiagente de Orquestación de Camas Hospitalarias

>>>>>>> d18e549 (feat: MVP CamAI Portal Paciente)
**Hackathon BRODT · Track "Future of Health & Wellbeing"**

> MVP funcional que demuestra la arquitectura CamAI Swarm Engine: predicción de alta, optimización de asignación de camas (algoritmo húngaro) y priorización de limpieza, sobre un dashboard en tiempo real.

---

## 1. Problema y contexto

En un hospital de mediana o alta complejidad, la cama no es solo un mueble: es la unidad de producción más cara y sistemáticamente infrautilizada del sistema. El problema de gestión de camas no es de infraestructura —construir más camas— sino de **coordinación de información en tiempo real**.

El cuello de botella crítico no ocurre en la cama en sí, sino en la transición entre el alta médica y la disponibilidad real de esa cama para el siguiente paciente. Tres fallas estructurales lo explican:

1. **Incertidumbre** del paciente y su familia sobre el momento real del alta, que retrasa la logística de transporte y coordinación externa.
2. **Silos de información** entre los sistemas clínicos (HIS/EHR), el equipo de limpieza y admisiones, que impiden una visión unificada del estado de cada cama.
3. Una **latencia de 3 a 6 horas** entre la orden médica de alta y la disponibilidad efectiva de la cama.

**Caso base:** hospital de 200 camas, 85% de ocupación promedio, 30-34 altas diarias. Con una latencia promedio de 4 horas por alta, el sistema pierde **120 horas-cama por día** — el equivalente a 5 camas completas paralizadas de forma permanente, sin que exista ningún problema físico, presupuestario o de personal que lo justifique.

La evidencia externa confirma que el problema es sistémico: estudios sitúan el costo marginal de cada día de estancia evitable entre $2,000 y $4,000 USD (Journal of Hospital Medicine / VectorCare); solo en Florida se perdieron cerca de 403,000 días-cama en 2025 por retrasos de traslado (~$1,000–$1,250 millones USD en capacidad atrapada). Hospitales comparables reportan tiempos de alta de casi 4 horas para pacientes particulares y más de 5 para pacientes con seguro (Journal LWW).

## 2. Usuario y oportunidad

CamAI no diseña una solución para "el hospital" como entidad abstracta, sino para cuatro actores concretos: **el paciente y su familia, el gestor de camas, el personal médico/enfermería y el equipo de limpieza**.

La oportunidad también es reputacional: un análisis de 170,000 comentarios de pacientes encontró que quienes mencionaban negativamente el tiempo de espera tenían 3.4 veces más probabilidad de convertirse en detractores en el NPS (NRC Health). CamAI proyecta una mejora de **+25 puntos de NPS** al eliminar la incertidumbre y comprimir los tiempos de espera del alta.

## 3. Solución: arquitectura CamAI Swarm Engine

```
[ Agente Triage/Ingreso ] --> [ Agente Predictor de Alta (Motor LOS) ]
            |                                |
            v                                v
      [ Agente Orquestador de Camas -- optimización húngara ]
                          |
                          v
      [ Agente de Operaciones / Limpieza -- cola dinámica ]
```

- **Agente de Triage/Ingreso**: clasifica y registra el estado clínico inicial de cada paciente.
- **Agente Predictor de Alta (Motor LOS)**: estima el momento probable del alta.
- **Agente Orquestador de Camas**: resuelve la asignación óptima entre altas previstas y nuevos ingresos mediante **optimización húngara**.
- **Agente de Operaciones/Limpieza**: traduce esa asignación en una cola de trabajo priorizada en tiempo real.

La arquitectura ya está validada en producción por referentes del sector: el **Judy Reitz Capacity Command Center** de Johns Hopkins asigna camas 30% más rápido y redujo 70% los retrasos de traslado desde quirófano (Harvard D3); **Tampa General** reportó 83% menos tiempo de colocación y 45% menos espera para limpieza de camas al implementar IA de patient placement (ScienceSoft). Estas cifras validan directamente la meta central de CamAI: reducir el tiempo de gestión de alta de **4.0 a 1.5 horas**.

## 4. Tecnología e innovación

Tres tecnologías maduras integradas en una arquitectura orientada a un problema operativo específico:

- **Motor Predictivo LOS**: entrenado (en producción) con variables clínicas y administrativas para estimar la hora de alta con horas de anticipación.
- **Orquestación Multiagente**: los agentes se coordinan de forma asíncrona; el Orquestador de Camas resuelve la asignación como un problema de emparejamiento bipartito con el **algoritmo húngaro** (complejidad polinómica), garantizando una asignación óptima global.
- **Interfaces Dinámicas**: notificación para paciente/familia, dashboard en tiempo real para el gestor de camas, cola de trabajo para limpieza.

**Roadmap técnico:** Fase 1 (preparación de datos e integración HIS/EHR) → Fase 2 (motor LOS + agentes) → Fase 3 (piloto MVP en unidad clínica limitada, medición de TAT real vs. proyectado).

## 5. Viabilidad y sostenibilidad

Modelo financiero (hospital de 200 camas, 85% ocupación, LOS actual 5.0 días, 34 altas diarias, $400 USD/día-cama, latencia 4.0→1.5h):

| Métrica | Valor |
|---|---|
| Horas-cama recuperadas/día | ~120 h (≈3.54 camas equivalentes) |
| Techo operativo anual (régimen estable) | $365,000 USD |
| Captura Año 1 (tasa conservadora 50%) | $182,500 USD |
| Costos Año 1 | $95,000 USD |
| **ROI Año 1** | **92.1%** |
| **Payback** | **6.2 meses** |

Modelo **SaaS B2B con renovación anual**: desde el Año 2, superada la marcha blanca, la captura tiende al techo de $365,000 USD sin un nuevo ciclo de venta.

## 6. Escalabilidad y futuro

- **Etapa 1 — Piloto clínico (0-3 meses):** validación en una unidad del hospital ancla, medición real de TAT y NPS.
- **Etapa 2 — Integración con HIS (3-6 meses):** conexión bidireccional con HIS/EHR y expansión a todas las unidades.
- **Etapa 3 — Escalamiento multi-centro (6-12 meses):** despliegue en red de hospitales bajo el mismo modelo SaaS, sin infraestructura física adicional por sitio.

Johns Hopkins Medicine gestiona más de 115,000 admisiones anuales en 6 hospitales (2,671 camas) y logró el equivalente a 13-16 camas adicionales solo optimizando el flujo de pacientes con IA — sin construir una sola cama nueva (Advisory Board). La misma arquitectura es extensible a planificación de quirófanos, gestión de personal clínico y coordinación de traslados entre centros.

---

## 🧪 Sobre este repositorio: alcance del MVP

Este repo contiene una **demo funcional** construida en el marco del hackathon, no el producto final. Decisiones explícitas de alcance:

| Componente | En este MVP | En producción |
|---|---|---|
| Motor LOS | Heurística por complejidad clínica + variabilidad aleatoria | Modelo de ML entrenado con datos históricos HIS/EHR |
| Orquestador de Camas | **Algoritmo húngaro real** (`scipy.optimize.linear_sum_assignment`) | El mismo algoritmo, sobre datos reales en tiempo real |
| Datos | Generador sintético (200 camas, 85% ocupación, ~34 altas/día) | Integración bidireccional con HIS/EHR |
| Interfaces | Dashboard Streamlit (3 vistas simuladas) | App móvil para familias, dashboard clínico, app de limpieza |
| Orquestación multiagente | Funciones Python secuenciales que simulan el rol de cada agente | Protocolo de mensajería asíncrono entre agentes autónomos |

La pieza que **sí es técnicamente real y no una simulación superficial** es la optimización húngara para la asignación cama-paciente, que es el componente que la propuesta identifica como clave para la asignación óptima global.

## 🚀 Cómo correr la demo

```bash
git clone <URL_DE_ESTE_REPO>
cd camai-hackathon
pip install -r requirements.txt
streamlit run app.py
```

Se abrirá en `http://localhost:8501`. Usa el botón **"▶️ Simular siguiente hora"** en la barra lateral para avanzar la simulación y ver a los agentes trabajando: predicción de alta → liberación de cama → asignación óptima → cola de limpieza.

## 📁 Estructura del repositorio

```
camai-hackathon/
├── app.py            # Dashboard Streamlit (UI + loop de simulación)
├── agents.py         # Los 4 agentes: Triage, Motor LOS, Orquestador, Limpieza
├── data_gen.py        # Generador de datos sintéticos (camas y pacientes)
├── requirements.txt
└── README.md
```

## Referencias

- Advisory Board. (2018). *How Johns Hopkins used a 'command center' to add the equivalent of 16 beds.* https://www.advisory.com/daily-briefing/2018/06/11/command-center
- Babu, M. S., Ramesh, A. S., & Vignesh, S. (2022). *A study of the causes of delay in patient discharge process in a multispecialty hospital.* https://journals.lww.com/qaij/fulltext/2022/03010/a_study_of_the_causes_of_delay_in_patient.3.aspx
- Forster, A. J., et al. (2003). *The effect of hospital occupancy on emergency department length of stay and patient disposition.* Academic Emergency Medicine, 10(2), 127–133.
- Johns Hopkins Medicine. (2016). *Capacity command center uses predictive analytics to improve patient flow.* https://d3.harvard.edu/platform-rctom/submission/capacity-command-center-machine-learning-hospital-management-at-johns-hopkins/
- NRC Health. (2020). *Understanding perceptions about wait times and their impact on patient satisfaction and NPS.* https://nrchealth.com/resource/understanding-perceptions-about-wait-times/
- Ryu, J. H., Kim, S. H., & Park, Y. S. (2024). *Exploring the ramifications of delayed hospital discharges and extended ED length of stay on overall healthcare costs.* PMC11210572. https://pmc.ncbi.nlm.nih.gov/articles/PMC11210572/
- ScienceSoft. (2023). *AI-powered healthcare command center: Real-world case studies in patient placement and bed management.* https://www.scnsoft.com/healthcare/artificial-intelligence/command-center
- VectorCare. (2024–2025). *The hidden cost of discharge delays* / *Patient logistics and discharge transport delays.* https://www.vectorcare.com/journal/
