# Laboratorio de Decisiones con IA | Portal de Estudiantes UDD

Aplicación Streamlit pública, independiente y de solo lectura.

## Ejecución local

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

El portal consume exclusivamente `data/publication.json`. No utiliza SQLite. El correo autorizado y la clave estudiantil se configuran como secretos del despliegue y nunca se incluyen en el repositorio.

## Acceso estudiantil

Configure estos valores en **Streamlit Community Cloud → App settings → Secrets** usando como referencia `.streamlit/secrets.example.toml`:

```toml
[access]
student_password = "CLAVE_DEFINIDA_POR_EL_DOCENTE"
allowed_emails = ["REEMPLAZAR_CON_CORREO_AUTORIZADO"]

[access.student_names]
"REEMPLAZAR_CON_CORREO_AUTORIZADO" = "NOMBRE DEL ESTUDIANTE"
```

No cree ni publique `.streamlit/secrets.toml`. Para una vista local sin autenticación destinada exclusivamente a revisión docente, defina temporalmente `PORTAL_PREVIEW_MODE=1`.

## Despliegue

Sube el contenido de esta carpeta a un repositorio público independiente. En Streamlit Community Cloud selecciona `app.py` como punto de entrada. Mantén el mismo repositorio y nombre de aplicación para conservar una URL estable.

Los paquetes deben generarse desde el Centro de Publicaciones del laboratorio docente. No agregues archivos del repositorio privado.
