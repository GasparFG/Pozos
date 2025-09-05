import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import calendar

st.set_page_config(page_title="Producción | Vista rápida", layout="wide")

# Estado
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False
if "df" not in st.session_state:
    st.session_state.df = None

st.title("Carga de Excel y vista rápida")
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols_low = {c.lower(): c for c in df.columns}
    rename_map = {}
    for key in ["date", "fecha", "fechas"]:
        if key in cols_low: rename_map[cols_low[key]] = "date"; break
    for key in ["well", "pozo", "wells", "pozos"]:
        if key in cols_low: rename_map[cols_low[key]] = "well"; break
    for key in ["oil bbl", "oil", "petróleo", "petroleo"]:
        if key in cols_low: rename_map[cols_low[key]] = "Oil"; break
    for key in ["water bbl", "water", "agua"]:
        if key in cols_low: rename_map[cols_low[key]] = "Water"; break
    for key in ["gas mcf", "gas"]:
        if key in cols_low: rename_map[cols_low[key]] = "Gas"; break
    return df.rename(columns=rename_map)

def _to_datetime_safe(s: pd.Series):
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
    return dt.mask(~dt.dt.year.between(1900, 2100))

def preparar_mensual(df):
    df = df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["period"] = pd.to_datetime(df[["year","month"]].assign(day=1))
    agg_cols = [c for c in ["Oil","Water","Gas"] if c in df.columns]
    df_month = df.groupby(["period","well"], as_index=False)[agg_cols].sum()
    df_month["days_in_month"] = df_month["period"].dt.days_in_month
    for col in agg_cols:
        df_month[col] = df_month[col] / df_month["days_in_month"]
    return df_month

def calcular_metricas(df, var, unidad_q, unidad_v, include_qoi=False):
    if df.empty or var not in df.columns:
        return pd.DataFrame()
    serie = df[var].dropna()
    if serie.empty:
        return pd.DataFrame()
    # Producción acumulada (V)
    prod_acum = (serie * df["period"].dt.days_in_month).sum()
    # Meses totales
    total_meses = (df["period"].max().year - df["period"].min().year) * 12 + (
        df["period"].max().month - df["period"].min().month
    ) + 1
    # Promedio Diario Mensual (Q)
    promedio_q = serie.mean()
    # Qoi (primer mes o promedio de pozos)
    qoi = None
    if include_qoi == "pozo":
        qoi = serie.iloc[0]
    elif include_qoi == "fluido":
        qoi = serie.groupby(df["well"]).first().mean()
    max_val, max_fecha = serie.max(), df.loc[serie.idxmax(), "period"]
    min_val, min_fecha = serie.min(), df.loc[serie.idxmin(), "period"]
    std = serie.std()
    fecha_inicio = df["period"].min()
    fecha_final = df["period"].max()
    def fmt_num(x):
        if pd.isnull(x): return "-"
        if float(x).is_integer(): return f"{int(x):,}"
        return f"{x:,.3f}".rstrip("0").rstrip(".")
    def fmt_fecha(x):
        return x.strftime("%Y-%m") if pd.notnull(x) else "-"
    metricas = [
        ("Promedio Diario Mensual (Q)", fmt_num(promedio_q), unidad_q),
        ("Qoi – Ritmo de producción inicial", fmt_num(qoi), unidad_q),
        ("Máximo", fmt_num(max_val), unidad_q),
        ("Fecha máximo", fmt_fecha(max_fecha), ""),
        ("Mínimo", fmt_num(min_val), unidad_q),
        ("Fecha mínimo", fmt_fecha(min_fecha), ""),
        ("Desviación estándar (Q)", fmt_num(std), unidad_q),
        ("Duración del rango (meses)", fmt_num(total_meses), "meses"),
        ("Producción acumulada (V)", fmt_num(prod_acum), unidad_v),
        ("Fecha inicio de producción", fmt_fecha(fecha_inicio), ""),
        ("Fecha fin de producción", fmt_fecha(fecha_final), "")
    ]
    return pd.DataFrame(metricas, columns=["Métrica", "Valor", "Unidad"])

# Paso 1: subir archivo
if uploaded_file is not None and not st.session_state.confirmed:
    df_raw = pd.read_excel(uploaded_file)
    df = _normalize_columns(df_raw.copy())
    df["date"] = _to_datetime_safe(df["date"])
    df = df.dropna(subset=["date"]).sort_values("date")
    st.session_state.df = df
    st.subheader("Vista previa (primeras 5 filas)")
    st.dataframe(df.head(5))
    st.info("Verifica columnas: 'date', 'well', 'Oil', 'Water', 'Gas'.")
    if st.button("Confirmar y ver gráficas"):
        st.session_state.confirmed = True
        st.rerun()

# Paso 2: análisis
if st.session_state.confirmed:
    df = st.session_state.df.copy()
    df_month = preparar_mensual(df)
    # --- Filtros ---
    st.subheader("Selecciona pozos")
    pozos = sorted(df_month["well"].dropna().unique().tolist())
    if "pozos_sel" not in st.session_state:
        st.session_state["pozos_sel"] = pozos
    pozos_sel = st.multiselect("Pozos", options=pozos, default=st.session_state["pozos_sel"])
    st.session_state["pozos_sel"] = pozos_sel
    if st.button("Seleccionar/Quitar todos los pozos"):
        if set(st.session_state["pozos_sel"]) == set(pozos):
            st.session_state["pozos_sel"] = []
        else:
            st.session_state["pozos_sel"] = pozos
        st.rerun()
    df_filt_base = df_month[df_month["well"].isin(st.session_state["pozos_sel"])]
    if df_filt_base.empty:
        st.warning("No hay datos para los pozos seleccionados.")
        st.stop()
    # Rango fechas
    st.subheader("Rango de fechas")
    min_ts, max_ts = df_filt_base["period"].min().to_pydatetime(), df_filt_base["period"].max().to_pydatetime()
    if "fecha_range" not in st.session_state:
        st.session_state["fecha_range"] = (min_ts, max_ts)
    else:
        start_dt, end_dt = st.session_state["fecha_range"]
        if start_dt < min_ts or end_dt > max_ts:
            st.session_state["fecha_range"] = (min_ts, max_ts)
    start_dt, end_dt = st.slider(
        "Selecciona rango de fechas",
        min_value=min_ts,
        max_value=max_ts,
        value=st.session_state["fecha_range"],
        format="YYYY-MM",
        key="date_range_slider",
    )
    st.session_state["fecha_range"] = (start_dt, end_dt)
    if st.button("Reiniciar fecha"):
        st.session_state["fecha_range"] = (min_ts, max_ts)
        st.rerun()
    df_filt = df_filt_base[(df_filt_base["period"] >= start_dt) & (df_filt_base["period"] <= end_dt)]
    # --- Pestañas ---
    vars_ok = [c for c in ["Oil", "Gas", "Water"] if c in df_filt.columns]
    tabs = st.tabs(["Producción Total"] + vars_ok + ["Pozos"])
    # Producción Total
    with tabs[0]:
        st.subheader("Producción Total (Oil, Gas, Water)")
        df_total = {}
        for var in ["Oil", "Gas", "Water"]:
            if var in df_filt.columns:
                df_tmp = df_filt.groupby("period", as_index=False)[var].sum()
                df_tmp["V_acum"] = (df_tmp[var] * df_tmp["period"].dt.days_in_month).cumsum()
                df_tmp["Q"] = df_tmp[var]
                df_tmp["fluido"] = var
                df_total[var] = df_tmp
        df_total_all = pd.concat(df_total.values(), ignore_index=True)
        colores = {"Oil": "black", "Gas": "green", "Water": "blue"}
        chart_q = (
            alt.Chart(df_total_all)
            .mark_line()
            .encode(
                x="period:T",
                y=alt.Y("Q:Q", title="Q"),
                color=alt.Color("fluido:N", scale=alt.Scale(domain=list(colores.keys()), range=list(colores.values())),
                                legend=alt.Legend(orient="bottom")),
                strokeDash=alt.value([1,0])
            )
        )
        chart_v = (
            alt.Chart(df_total_all)
            .mark_line()
            .encode(
                x="period:T",
                y=alt.Y("V_acum:Q", title="V acumulado"),
                color=alt.Color("fluido:N", scale=alt.Scale(domain=list(colores.keys()), range=list(colores.values())),
                                legend=alt.Legend(orient="bottom")),
                strokeDash=alt.value([4,2])
            )
        )
        chart_total = alt.layer(chart_q, chart_v).resolve_scale(y="independent")
        st.altair_chart(chart_total, use_container_width=True)
    # Oil, Gas, Water
    for i, var in enumerate(vars_ok, start=1):
        with tabs[i]:
            st.subheader(f"{var} por fecha y pozo")
            chart_type = st.radio("Tipo de gráfica", ["Líneas", "Área apilada (valores)"], horizontal=True, key=f"chart_type_{var}")
            if chart_type == "Líneas":
                chart_pozos = (
                    alt.Chart(df_filt)
                    .mark_line()
                    .encode(
                        x=alt.X("period:T", title="Fecha"),
                        y=alt.Y(f"{var}:Q", title=f"{var} (Q)"),
                        color=alt.Color("well:N", title="Pozo", legend=alt.Legend(orient="bottom", columns=5)),
                        tooltip=["period:T", "well:N", alt.Tooltip(f"{var}:Q", format=",.2f")]
                    )
                )
                df_avg = df_filt.groupby("period", as_index=False)[var].mean()
                df_avg["well"] = "PROMEDIO"
                chart_avg = alt.Chart(df_avg).mark_line(strokeDash=[4,2], color="black", strokeWidth=2).encode(x="period:T", y=alt.Y(f"{var}:Q"))
                chart = alt.layer(chart_pozos, chart_avg)
            else:
                chart = (
                    alt.Chart(df_filt)
                    .mark_area(opacity=0.8)
                    .encode(
                        x=alt.X("period:T", title="Fecha"),
                        y=alt.Y(f"{var}:Q", stack="zero", title=f"{var} (Q)"),
                        color=alt.Color("well:N", title="Pozo", legend=alt.Legend(orient="bottom", columns=5)),
                        tooltip=["period:T", "well:N", alt.Tooltip(f"{var}:Q", format=",.2f")]
                    )
                )
            st.altair_chart(chart.properties(height=350).interactive(), use_container_width=True)
            unidad_q = "BPD" if var in ["Oil","Water"] else "MCFD"
            unidad_v = "BBL" if var in ["Oil","Water"] else "MCF"
            st.subheader("Métricas descriptivas")
            met = calcular_metricas(df_filt, var, unidad_q, unidad_v, include_qoi="fluido")
            st.dataframe(met)
            # Total por fluido
            st.subheader(f"TOTAL {var.upper()}")
            df_var = df_filt.groupby("period", as_index=False)[var].sum()
            df_var["V_acum"] = (df_var[var] * df_var["period"].dt.days_in_month).cumsum()
            df_var["Q"] = df_var[var]
            base = alt.Chart(df_var).encode(x="period:T")
            line_q = base.mark_line(color="blue").encode(y=alt.Y("Q:Q", title="Q"))
            line_v = base.mark_line(color="red", strokeDash=[4,2]).encode(y=alt.Y("V_acum:Q", title="V acumulado"))
            chart_total_var = alt.layer(line_q, line_v).resolve_scale(y="independent")
            st.altair_chart(chart_total_var, use_container_width=True)
    # Pozos
    with tabs[-1]:
        st.subheader("Métricas por pozo (Q)")
        unidad_q = "BPD" if "Oil" in vars_ok else "MCFD"
        unidad_v = "BBL" if "Oil" in vars_ok else "MCF"
        cols = st.columns(3)
        for i, pozo in enumerate(sorted(df_filt["well"].unique())):
            df_p = df_filt[df_filt["well"] == pozo]
            met = calcular_metricas(df_p, vars_ok[0], unidad_q, unidad_v, include_qoi="pozo")
            with cols[i % 3]:
                st.markdown(f"### {pozo}")
                st.table(met)
    if st.button("Reiniciar y subir otro archivo"):
        st.session_state.clear()
        st.rerun()


## cd "C:\Users\gfg30\OneDrive\Desktop\Phyton Projects\Prediccion_de_produccion"
 
# streamlit run app.py
