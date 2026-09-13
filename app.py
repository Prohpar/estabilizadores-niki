import streamlit as st
import pandas as pd
import math

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
st.markdown("Dimensionamiento de capacidad aparente ($kVA$) con asignación de fases ($L1, L2, L3$), balanceo de líneas y motores NEC (NFPA 70).")

# --- TABLAS DE CORRIENTE NOMINAL DE MOTORES DE INDUCCIÓN (NEC) ---
MOTORES_NEC = {
    "Monofásico 120V": {"0.5 HP": 9.8, "0.75 HP": 13.8, "1.0 HP": 16.0, "1.5 HP": 20.0, "2.0 HP": 24.0, "3.0 HP": 34.0, "5.0 HP": 56.0},
    "Monofásico 220V": {"0.5 HP": 4.9, "0.75 HP": 6.9, "1.0 HP": 8.0, "1.5 HP": 10.0, "2.0 HP": 12.0, "3.0 HP": 17.0, "5.0 HP": 28.0, "7.5 HP": 40.0, "10.0 HP": 50.0},
    "Trifásico 220V": {"0.5 HP": 2.2, "0.75 HP": 3.2, "1.0 HP": 4.2, "1.5 HP": 6.0, "2.0 HP": 6.8, "3.0 HP": 9.6, "5.0 HP": 15.2, "7.5 HP": 22.0, "10.0 HP": 28.0, "15.0 HP": 42.0, "20.0 HP": 54.0, "25.0 HP": 68.0, "30.0 HP": 80.0, "40.0 HP": 104.0, "50.0 HP": 130.0, "75.0 HP": 192.0, "100.0 HP": 248.0},
    "Trifásico 480V": {"0.5 HP": 1.1, "0.75 HP": 1.6, "1.0 HP": 2.1, "1.5 HP": 3.0, "2.0 HP": 3.4, "3.0 HP": 4.8, "5.0 HP": 7.6, "7.5 HP": 11.0, "10.0 HP": 14.0, "15.0 HP": 21.0, "20.0 HP": 27.0, "25.0 HP": 34.0, "30.0 HP": 40.0, "40.0 HP": 52.0, "50.0 HP": 65.0, "75.0 HP": 96.0, "100.0 HP": 124.0}
}

DATOS_SISTEMA_VOLTAJE = {
    "Monofásico 120V": {"v_ln": 120, "v_ll": 120, "fases": 1},
    "220V Monofásico (L1 + L2)": {"v_ln": 110, "v_ll": 220, "fases": 1},
    "Bifásico 120/208V": {"v_ln": 120, "v_ll": 208, "fases": 2},
    "Trifásico 120/208V": {"v_ln": 120, "v_ll": 208, "fases": 3},
    "Trifásico 277/480V": {"v_ln": 277, "v_ll": 480, "fases": 3}
}

EQUIPOS_PREDETERMINADOS = {
    "Iluminación LED General": {"valor": 0.30, "unidad": "kW", "fases": "Monofásica", "fp": 0.95},
    "Puesto de Trabajo (PC + Monitores)": {"valor": 0.50, "unidad": "kVA", "fases": "Monofásica", "fp": 0.90},
    "Servidor / Rack IT": {"valor": 2.00, "unidad": "kVA", "fases": "Monofásica", "fp": 0.95},
    "Microondas / Horno Eléctrico": {"valor": 1.20, "unidad": "kW", "fases": "Monofásica", "fp": 0.95},
    "Carga General Personalizada": {"valor": 1.00, "unidad": "kVA", "fases": "Monofásica", "fp": 0.80}
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
    if pct_carga > 90: return "⚠️ Carga Crítica (>90%)", "#EF4444"
    elif 60 <= pct_carga <= 85: return "✅ Carga Óptima (60-85%)", "#10B981"
    elif pct_carga < 50: return "ℹ️ Carga Ligera (<50%)", "#3B82F6"
    else: return "👍 Carga Aceptable", "#F59E0B"

# --- SIDEBAR: CONFIGURACIÓN DE RED ---
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

# --- INICIALIZACIÓN DE TABLA VACÍA ---
if "tabla_cargas" not in st.session_state:
    st.session_state.tabla_cargas = pd.DataFrame(columns=[
        "Descripción", "Cantidad", "Valor", "Unidad", "Fases Carga", "Línea / Asignación", "FP"
    ])

# --- INGRESO DE CARGAS ---
st.subheader("📋 Levantamiento de Cargas")
tab_motores, tab_cargas_gen = st.tabs(["⚙️ Motores Industriales (Norma NEC)", "🔌 Cargas Generales"])

with tab_motores:
    col_tipo_m, col_hp_m, col_cant_m, col_btn_m = st.columns([2.5, 2, 1, 1.5])
    with col_tipo_m: tipo_motor_sel = st.selectbox("Configuración de Motor:", list(MOTORES_NEC.keys()))
    with col_hp_m: hp_sel = st.selectbox("Potencia Nominal (HP):", list(MOTORES_NEC[tipo_motor_sel].keys()))
    with col_cant_m: cant_m = st.number_input("Cantidad:", min_value=1, value=1, step=1, key="cant_m_in")
    with col_btn_m:
        st.write(""); st.write("")
        if st.button("➕ Agregar Motor", use_container_width=True):
            amp_nec = MOTORES_NEC[tipo_motor_sel][hp_sel]
            fases_eq = "Trifásica" if "Trifásico" in tipo_motor_sel else "Monofásica"
            nueva_fila = pd.DataFrame([{
                "Descripción": f"Motor {hp_sel} ({tipo_motor_sel})",
                "Cantidad": cant_m,
                "Valor": amp_nec,
                "Unidad": "A",
                "Fases Carga": fases_eq,
                "Línea / Asignación": "Auto / Balanceada",
                "FP": 0.80
            }])
            st.session_state.tabla_cargas = pd.concat([st.session_state.tabla_cargas, nueva_fila], ignore_index=True)
            st.rerun()

with tab_cargas_gen:
    col_sel_g, col_cant_g, col_btn_g = st.columns([3, 1, 1.5])
    with col_sel_g: equipo_nuevo = st.selectbox("Librería de cargas generales:", list(EQUIPOS_PREDETERMINADOS.keys()))
    with col_cant_g: cant_nueva = st.number_input("Cantidad:", min_value=1, value=1, step=1, key="cant_g_in")
    with col_btn_g:
        st.write(""); st.write("")
        if st.button("➕ Agregar Carga", use_container_width=True):
            datos_eq = EQUIPOS_PREDETERMINADOS[equipo_nuevo]
            nueva_fila = pd.DataFrame([{
                "Descripción": equipo_nuevo,
                "Cantidad": cant_nueva,
                "Valor": datos_eq["valor"],
                "Unidad": datos_eq["unidad"],
                "Fases Carga": datos_eq["fases"],
                "Línea / Asignación": "Auto / Balanceada",
                "FP": datos_eq["fp"]
            }])
            st.session_state.tabla_cargas = pd.concat([st.session_state.tabla_cargas, nueva_fila], ignore_index=True)
            st.rerun()

st.divider()

# --- TABLA INTERACTIVA ---
col_head, col_vaciar = st.columns([4, 1])
with col_head: st.subheader("📑 Cuadro de Cargas y Distribución de Fases")
with col_vaciar:
    if st.button("🗑️ Vaciar Tabla", use_container_width=True):
        st.session_state.tabla_cargas = pd.DataFrame(columns=["Descripción", "Cantidad", "Valor", "Unidad", "Fases Carga", "Línea / Asignación", "FP"])
        st.rerun()

cargas_editadas = st.data_editor(
    st.session_state.tabla_cargas,
    num_rows="dynamic",
    column_config={
        "Descripción": st.column_config.TextColumn("Equipo / Motor / Circuito"),
        "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=1, step=1, default=1),
        "Valor": st.column_config.NumberColumn("Valor", min_value=0.01, step=0.1, default=1.0, format="%.2f"),
        "Unidad": st.column_config.SelectboxColumn("Unidad", options=["A", "kW", "kVA"], default="A"),
        "Fases Carga": st.column_config.SelectboxColumn("Fases del Equipo", options=["Monofásica", "Bifásica", "Trifásica"], default="Monofásica"),
        "Línea / Asignación": st.column_config.SelectboxColumn("Línea Conectada", options=["Auto / Balanceada", "L1", "L2", "L3"], default="Auto / Balanceada"),
        "FP": st.column_config.NumberColumn("FP", min_value=0.5, max_value=1.0, step=0.05, default=0.8, format="%.2f")
    },
    use_container_width=True
)

st.session_state.tabla_cargas = cargas_editadas

# --- MOTOR DE CÁLCULO Y BALANCEO DE FASES ---
v_info = DATOS_SISTEMA_VOLTAJE[sistema_sel]
num_fases_red = v_info["fases"]

kva_l1, kva_l2, kva_l3 = 0.0, 0.0, 0.0
total_kva_directo = 0.0

for _, row in cargas_editadas.iterrows():
    cant = row.get("Cantidad", 1)
    val = row.get("Valor", 0.0)
    unidad = row.get("Unidad", "A")
    fases_carga = row.get("Fases Carga", "Monofásica")
    asig_linea = row.get("Línea / Asignación", "Auto / Balanceada")
    fp = row.get("FP", 0.8)

    # Convertir valor unitario a kVA
    if unidad == "kVA": kva_unitario = val
    elif unidad == "kW": kva_unitario = (val / fp) if fp > 0 else val
    elif unidad == "A":
        if fases_carga == "Monofásica":
            v_calc = v_info["v_ln"] if sistema_sel != "220V Monofásico (L1 + L2)" else v_info["v_ll"]
            kva_unitario = (v_calc * val) / 1000.0
        elif fases_carga == "Bifásica": kva_unitario = (v_info["v_ll"] * val) / 1000.0
        elif fases_carga == "Trifásica": kva_unitario = (math.sqrt(3) * v_info["v_ll"] * val) / 1000.0
        else: kva_unitario = (v_info["v_ll"] * val) / 1000.0

    kva_total_item = kva_unitario * cant
    total_kva_directo += kva_total_item

    # Distribución por fase crítica
    if num_fases_red == 1:
        kva_l1 += kva_total_item
    elif num_fases_red == 2:
        if asig_linea == "L1": kva_l1 += kva_total_item
        elif asig_linea == "L2": kva_l2 += kva_total_item
        else:
            # Auto / Balanceada con factor 1.15
            por_fase = (kva_total_item / 2.0) * 1.15
            kva_l1 += por_fase; kva_l2 += por_fase
    elif num_fases_red == 3:
        if asig_linea == "L1": kva_l1 += kva_total_item
        elif asig_linea == "L2": kva_l2 += kva_total_item
        elif asig_linea == "L3": kva_l3 += kva_total_item
        else:
            # Auto / Balanceada con factor 1.15
            por_fase = (kva_total_item / 3.0) * 1.15
            kva_l1 += por_fase; kva_l2 += por_fase; kva_l3 += por_fase

# Determinar fase crítica y kVA equivalente
if num_fases_red == 1:
    fase_critica_kva = kva_l1
    total_kva_equivalente = kva_l1
elif num_fases_red == 2:
    fase_critica_kva = max(kva_l1, kva_l2)
    total_kva_equivalente = 2.0 * fase_critica_kva
else:
    fase_critica_kva = max(kva_l1, kva_l2, kva_l3)
    total_kva_equivalente = 3.0 * fase_critica_kva

f_desc = obtener_factor_desclasificacion(sistema_sel, v_medido)
f_res = 1.0 + (margen_reserva / 100.0)
kva_objetivo = (total_kva_equivalente * f_res) / f_desc if f_desc > 0 else 0.0

# --- MÉTRICAS DE RESUMEN Y ESTADO DE BALANCEO ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Carga Instalada Directa", f"{total_kva_directo:.2f} kVA")
c2.metric("Demanda Balanceada Equiv.", f"{total_kva_equivalente:.2f} kVA")
c3.metric("Factor Desclasificación", f"{f_desc * 100:.1f}%")
c4.metric("Demanda Objetivo Niki", f"{kva_objetivo:.2f} kVA")

# Alerta de desbalance
if num_fases_red > 1 and total_kva_directo > 0:
    lineas_vals = [kva_l1, kva_l2] if num_fases_red == 2 else [kva_l1, kva_l2, kva_l3]
    val_max, val_min = max(lineas_vals), min(lineas_vals)
    pct_desbalance = ((val_max - val_min) / val_max * 100) if val_max > 0 else 0

    st.markdown(f"**Distribución de Carga por Fase:** L1 = `{kva_l1:.2f} kVA` | L2 = `{kva_l2:.2f} kVA`" + (f" | L3 = `{kva_l3:.2f} kVA`" if num_fases_red == 3 else ""))
    
    if pct_desbalance > 20:
        st.warning(f"⚠️ **Desbalance de fases detectado ({pct_desbalance:.1f}%):** La línea crítica requiere que el estabilizador se dimensione a **{total_kva_equivalente:.2f} kVA** para evitar disparos por sobrecorriente. Considera redistribuir los circuitos en el tablero.")

st.divider()

# --- RECOMENDACIÓN DE MODELO NIKI ---
st.subheader("🎯 Selección de Estabilizador Niki")

if total_kva_directo == 0.0:
    st.info("💡 La lista de cargas está vacía. Selecciona un motor o carga general arriba para realizar el cálculo.")
elif f_desc == 0.0:
    st.error(f"❌ Tensión fuera de rango operativo seguro ({v_medido}V).")
else:
    cat = CATALOGO_NIKI[sistema_sel]
    aptos = [m for m in cat if m["kva"] >= kva_objetivo]
    aptos_filtrados = [m for m in aptos if m["kva"] <= (kva_objetivo * 2.5)]
    if not aptos_filtrados and aptos: aptos_filtrados = [aptos[0]]

    if aptos_filtrados:
        modelo_optimo = aptos_filtrados[0]
        cap_efectiva_opt = modelo_optimo["kva"] * f_desc
        pct_opt = (total_kva_equivalente / cap_efectiva_opt) * 100 if cap_efectiva_opt > 0 else 0
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
                pct_exp = (total_kva_equivalente / cap_efectiva_exp) * 100 if cap_efectiva_exp > 0 else 0
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
    df_eval["Carga (%)"] = (total_kva_equivalente / df_eval["Capacidad Efectiva (kVA)"]) * 100 if total_kva_equivalente > 0 else 0.0
    df_eval["Evaluación"] = df_eval["kva"].apply(lambda x: "✅ Apto" if x >= kva_objetivo else "❌ Insuficiente")
    st.dataframe(df_eval[["serie", "modelo", "kva", "amp", "Capacidad Efectiva (kVA)", "Carga (%)", "Evaluación"]], use_container_width=True)