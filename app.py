import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Seleccionador de Estabilizadores Niki",
    page_icon="⚡",
    layout="wide"
)

# Estilos CSS personalizados (Nomenclatura y diseño Must/Bluetti)
st.markdown("""
    <style>
    .metric-container { background-color: #F8FAFC; padding: 15px; border-radius: 8px; border: 1px solid #E2E8F0; }
    .card-optimal { background-color: #ECFDF5; padding: 18px; border-radius: 10px; border-left: 6px solid #10B981; margin-bottom: 15px; }
    .card-expansion { background-color: #EFF6FF; padding: 18px; border-radius: 10px; border-left: 6px solid #3B82F6; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 18px; border-radius: 10px; border-left: 6px solid #F59E0B; margin-bottom: 15px; }
    .badge-optimal { background-color: #10B981; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-alert { background-color: #F59E0B; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Seleccionador Técnico de Estabilizadores Niki")
st.markdown("Dimensionamiento dinámico en kVA con desclasificación por caídas de tensión ($F_{\\text{desc}}$) y motor de selección multinivel.")

# --- CATÁLOGO DE EQUIPOS NIKI ---
CATALOGO_NIKI = {
    "Monofásico 120V": [
        {"serie": "COL-A", "modelo": "COL-A 5 kVA", "kva": 5.0, "amp": 40, "pdf": "COL-A_5kVA.pdf"},
        {"serie": "COL-A", "modelo": "COL-A 10 kVA", "kva": 10.0, "amp": 80, "pdf": "COL-A_10kVA.pdf"},
        {"serie": "COL-B", "modelo": "COL-B 5 kVA", "kva": 5.0, "amp": 40, "pdf": "COL-B_5kVA.pdf"},
        {"serie": "COL-B", "modelo": "COL-B 10 kVA", "kva": 10.0, "amp": 80, "pdf": "COL-B_10kVA.pdf"},
    ],
    "220V Monofásico (L1 + L2)": [
        {"serie": "COL115", "modelo": "COL115 5 kVA", "kva": 5.0, "amp": 21, "pdf": "COL115_5kVA.pdf"},
        {"serie": "COL115", "modelo": "COL115 10 kVA", "kva": 10.0, "amp": 43, "pdf": "COL115_10kVA.pdf"},
        {"serie": "COL115", "modelo": "COL115 20 kVA", "kva": 20.0, "amp": 86, "pdf": "COL115_20kVA.pdf"},
    ],
    "Bifásico 120/208V": [
        {"serie": "TND/S", "modelo": "TND/S 10 kVA", "kva": 10.0, "amp": 40, "pdf": "TNDS_10kVA.pdf"},
        {"serie": "TND/S", "modelo": "TND/S 30 kVA", "kva": 30.0, "amp": 120, "pdf": "TNDS_30kVA.pdf"},
        {"serie": "TND/S", "modelo": "TND/S 50 kVA", "kva": 50.0, "amp": 200, "pdf": "TNDS_50kVA.pdf"},
    ],
    "Trifásico 120/208V": [
        {"serie": "TNSA-U", "modelo": "TNSA-U 30 kVA", "kva": 30.0, "amp": 75, "pdf": "TNSA_30kVA.pdf"},
        {"serie": "TNSA-U", "modelo": "TNSA-U 50 kVA", "kva": 50.0, "amp": 130, "pdf": "TNSA_50kVA.pdf"},
        {"serie": "TNSA-U", "modelo": "TNSA-U 100 kVA", "kva": 100.0, "amp": 260, "pdf": "TNSA_100kVA.pdf"},
        {"serie": "TNSA-U", "modelo": "TNSA-U 150 kVA", "kva": 150.0, "amp": 390, "pdf": "TNSA_150kVA.pdf"},
        {"serie": "TNSA-U", "modelo": "TNSA-U 200 kVA", "kva": 200.0, "amp": 520, "pdf": "TNSA_200kVA.pdf"},
    ],
    "Trifásico 277/480V": [
        {"serie": "TNSB-U", "modelo": "TNSB-U 100 kVA", "kva": 100.0, "amp": 110, "pdf": "TNSB_100kVA.pdf"},
        {"serie": "TNSB-U", "modelo": "TNSB-U 150 kVA", "kva": 150.0, "amp": 165, "pdf": "TNSB_150kVA.pdf"},
        {"serie": "TNSB-U", "modelo": "TNSB-U 200 kVA", "kva": 200.0, "amp": 220, "pdf": "TNSB_200kVA.pdf"},
    ]
}

# --- FUNCIONES DE DESCLASIFICACIÓN ---
def obtener_factor_desclasificacion(sistema, v_medido):
    if sistema == "Monofásico 120V":
        if v_medido >= 108: return 1.0
        if v_medido < 65: return 0.0
        puntos = [(65, 0.40), (75, 0.50), (85, 0.72), (108, 1.00)]
    elif sistema == "220V Monofásico (L1 + L2)":
        if v_medido >= 198: return 1.0
        if v_medido < 45: return 0.0
        puntos = [(45, 0.15), (60, 0.20), (95, 0.30), (150, 0.50), (198, 1.00)]
    elif sistema in ["Bifásico 120/208V", "Trifásico 120/208V"]:
        if v_medido >= 190: return 1.0
        if v_medido < 140: return 0.0
        return 0.50 + 0.01 * (v_medido - 140)
    elif sistema == "Trifásico 277/480V":
        if v_medido < 336 or v_medido > 624: return 0.0
        puntos = [(336, 0.40), (432, 1.00), (528, 1.00), (624, 0.50)]

    for i in range(len(puntos) - 1):
        x1, y1 = puntos[i]
        x2, y2 = puntos[i + 1]
        if x1 <= v_medido <= x2:
            return y1 + ((v_medido - x1) / (x2 - x1)) * (y2 - y1)
    return 1.0

def evaluar_estado_carga(pct_carga):
    if pct_carga > 90:
        return "⚠️ Carga Crítica (>90%)", "#EF4444"
    elif 60 <= pct_carga <= 85:
        return "✅ Carga Óptima (60-85%)", "#10B981"
    elif pct_carga < 50:
        return "ℹ️ Carga Ligera (<50%)", "#3B82F6"
    else:
        return "👍 Carga Aceptable", "#F59E0B"

# --- SIDEBAR: PARÁMETROS DE ENTORNOS ---
st.sidebar.header("⚙️ Configuración Eléctrica")

sistema_sel = st.sidebar.selectbox("Configuración de Red", list(CATALOGO_NIKI.keys()))

voltajes_def = {
    "Monofásico 120V": (120, 60, 150),
    "220V Monofásico (L1 + L2)": (220, 40, 280),
    "Bifásico 120/208V": (208, 130, 240),
    "Trifásico 120/208V": (208, 130, 240),
    "Trifásico 277/480V": (480, 300, 650)
}

v_nom, v_min_lim, v_max_lim = voltajes_def[sistema_sel]
v_medido = st.sidebar.number_input("Voltaje Mínimo Medido en Sitio (V)", min_value=v_min_lim, max_value=v_max_lim, value=v_nom)
margen_reserva = st.sidebar.slider("Margen de Reserva / Seguridad (%)", min_value=0, max_value=50, value=25, step=5)

# --- PANEL DE CARGAS INTERACTIVO ---
st.subheader("📋 Levantar Cuadro de Cargas")

if "cargas" not in st.session_state:
    st.session_state.cargas = pd.DataFrame([
        {"Descripción": "Circuito Principal", "Cantidad": 1, "Potencia": 8.0, "Unidad": "kVA", "FP": 0.8}
    ])

cargas_df = st.data_editor(
    st.session_state.cargas,
    num_rows="dynamic",
    column_config={
        "Descripción": st.column_config.TextColumn("Equipo / Circuito"),
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
        "Potencia": st.column_config.NumberColumn("Potencia Unitaria", min_value=0.1, default=1.0, format="%.2f"),
        "Unidad": st.column_config.SelectboxColumn("Unidad", options=["kVA", "kW"], default="kVA"),
        "FP": st.column_config.NumberColumn("FP", min_value=0.5, max_value=1.0, default=0.8, format="%.2f")
    },
    use_container_width=True
)

# --- CÁLCULO DE POTENCIA APARENTE ---
total_kva_carga = 0.0
for _, row in cargas_df.iterrows():
    cant = row.get("Cantidad", 1)
    pot = row.get("Potencia", 0.0)
    unidad = row.get("Unidad", "kVA")
    fp = row.get("FP", 0.8)
    total_kva_carga += (pot / fp if unidad == "kW" and fp > 0 else pot) * cant

f_desc = obtener_factor_desclasificacion(sistema_sel, v_medido)
f_res = 1.0 + (margen_reserva / 100.0)
kva_objetivo = (total_kva_carga * f_res) / f_desc if f_desc > 0 else 0.0

# --- MÉTRICAS PRINCIPALES ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Carga Instalada Directa", f"{total_kva_carga:.2f} kVA")
c2.metric("Reserva Comercial", f"+{margen_reserva}%")
c3.metric("Factor Desclasificación", f"{f_desc * 100:.1f}%")
c4.metric("Demanda Objetivo Niki", f"{kva_objetivo:.2f} kVA")

st.divider()

# --- MOTOR DE SELECCIÓN INTELIGENTE (LOGICA MUST/BLUETTI) ---
st.subheader("🎯 Alternativas Recomendadas")

if f_desc == 0.0:
    st.error(f"❌ Tensión fuera de rango operativo seguro ({v_medido}V).")
else:
    cat = CATALOGO_NIKI[sistema_sel]
    # Filtrar modelos aptos (Capacidad >= Demanda Objetivo)
    aptos = [m for m in cat if m["kva"] >= kva_objetivo]
    
    # Aplicar filtro inteligente de sobredimensionamiento (Máximo 2.5x la demanda objetivo)
    aptos_filtrados = [m for m in aptos if m["kva"] <= (kva_objetivo * 2.5)]
    if not aptos_filtrados and aptos:
        aptos_filtrados = [aptos[0]]  # Si todos superan 2.5x, tomar la opción más pequeña disponible

    if aptos_filtrados:
        modelo_optimo = aptos_filtrados[0]
        cap_efectiva_opt = modelo_optimo["kva"] * f_desc
        pct_opt = (total_kva_carga / cap_efectiva_opt) * 100
        estado_opt, color_opt = evaluar_estado_carga(pct_opt)

        col_opt, col_exp = st.columns(2)

        # CARD 1: MODELO ÓPTIMO RECOMENDADO
        with col_opt:
            st.markdown(f"""
                <div class="card-optimal">
                    <span class="badge-optimal">RECOMENDACIÓN PRINCIPAL</span>
                    <h3 style="margin-top:5px; color:#065F46;">{modelo_optimo['modelo']}</h3>
                    <p><b>Serie:</b> {modelo_optimo['serie']} | <b>Corriente Nominal:</b> {modelo_optimo['amp']} A</p>
                    <hr style="border:0; border-top:1px solid #A7F3D0;">
                    <ul>
                        <li><b>Capacidad Nominal:</b> {modelo_optimo['kva']} kVA</li>
                        <li><b>Capacidad Corregida a {v_medido}V:</b> {cap_efectiva_opt:.2f} kVA</li>
                        <li><b>Nivel de Carga Estimado:</b> {pct_opt:.1f}%</li>
                        <li><b>Estado Operativo:</b> <span style="color:{color_opt}; font-weight:bold;">{estado_opt}</span></li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

        # CARD 2: MODELO PARA EXPANSIÓN (SI EXISTE UN MODELO SUPERIOR EN FILTRADOS)
        with col_exp:
            idx_opt = cat.index(modelo_optimo)
            if idx_opt + 1 < len(cat):
                modelo_exp = cat[idx_opt + 1]
                cap_efectiva_exp = modelo_exp["kva"] * f_desc
                pct_exp = (total_kva_carga / cap_efectiva_exp) * 100
                estado_exp, color_exp = evaluar_estado_carga(pct_exp)

                st.markdown(f"""
                    <div class="card-expansion">
                        <span class="badge-alert">OPCIÓN DE CRECIMIENTO / RESERVA</span>
                        <h3 style="margin-top:5px; color:#1E40AF;">{modelo_exp['modelo']}</h3>
                        <p><b>Serie:</b> {modelo_exp['serie']} | <b>Corriente Nominal:</b> {modelo_exp['amp']} A</p>
                        <hr style="border:0; border-top:1px solid #BFDBFE;">
                        <ul>
                            <li><b>Capacidad Nominal:</b> {modelo_exp['kva']} kVA</li>
                            <li><b>Capacidad Corregida a {v_medido}V:</b> {cap_efectiva_exp:.2f} kVA</li>
                            <li><b>Nivel de Carga Estimado:</b> {pct_exp:.1f}%</li>
                            <li><b>Estado Operativo:</b> <span style="color:{color_exp}; font-weight:bold;">{estado_exp}</span></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ El modelo óptimo es la máxima capacidad comercial disponible para esta serie.")

    else:
        st.markdown(f"""
            <div class="card-warning">
                <h3>⚠️ Capacidad Requerida Excede Catálogo Estándar</h3>
                <p>La carga ajustada de <b>{kva_objetivo:.2f} kVA</b> supera la capacidad del modelo individual más grande para la serie seleccionada.</p>
            </div>
        """, unsafe_allow_html=True)

    # --- TABLA COMPARATIVA COMPLETA ---
    st.subheader("📊 Matriz de Evaluación de la Serie")
    df_eval = pd.DataFrame(cat)
    df_eval["Capacidad Efectiva (kVA)"] = df_eval["kva"] * f_desc
    df_eval["Carga (%)"] = (total_kva_carga / df_eval["Capacidad Efectiva (kVA)"]) * 100
    df_eval["Evaluación"] = df_eval["kva"].apply(lambda x: "✅ Apto" if x >= kva_objetivo else "❌ Insuficiente")
    st.dataframe(df_eval[["serie", "modelo", "kva", "amp", "Capacidad Efectiva (kVA)", "Carga (%)", "Evaluación"]], use_container_width=True)