"""
🔬 AWS Bedrock — Lambda Handler
================================
Compara Claude Haiku 4.5, Sonnet 4.6 y Opus 4.6 en una sola invocación.
Recibe un prompt vía event y devuelve métricas + respuestas en JSON.

Event de entrada (opcional):
{
  "prompt": "Tu pregunta aquí",
  "models": ["Claude Haiku 4.5", "Claude Sonnet 4.6"]  // opcional, default = todos
}

Respuesta:
{
  "statusCode": 200,
  "results": { ... },
  "summary": { ... }
}
"""

import boto3
import json
import time
import os

# ─── Configuración ────────────────────────────────────────────────────────────

# Forzar us-east-1 siempre (cambiar aquí si usas otra región)
BEDROCK_REGION = "us-east-1"

MODELS = {
    "Claude Haiku 4.5": {
        "id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "price_input":  1.00,   # USD por millón de tokens
        "price_output": 5.00,
        "tier": "fast",
    },
    "Claude Sonnet 4.6": {
        "id": "us.anthropic.claude-sonnet-4-6",
        "price_input":  3.00,
        "price_output": 15.00,
        "tier": "balanced",
    },
    "Claude Opus 4.6": {
        "id": "us.anthropic.claude-opus-4-6-v1",
        "price_input":  5.00,
        "price_output": 25.00,
        "tier": "powerful",
    },
}

DEFAULT_PROMPT = (
    "Explica en 3 párrafos cortos qué es la computación en la nube "
    "y cuáles son sus principales beneficios para una empresa pequeña. "
    "Usa un lenguaje claro y sin tecnicismos."
)

# Cliente se inicializa fuera del handler para reutilizar el contenedor
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

# ─── Invocación de un modelo ──────────────────────────────────────────────────

def invoke_model(model_name: str, config: dict, prompt: str) -> dict:
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    start = time.perf_counter()
    response = bedrock.invoke_model(
        modelId=config["id"],
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json",
    )
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    body = json.loads(response["body"].read())
    input_tokens  = body["usage"]["input_tokens"]
    output_tokens = body["usage"]["output_tokens"]

    cost_usd = (
        (input_tokens  / 1_000_000) * config["price_input"] +
        (output_tokens / 1_000_000) * config["price_output"]
    )

    return {
        "model":         model_name,
        "tier":          config["tier"],
        "response":      body["content"][0]["text"],
        "latency_ms":    latency_ms,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "total_tokens":  input_tokens + output_tokens,
        "cost_usd":      round(cost_usd, 8),
    }

# ─── Generación de insights automáticos ──────────────────────────────────────

def build_summary(results: list) -> dict:
    if not results:
        return {}

    fastest  = min(results, key=lambda r: r["latency_ms"])
    cheapest = min(results, key=lambda r: r["cost_usd"])
    longest  = max(results, key=lambda r: r["output_tokens"])  # proxy de "más detallado"

    total_cost = sum(r["cost_usd"] for r in results)

    haiku = next((r for r in results if "Haiku" in r["model"]), None)
    opus  = next((r for r in results if "Opus"  in r["model"]), None)

    savings_pct = None
    if haiku and opus and opus["cost_usd"] > 0:
        savings_pct = round((opus["cost_usd"] - haiku["cost_usd"]) / opus["cost_usd"] * 100, 1)

    return {
        "total_cost_usd":        round(total_cost, 8),
        "fastest_model":         fastest["model"],
        "fastest_latency_ms":    fastest["latency_ms"],
        "cheapest_model":        cheapest["model"],
        "cheapest_cost_usd":     cheapest["cost_usd"],
        "most_verbose_model":    longest["model"],
        "haiku_vs_opus_savings": f"{savings_pct}%" if savings_pct else None,
        "lambda_cost_usd":       0.0,  # Always Free para este volumen
        "region":                BEDROCK_REGION,
    }

def print_report(prompt: str, results: list, summary: dict, errors: list):
    """Imprime un reporte legible en CloudWatch Logs."""
    lines = [
        "",
        "═" * 60,
        "🔬 BEDROCK MODEL COMPARISON — RESULTADOS",
        "═" * 60,
        f"📝 Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}",
        "─" * 60,
    ]

    for r in results:
        lines.append(f"")
        lines.append(f"🤖 {r['model']} ({r['tier']})")
        lines.append(f"   ⏱️  Latencia:  {r['latency_ms']:,.1f} ms")
        lines.append(f"   🔢 Tokens:    {r['input_tokens']} in / {r['output_tokens']} out / {r['total_tokens']} total")
        lines.append(f"   💰 Costo:     ${r['cost_usd']:.6f}")
        lines.append(f"   📄 Respuesta: {r['response'][:100]}...")

    if summary:
        lines.append("")
        lines.append("─" * 60)
        lines.append("📊 RESUMEN")
        lines.append("─" * 60)
        lines.append(f"   🏆 Más rápido:  {summary['fastest_model']} ({summary['fastest_latency_ms']:,.1f} ms)")
        lines.append(f"   💸 Más barato:  {summary['cheapest_model']} (${summary['cheapest_cost_usd']:.6f})")
        lines.append(f"   📝 Más extenso: {summary['most_verbose_model']}")
        lines.append(f"   💰 Costo total: ${summary['total_cost_usd']:.6f}")
        if summary.get('haiku_vs_opus_savings'):
            lines.append(f"   📉 Ahorro Haiku vs Opus: {summary['haiku_vs_opus_savings']}")

    if errors:
        lines.append("")
        lines.append("⚠️  ERRORES:")
        for e in errors:
            lines.append(f"   ❌ {e['model']}: {e['error'][:80]}")

    lines.append("═" * 60)
    print("\n".join(lines))


# ─── Handler principal ────────────────────────────────────────────────────────


def lambda_handler(event, context):
    prompt           = event.get("prompt", DEFAULT_PROMPT)
    requested_models = event.get("models", list(MODELS.keys()))

    selected = {k: v for k, v in MODELS.items() if k in requested_models}
    if not selected:
        return {
            "statusCode": 400,
            "error": "Ningún modelo válido. Usa: " + ", ".join(MODELS.keys()),
        }

    results = []
    errors  = []

    for model_name, config in selected.items():
        try:
            result = invoke_model(model_name, config, prompt)
            results.append(result)
        except Exception as e:
            errors.append({"model": model_name, "error": str(e)})

    summary = build_summary(results)

    # Imprimir reporte legible en CloudWatch
    print_report(prompt, results, summary, errors)

    return {
        "statusCode": 200,
        "prompt":     prompt,
        "results":    results,
        "summary":    summary,
        "errors":     errors if errors else None,
    }

