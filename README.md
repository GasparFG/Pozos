# 📊 App de Producción Petrolera

Aplicación desarrollada en **Streamlit** para analizar datos de producción de pozos.  
Permite cargar archivos Excel y obtener una vista rápida de producción de **petróleo, agua y gas** con gráficas y métricas automáticas.
---

## 🚀 Funcionalidades

- Carga de archivos Excel (`.xlsx`, `.xls`).
- Normalización automática de columnas (`date`, `well`, `Oil`, `Water`, `Gas`).
- Filtro por pozo y rango de fechas.
- Gráficas interactivas con **Altair** (líneas y áreas apiladas).
- Cálculo de métricas descriptivas: media, máximo, mínimo, coeficiente de cambio.
- Tablas de resultados por variable y por pozo.
- Totales acumulados (Q y V).

---

## 📦 Requisitos

- **Python 3.11** o superior  
- Librerías (definidas en `requirements.txt`):
  - `streamlit`
  - `pandas`
  - `altair`
  - `numpy`
  - `openpyxl`

---

## 🛠 Instalación local

1. Clona el repositorio:
```bash
git clone https://github.com/usuario/produccion-app.git
cd produccion-app
````

2. Crea un entorno virtual:

```bash
python -m venv .venv
```

3. Activa el entorno virtual:

* Linux/Mac:

```bash
source .venv/bin/activate
```

* Windows (PowerShell):

```powershell
.venv\Scripts\activate
```

4. Instala dependencias:

```bash
pip install -r requirements.txt
```

5. Ejecuta la app:

```bash
streamlit run app.py
```

Abre el navegador en: [http://localhost:8501](http://localhost:8501)

---

## 🌐 Despliegue en Streamlit Cloud

1. Sube tu código a GitHub (asegúrate de incluir `app.py`, `requirements.txt` y `.streamlit/config.toml` si lo usas).
2. Ve a [Streamlit Cloud](https://streamlit.io/cloud) e inicia sesión con GitHub.
3. Crea una nueva app seleccionando tu repo y rama (`main`).
4. En *Main file path* escribe:

```
app.py
```

5. Haz deploy y tu app estará disponible en una URL pública tipo:

```
https://tuapp.streamlit.app
```

---

## 📊 Ejemplo de uso

1. Sube un archivo Excel con datos de pozos.
2. Verifica que las columnas se detecten correctamente.
3. Selecciona pozos y rango de fechas.
4. Explora gráficas y métricas en las pestañas de la aplicación.

---

## 👤 Autor

**Gaspar Franco**
[LinkedIn](https://www.linkedin.com/) | [Portafolio](https://tusitio.com)

---
