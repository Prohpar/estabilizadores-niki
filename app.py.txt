import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Seleccionador de Estabilizadores Niki",
    page_icon="⚡",
    layout="wide"
)

# Estilo personalizado CSS
st.markdown("""
    <style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    .metric-card { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 5px solid #1E3A8A; }
    .success-card { background-color: #ECFDF5; padding: 15px; border-radius: 10px; border-left: 5px solid #10B981; }
    .warning-card { background-color: #FEF3C7; padding: 15px; border-radius: 10px; border-left: 5px solid #F59E0B; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Seleccionador Técnico de Estabilizadores Niki")
st.markdown("Dimensionamiento dinámico de capacidad aparente (kVA) con desclasificación por caídas de tensión en red (*Derating Curve*).")

# --- BASE DE DATOS DEL CATÁLOGO NIKI ---
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

# --- PANEL LATERAL: CONFIGURACIÓN DE RED ---
st.sidebar.header("⚙️ Parámetros Eléctricos")

sistema_sel = st.sidebar.selectbox(
    "Sistema Eléctrico de Red",
    list(CATALOGO_NIKI.keys())
)

# Definición dinámica de límites de entrada según sistema
voltajes_def = {
    "Monofásico 120V": (120, 60, 150),
    "220V Monofásico (L1 + L2)": (220, 40, 280),
    "Bifásico 120/208V": (208, 130, 240),
    "Trifásico 120/208V": (208, 130, 240),
    "Trifásico 277/480V": (480, 300, 650)
}

v_nom, v_min_lim, v_max_lim = voltajes_def[sistema_sel]

v_medido = st.sidebar.number_input(
    f"Voltaje Mínimo Medido en Sitio (V)",
    min_value=v_min_lim,
    max_value=v_max_lim,
    value=v_nom,
    step=1
)

margen_seguridad = st.sidebar.slider(
    "Margen de Reserva Comercial (%)",
    min_value=0,
    max_value=50,
    value=25,
    step=5
)

# --- CUERPO PRINCIPAL: INGRESO DE CARGAS ---
st.subheader("📋 Levantamiento de Cargas")

if "cargas" not in st.session_state:
    st.session_state.cargas = pd.DataFrame([
        {"Descripción": "Carga General 1", "Cantidad": 1, "Potencia": 5.0, "Unidad": "kVA", "FP": 0.8},
    ])

cargas_df = st.data_editor(
    st.session_state.cargas,
    num_rows="dynamic",
    column_config={
        "Descripción": st.column_config.TextColumn("Equipo / Circuito"),
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, default=1),
        "Potencia": st.column_config.NumberColumn("Potencia Unitaria", min_value=0.1, default=1.0, format="%.2f"),
        "Unidad": st.column_config.SelectboxColumn("Unidad", options=["kVA", "kW"], default="kVA"),
        "FP": st.column_config.NumberColumn("Factor de Potencia (FP)", min_value=0.5, max_value=1.0, default=0.8, format="%.2f")
    },
    use_container_width=True
)

# --- MOTOR DE CÁLCULO ---
total_kva = 0.0
for _, row in cargas_df.iterrows():
    cant = row.get("Cantidad", 1)
    pot = row.get("Potencia", 0.0)
    unidad = row.get("Unidad", "kVA")
    fp = row.get("FP", 0.8)
    
    if unidad == "kW":
        kva_ind = (pot / fp) if fp > 0 else pot
    else:
        kva_ind = pot
    
    total_kva += kva_ind * cant

factor_desc = obtener_factor_desclasificacion(sistema_sel, v_medido)
factor_reserva = 1.0 + (margen_seguridad / 100.0)

if factor_desc > 0:
    kva_requeridos = (total_kva * factor_reserva) / factor_desc
else:
    kva_requeridos = 0.0

# --- METRICAS Y RESULTADOS ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Demanda Instalada", f"{total_kva:.2f} kVA")

with col2:
    st.metric("Margen Aplicado", f"+{margen_seguridad}%")

with col3:
    st.metric("Factor Desclasificación", f"{factor_desc * 100:.1f}%")

with col4:
    st.metric("Capacidad Mínima Niki", f"{kva_requeridos:.2f} kVA")

st.divider()

# --- SELECCIÓN Y RECOMENDACIÓN DE MODELO ---
st.subheader("🎯 Estabilizador Niki Recomendado")

if factor_desc == 0.0:
    st.error(f"❌ El voltaje medido ({v_medido}V) está fuera del rango operativo seguro para el sistema {sistema_sel}.")
else:
    modelos_disponibles = CATALOGO_NIKI[sistema_sel]
    modelos_aptos = [m for m in modelos_disponibles if m["kva"] >= kva_requeridos]

    if modelos_aptos:
        seleccionado = modelos_aptos[0]
        porcentaje_carga = (total_kva / (seleccionado["kva"] * factor_desc)) * 100

        st.markdown(f"""
            <div class="success-card">
                <h3>Modelo Sugerido: <b>{seleccionado['modelo']}</b></h3>
                <ul>
                    <li><b>Serie Comercial:</b> {seleccionado['serie']}</li>
                    <li><b>Capacidad Nominal:</b> {seleccionado['kva']} kVA ({seleccionado['kva'] * 1000:.0f} VA)</li>
                    <li><b>Corriente Nominal:</b> {seleccionado['amp']} A</li>
                    <li><b>Porcentaje de Carga Operativa a {v_medido}V:</b> {porcentaje_carga:.1f}% de su capacidad corregida</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    else:
        max_modelo = modelos_disponibles[-1]
        st.markdown(f"""
            <div class="warning-card">
                <h3>⚠️ Carga Excede Capacidad Individual</h3>
                <p>La capacidad requerida (<b>{kva_requeridos:.2f} kVA</b>) supera el modelo individual más grande de la serie ({max_modelo['modelo']}).</p>
                <p><b>Sugerencia:</b> Dividir las cargas en varios circuitos o consultar por soluciones a medida.</p>
            </div>
        """, unsafe_allow_html=True)

    # Tabla resumen del catálogo para el sistema seleccionado
    st.subheader("📊 Comparativa de Serie")
    df_cat = pd.DataFrame(modelos_disponibles)
    df_cat["Capacidad Efectiva a " + str(v_medido) + "V (kVA)"] = df_cat["kva"] * factor_desc
    df_cat["Estado"] = df_cat["kva"].apply(lambda x: "✅ Apto" if x >= kva_requeridos else "❌ Insuficiente")
    st.dataframe(df_cat, use_container_width=True)