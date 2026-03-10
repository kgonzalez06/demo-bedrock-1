# 🔬 Bedrock Model Comparison — Lambda

Compara **Claude Haiku 4.5 vs Sonnet 4.6 vs Opus 4.6** con una sola llamada HTTP.  
Mide latencia, tokens y costo real en USD. Ideal para posts técnicos en dev.to / LinkedIn.

---

## 📁 Estructura del proyecto

```
bedrock-comparison/
├── lambda/
│   └── lambda_handler.py     # Código de la Lambda
├── cdk_stack.py              # Infrastructure as Code (CDK)
├── requirements.txt
└── README.md
```

---

## 🚀 Despliegue rápido

### 1. Instalar dependencias

```bash
pip install aws-cdk-lib constructs
npm install -g aws-cdk
```

### 2. Preparar la carpeta Lambda

```bash
mkdir lambda
cp lambda_handler.py lambda/
```

### 3. Habilitar modelos en Bedrock Console

Ve a **AWS Console → Bedrock → Model access** y habilita:
- ✅ Claude Haiku 4.5
- ✅ Claude Sonnet 4.6
- ✅ Claude Opus 4.6  *(puede tardar ~1 min en aprobarse)*

### 4. Deploy

```bash
cdk bootstrap   # solo la primera vez
cdk deploy
```

Al terminar verás el output:
```
Outputs:
BedrockComparisonStack.FunctionUrl = https://xxxx.lambda-url.us-east-1.on.aws/
```

---

## 🧪 Probarlo

### Desde curl (prompt personalizado)

```bash
curl -X POST https://xxxx.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "¿Qué es AWS Lambda y cuándo usarlo?"
  }'
```

### Desde AWS CLI (sin Function URL)

```bash
aws lambda invoke \
  --function-name bedrock-model-comparison \
  --payload '{"prompt": "¿Qué es AWS Lambda?"}' \
  --cli-binary-format raw-in-base64-out \
  output.json && cat output.json
```

### Solo algunos modelos

```bash
curl -X POST https://xxxx.lambda-url.us-east-1.on.aws/ \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Dame 3 ventajas de serverless",
    "models": ["Claude Haiku 4.5", "Claude Sonnet 4.6"]
  }'
```

---

## 📊 Ejemplo de respuesta JSON

```json
{
  "statusCode": 200,
  "prompt": "¿Qué es AWS Lambda y cuándo usarlo?",
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
    },
    {
      "model": "Claude Sonnet 4.6",
      "tier": "balanced",
      "response": "AWS Lambda es una plataforma de cómputo...",
      "latency_ms": 3821.0,
      "input_tokens": 28,
      "output_tokens": 489,
      "total_tokens": 517,
      "cost_usd": 0.00000819
    },
    {
      "model": "Claude Opus 4.6",
      "tier": "powerful",
      "response": "AWS Lambda representa un paradigma...",
      "latency_ms": 9104.2,
      "input_tokens": 28,
      "output_tokens": 621,
      "total_tokens": 649,
      "cost_usd": 0.00001693
    }
  ],
  "summary": {
    "total_cost_usd": 0.00002639,
    "fastest_model": "Claude Haiku 4.5",
    "fastest_latency_ms": 1243.5,
    "cheapest_model": "Claude Haiku 4.5",
    "cheapest_cost_usd": 0.00000127,
    "most_verbose_model": "Claude Opus 4.6",
    "haiku_vs_opus_savings": "92.5%",
    "lambda_cost_usd": 0.0,
    "region": "us-east-1"
  },
  "errors": null
}
```

---

## 💰 Costo estimado

| Componente | Costo |
|---|---|
| Lambda (invocaciones) | **$0.00** — Always Free (1M req/mes) |
| Lambda (duración) | **~$0.00** — entra en free tier |
| Bedrock (3 modelos, prompt corto) | **~$0.00002 por llamada** |
| **Para gastar $1** | necesitas ~50,000 invocaciones |

---

## ⚠️ Notas importantes

- La **Function URL está sin autenticación** (auth=NONE) — solo para demo. En producción usa `AWS_IAM`.
- El timeout está en **60 segundos** porque Opus puede tardar ~10-15s.
- Los precios en el código son de **Marzo 2026, región us-east-1**. Verifica en [aws.amazon.com/bedrock/pricing](https://aws.amazon.com/bedrock/pricing).
