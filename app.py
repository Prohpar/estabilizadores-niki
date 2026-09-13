import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Seleccionador de Estabilizadores Niki",
    page_icon="⚡",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .card-optimal { background-color: #ECFDF5; padding: 18px; border-radius: 10px; border-left: 6px solid #10B981; margin-bottom: 15px; }
    .card-expansion { background-color: #EFF6FF; padding: 18px; border-radius: 10px; border-left: 6px solid #3B82F6; margin-bottom: 15px; }
    .card-warning { background-color: #FEF3C7; padding: 18px; border-radius: 10px; border-left: 6px solid #F59E0B; margin-bottom: 15px; }
    .badge-optimal { background-color: #10B981; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-alert { background-color: #3B82F6; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Seleccionador Técnico de Estabilizadores Niki")
st.markdown("Dimensionamiento de capacidad aparente (kVA) con tabla de cargas dinámicamente editable y desclasificación por tensión de red.")

# --- CATÁLOGO PRESET DE EQUIPOS DISPONIBLES ---
EQUIPOS_PREDETERMINADOS = {
    "Nevera / Refrigerador Doméstico": {"potencia": 0.40, "unidad": "kW", "fp": 0.80},
    "Cava Cuarto / Freezer Comercial": {"potencia": 1.50, "unidad": "kW", "fp": 0.75},
    "Aire Acondicionado 12,000 BTU": {"potencia": 1.20, "unidad": "kW", "fp": 0.85},
    "Aire Acondicionado 18,000 BTU": {"potencia": 1.80, "unidad": "kW", "fp": 0.85},
    "Aire Acondicionado 24,000 BTU": {"potencia": 2.40, "unidad": "kW", "fp": 0.85},
    "Bomba de Agua 1 HP": {"potencia": 1.10, "unidad": "kVA", "fp": 0.80},
    "Bomba de Agua 2 HP": {"potencia": 2.20, "unidad": "kVA", "fp": 0.80},
    "Iluminación LED General": {"potencia": 0.30, "unidad": "kW", "fp": 0.95},
    "Puesto de Trabajo (PC + Monitores)": {"potencia": 0.50, "unidad": "kVA", "fp": 0.90},
    "Servidor / Rack IT": {"potencia": 2.00, "unidad": "kVA", "fp": 0.95},
    "Microondas / Horno Eléctrico": {"potencia": 1.20, "unidad": "kW", "fp": 0.95},
    "Carga Personalizada": {"potencia": 1.00, "unidad": "kVA", "fp": 0.80}
}

# --- CATÁLOGO DE ESTABILIZADORES NIKI ---
CATALOGO_NIKI = {
    "Monofásico 120V": [
        {"serie": "COL-A", "modelo": "COL-A 5 kVA", "kva": 5.0, "amp": 40},
        {"serie": "COL-A", "modelo": "COL-A 10 kVA", "kva": 10.0, "amp": 80},
        {"serie": "COL-B", "modelo": "COL-B 5 kVA", "kva": 5.0, "amp": 40},
        {"serie": "COL-B", "modelo": "COL-B 10 kVA", "kva": 10.0, "amp": 80},
    ],
    "220V Monofásico (L1 + L2)": [
        {"serie": "COL115", "modelo": "COL115 5 kVA", "kva": 5.0, "amp": 21},
        {"serie": "COL115", "modelo": "COL115 10 kVA", "kva": 10.0, "amp": 43},
        {"serie": "COL115", "modelo": "COL115 20 kVA", "kva": 20.0, "amp": 86},
    ],
    "Bifásico 120/208V": [
        {"serie": "TND/S", "modelo": "TND/S 10 kVA", "kva": 10.0, "amp": 40},
        {"serie": "TND/S", "modelo": "TND/S 30 kVA", "kva": 30.0, "amp": 120},
        {"serie": "TND/S", "modelo": "TND/S 50 kVA", "kva": 50.0, "amp": 200},
    ],
    "Trifásico 120/208V": [
        {"serie": "TNSA-U", "modelo": "TNSA-U 30 kVA", "kva": 30.0, "amp": 75},
        {"serie": "TNSA-U", "modelo": "TNSA-U 50 kVA", "kva": 50.0, "amp": 130},
        {"serie": "TNSA-U", "modelo": "TNSA-U 100 kVA", "kva": 100.0, "amp": 260},
        {"serie": "TNSA-U", "modelo": "TNSA-U 150 kVA", "kva": 150.0, "amp": 390},
        {"serie": "TNSA-U", "modelo": "TNSA-U 200 kVA", "kva": 200.0, "amp": 520},
    ],
    "Trifásico 277/480V": [
        {"serie": "TNSB-U", "modelo": "TNSB-U 100 kVA", "kva": 100.0, "amp": 110},
        {"serie": "TNSB-U", "modelo": "TNSB-U 150 kVA", "kva": 150.0, "amp": 165},
        {"serie": "TNSB-U", "modelo": "TNSB-U 200 kVA", "kva": 220.0, "amp": 220},
    ]
}

# --- FUNCIONES DE INTERPOLACIÓN DE CURVAS ---
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

# --- SIDEBAR: PARÁMETROS DE RED ---
st.sidebar.header("⚙️ Parámetros de Red")
sistema_sel = st.sidebar.selectbox("Configuración de Red", list(CATALOGO_NIKI.keys()))

voltajes_def = {
    "Monofásico 120V": (120, 60, 150),
    "220V Monofásico (L1 + L2)": (220, 40, 280),
    "Bifásico 120/208V": (208, 130, 240),
    "Trifásico 120/208V": (208, 130, 240),
    "Trifásico 277/480V": (480, 300, 650)
}

v_nom, v_min_lim, v_max_lim = voltajes_def[sistema_sel]
v_medido = st.sidebar.number_input("Voltaje Mínimo Medido (V)", min_value=v_min_lim, max_value=v_max_lim, value=v_nom)
margen_reserva = st.sidebar.slider("Margen de Reserva (%)", min_value=0, max_value=50, value=25, step=5)

# --- PANEL DE SELECCIÓN Y EDICIÓN COMPLETA DE CARGAS ---
st.subheader("📋 Levantamiento y Edición de Cargas")
st.caption("💡 Puedes hacer doble clic sobre cualquier campo de la tabla para editar el nombre, la cantidad, la potencia o el factor de potencia directamente.")

# Inicialización del DataFrame en session_state
if "tabla_cargas" not in st.session_state:
    st.session_state.tabla_cargas = pd.DataFrame([
        {"Descripción": "Aire Acondicionado 18,000 BTU", "Cantidad": 1, "Potencia": 1.80, "Unidad": "kW", "FP": 0.85},
        {"Descripción": "Iluminación LED General", "Cantidad": 1, "Potencia": 0.30, "Unidad": "kW", "FP": 0.95}
    ])

# Selector para agregar equipos desde la librería
col_sel, col_cant, col_btn = st.columns([3, 1, 1])

with col_sel:
    equipo_nuevo = st.selectbox("Seleccionar equipo de la librería:", list(EQUIPOS_PREDETERMINADOS.keys()))

with col_cant:
    cant_nueva = st.number_input("Cantidad:", min_value=1, value=1, step=1)

with col_btn:
    st.write("")
    st.write("")
    if st.button("➕ Agregar a la Tabla", use_container_width=True):
        datos_eq = EQUIPOS_PREDETERMINADOS[equipo_nuevo]
        nueva_fila = pd.DataFrame([{
            "Descripción": equipo_nuevo,
            "Cantidad": cant_nueva,
            "Potencia": datos_eq["potencia"],
            "Unidad": datos_eq["unidad"],
            "FP": datos_eq["fp"]
        }])
        st.session_state.tabla_cargas = pd.concat([st.session_state.tabla_cargas, nueva_fila], ignore_index=True)
        st.rerun()

# Tabla interactiva totalmente modificable
cargas_editadas = st.data_editor(
    st.session_state.tabla_cargas,
    num_rows="dynamic",
    key="editor_cargas",
    column_config={
        "Descripción": st.column_config.TextColumn("Equipo / Circuito (Editable)", help="Haz doble clic para cambiar el nombre"),
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, default=1),
        "Potencia": st.column_config.NumberColumn("Potencia Unitaria", min_value=0.01, step=0.1, default=1.0, format="%.2f"),
        "Unidad": st.column_config.SelectboxColumn("Unidad", options=["kVA", "kW"], default="kVA"),
        "FP": st.column_config.NumberColumn("Factor de Potencia (FP)", min_value=0.5, max_value=1.0, step=0.05, default=0.8, format="%.2f")
    },
    use_container_width=True
)

st.session_state.tabla_cargas = cargas_editadas

# --- CÁLCULO DE POTENCIA APARENTE TOTAL ---
total_kva_carga = 0.0
for _, row in cargas_editadas.iterrows():
    cant = row.get("Cantidad", 1)
    pot = row.get("Potencia", 0.0)
    unidad = row.get("Unidad", "kVA")
    fp = row.get("FP", 0.8)
    total_kva_carga += (pot / fp if unidad == "kW" and fp > 0 else pot) * cant

f_desc = obtener_factor_desclasificacion(sistema_sel, v_medido)
f_res = 1.0 + (margen_reserva / 100.0)
kva_objetivo = (total_kva_carga * f_res) / f_desc if f_desc > 0 else 0.0

# --- MÉTRICAS DE RESUMEN ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Carga Instalada Directa", f"{total_kva_carga:.2f} kVA")
c2.metric("Margen Aplicado", f"+{margen_reserva}%")
c3.metric("Factor Desclasificación", f"{f_desc * 100:.1f}%")
c4.metric("Demanda Objetivo Niki", f"{kva_objetivo:.2f} kVA")

st.divider()

# --- RECOMENDACIÓN DE EQUIPOS NIKI ---
st.subheader("🎯 Selección de Estabilizador Niki")

if f_desc == 0.0:
    st.error(f"❌ Tensión fuera de rango operativo seguro ({v_medido}V).")
else:
    cat = CATALOGO_NIKI[sistema_sel]
    aptos = [m for m in cat if m["kva"] >= kva_objetivo]
    aptos_filtrados = [m for m in aptos if m["kva"] <= (kva_objetivo * 2.5)]
    if not aptos_filtrados and aptos:
        aptos_filtrados = [aptos[0]]

    if aptos_filtrados:
        modelo_optimo = aptos_filtrados[0]
        cap_efectiva_opt = modelo_optimo["kva"] * f_desc
        pct_opt = (total_kva_carga / cap_efectiva_opt) * 100
        estado_opt, color_opt = evaluar_estado_carga(pct_opt)

        col_opt, col_exp = st.columns(2)

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
                <p>La carga ajustada de <b>{kva_objetivo:.2f} kVA</b> supera el modelo individual más grande.</p>
            </div>
        """, unsafe_allow_html=True)

    st.subheader("📊 Matriz de Evaluación de la Serie")
    df_eval = pd.DataFrame(cat)
    df_eval["Capacidad Efectiva (kVA)"] = df_eval["kva"] * f_desc
    df_eval["Carga (%)"] = (total_kva_carga / df_eval["Capacidad Efectiva (kVA)"]) * 100
    df_eval["Evaluación"] = df_eval["kva"].apply(lambda x: "✅ Apto" if x >= kva_objetivo else "❌ Insuficiente")
    st.dataframe(df_eval[["serie", "modelo", "kva", "amp", "Capacidad Efectiva (kVA)", "Carga (%)", "Evaluación"]], use_container_width=True)