# Evaluador Automatico NIST e ISO 27001

Prototipo funcional para materializar el evaluador automatico de ciberseguridad para PYMES definido en la tesis. La evaluacion se basa en los criterios seleccionados del Apendice A: NIST CSF 2.0 e ISO/IEC 27001.

## Funciones incluidas

- Inicio de sesion.
- Registro de empresas evaluadas.
- Perfil de empresa con sector, cantidad de empleados y auditor responsable.
- Dashboard con total de evaluaciones, alineacion NIST, cumplimiento interno ISO, brechas criticas y criterios sin evidencia.
- Creacion de evaluaciones por empresa, fecha y auditor.
- Seleccion del marco evaluado: NIST CSF 2.0, ISO/IEC 27001 o ambos.
- Catalogo persistente de criterios en SQLite, sembrado desde las matrices del Apendice A.
- Cuestionario con 35 criterios:
  - NIST CSF 2.0: N-01 a N-12, organizado en Govern, Identify, Protect, Detect, Respond y Recover.
  - ISO/IEC 27001: I-01 a I-23, organizado por las areas definidas en la matriz de la tesis.
- Registro de evidencias mediante observaciones y archivos adjuntos.
- Calculo automatico con valores: cumple 100, cumple parcialmente 50, no cumple 0 y no aplica excluido del calculo.
- Calculo separado de alineacion NIST y cumplimiento interno ISO. Si se seleccionan ambos referentes, se evalua en una misma evaluacion, pero los resultados se mantienen separados.
- Indicadores de brechas criticas, controles cumplidos y controles pendientes.
- Distribucion de respuestas y principales oportunidades de mejora.
- Reporte PDF con resumen, evidencias, brechas y recomendaciones.

## Credenciales demo

- Usuario: `admin`
- Contrasena: `admin123`
- Usuario de consulta: `profesor`
- Contrasena: `tesis2026`
- Usuario empresa: `empresa`
- Contrasena: `empresa2026`

## Permisos

- Auditor: puede registrar empresas, crear evaluaciones, adjuntar evidencias, consultar dashboard y generar reportes.
- Empresa: puede responder evaluaciones y cargar evidencias.
- Revisor: puede consultar dashboard, resultados y reportes. No puede registrar empresas, crear evaluaciones ni subir evidencias.

## Ejecutar backend

```powershell
cd backend
python app.py
```

API disponible en:

```text
http://127.0.0.1:5000
```

## Ejecutar frontend

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

Aplicacion disponible en:

```text
http://127.0.0.1:5173
```

## Subir a Render

La forma recomendada para esta tesis es subir todo como una sola aplicacion en Render usando Docker. El contenedor compila React, instala Flask y publica la web completa desde una unica URL.

1. Crea una cuenta en GitHub y un repositorio nuevo.
2. Sube esta carpeta completa al repositorio.
3. Entra a Render y selecciona New > Web Service.
4. Conecta tu repositorio de GitHub.
5. Render detectara el `Dockerfile`. Si pregunta el entorno, selecciona Docker.
6. Usa el plan Free para la demostracion academica.
7. Presiona Deploy.

Cuando termine, Render entregara una URL parecida a:

```text
https://evaluador-nist-iso.onrender.com
```

Nota: en el plan gratuito, SQLite y los archivos subidos pueden reiniciarse cuando el servicio se redepliega o se recrea. Para una entrega academica funciona bien como demostracion. Para una version real se recomienda usar PostgreSQL o un disco persistente.

## Sustentacion

Este MVP materializa la propuesta conceptual del evaluador automatico. El sistema demuestra el flujo principal: autenticacion, registro de empresa, seleccion del referente, cuestionario basado en criterios N-XX/I-XX, adjunto de evidencias, calculo ponderado, identificacion de brechas, dashboard y generacion de reporte ejecutivo en PDF.

Los resultados de NIST representan alineacion interna con los criterios evaluados. Los resultados de ISO representan cumplimiento interno de los criterios seleccionados. Ningun porcentaje constituye certificacion oficial.
