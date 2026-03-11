# 🔬 Bedrock Model Comparison — Lambda

Compara **Claude Haiku 4.5 vs Sonnet 4.6 vs Opus 4.6** con una sola invocación.
Mide latencia, tokens y costo real en USD.

---

## 📁 Estructura del proyecto

```
bedrock-comparison/
├── lambda_handler.py         # Código de la Lambda (copiar a la consola)
├── guia_setup_aws.py         # Guía paso a paso para configurar en AWS Console
├── requirements.txt
└── README.md
```

---

## 🚀 Despliegue (100% desde la consola de AWS)

No se usa CDK, Terraform ni ninguna herramienta de IaC.

Abre `guia_setup_aws.py` y sigue los 5 pasos:

1. **Permisos de Marketplace** para tu usuario IAM (activar modelos)
2. **Activar modelos** en Bedrock Playground (suscripción de Marketplace)
3. **Crear IAM Role** con permisos mínimos (logs + bedrock solo 3 modelos)
4. **Crear la Lambda** con Python 3.12, timeout 60s, 256 MB
5. **Probar con Test Events** directamente en la consola

---

## 🧪 Test Events para la consola de Lambda

### Todos los modelos
```json
{
    "prompt": "Explica qué es AWS Lambda en 2 párrafos cortos."
}
```

### Solo Haiku (rápido)
```json
{
    "prompt": "¿Qué es serverless?",
    "models": ["Claude Haiku 4.5"]
}
```

### Haiku vs Sonnet
```json
{
    "prompt": "Dame 3 ventajas de la computación en la nube.",
    "models": ["Claude Haiku 4.5", "Claude Sonnet 4.6"]
}
```

### Sin prompt (usa el default)
```json
{}
```

---

## 📊 Ejemplo de respuesta

```json
{
  "statusCode": 200,
  "prompt": "¿Qué es AWS Lambda?",
  "results": [
    {
      "model": "Claude Haiku 4.5",
      "tier": "fast",
      "response": "AWS Lambda es un servicio serverless...",
      "latency_ms": 1243.5,
      "input_tokens": 28,
      "output_tokens": 312,
      "total_tokens": 340,
      "cost_usd": 0.00000127
    }
  ],
  "summary": {
    "total_cost_usd": 0.00002639,
    "fastest_model": "Claude Haiku 4.5",
    "cheapest_model": "Claude Haiku 4.5",
    "haiku_vs_opus_savings": "92.5%"
  },
  "errors": null
}
```

---

## 💰 Costos (capa gratuita)

| Componente | Costo |
|---|---|
| Lambda | **$0.00** — Free tier (1M req/mes) |
| CloudWatch Logs | **$0.00** — Free tier (5 GB/mes) |
| IAM | **$0.00** — Siempre gratis |
| Bedrock (3 modelos) | **~$0.00003 por invocación** |
| Para gastar $1 | ~33,000 invocaciones |

---

## ⚠️ Notas

- Región: **us-east-1** (N. Virginia) en todo momento
- Timeout: **90 segundos** (Opus puede tardar ~20s)
- Memory: **128 MB** (suficiente, minimiza costo)
- Runtime: **Python 3.14**
- boto3 ya viene incluido en Python 3.12 de Lambda, no necesitas layers
- El handler en la consola debe ser: `lambda_handler.lambda_handler`
  (si el archivo se llama `lambda_handler.py`)

---

## 🔐 Permisos IAM necesarios

La Lambda necesita un rol con:
- `AWSLambdaBasicExecutionRole` (managed policy)
- Inline policy con `bedrock:InvokeModel` sobre los 3 modelos específicos (no wildcard)

La policy JSON completa está en `guia_setup_aws.py` (Paso 3).
