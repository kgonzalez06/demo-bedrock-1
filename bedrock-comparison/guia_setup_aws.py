"""
🔬 Guía de Configuración Manual en AWS Console
================================================
Proyecto: Bedrock Model Comparison (Haiku 4.5 vs Sonnet 4.6 vs Opus 4.6)

NO necesitas CDK, Terraform ni ninguna herramienta de IaC.
Todo se hace desde https://console.aws.amazon.com
Región: us-east-1 (N. Virginia)

═══════════════════════════════════════════════════════════
PASO 1 — Permisos de Marketplace para tu usuario IAM
═══════════════════════════════════════════════════════════

Los modelos de Anthropic en Bedrock se sirven vía AWS Marketplace.
La primera vez que invocas un modelo, se crea una suscripción automática
(gratis). Tu usuario IAM necesita permisos para eso.

1. Ve a: IAM → Users → tu usuario (con el que accedes a la consola)
2. Add permissions → Create inline policy → JSON:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "MarketplaceForBedrock",
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*"
        }
    ]
}

3. Nombre: marketplace-bedrock-access
4. Guarda

NOTA: Si accedes con el usuario root (email + password), ya tienes
estos permisos. Este paso es solo para usuarios IAM.

═══════════════════════════════════════════════════════════
PASO 2 — Activar los modelos de Anthropic en Bedrock
═══════════════════════════════════════════════════════════

La página "Model access" fue retirada. Ahora los modelos se activan
automáticamente la primera vez que los usas. PERO para modelos de
Anthropic, necesitas enviar un formulario de use case la primera vez.

1. Ve a: Bedrock → Model catalog (us-east-1)
2. Busca "Claude Haiku 4.5" → click → Open in Playground
3. Si te pide "Submit use case details for Anthropic", llena:
   - Company name:     Tu nombre o "Independent Developer"
   - Company URL:      Tu perfil de GitHub, LinkedIn o dev.to
   - Industry:         Technology
   - Intended users:   ✅ Internal users
   - Use case:
     "Personal learning and technical content creation. Building a
      serverless application using AWS Lambda to compare response
      quality, latency, and cost across different Claude models on
      Amazon Bedrock. Low volume usage for testing and benchmarking."
4. Submit y espera aprobación (~1-2 minutos)

5. Una vez aprobado, haz una pregunta en el Playground para activar
   la suscripción de Marketplace. Recibirás un correo de confirmación.

6. Repite con Claude Sonnet 4.6 y Claude Opus 4.6
   (una pregunta en el Playground de cada uno para activar la suscripción)

7. Verifica que recibes 3 correos de AWS Marketplace, uno por modelo.

═══════════════════════════════════════════════════════════
PASO 3 — Crear el IAM Role para la Lambda (mínimo privilegio)
═══════════════════════════════════════════════════════════

1. Ve a: IAM → Roles → Create role
2. Trusted entity: AWS service → Lambda → Next
3. NO adjuntes ninguna managed policy por ahora → Next
4. Nombre del rol: bedrock-comparison-lambda-role
5. Crea el rol

6. Ve al rol recién creado → Permissions → Add permissions
   → Create inline policy → JSON:

── Policy 1: CloudWatch Logs (solo lo necesario) ──
Nombre: lambda-cloudwatch-logs

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:us-east-1:TU_ACCOUNT_ID:log-group:/aws/lambda/bedrock-model-comparison:*"
        }
    ]
}

NOTA: Reemplaza TU_ACCOUNT_ID con tu ID de cuenta (12 dígitos).
      Lo encuentras en la esquina superior derecha de la consola.
      Si tu Lambda se llama diferente, ajusta el nombre en el ARN.

7. Agrega otra inline policy → JSON:

── Policy 2: Bedrock InvokeModel (solo los 3 modelos específicos) ──
Nombre: bedrock-invoke-claude-models

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BedrockInvokeFoundationModels",
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6",
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-4-6-v1"
            ]
        },
        {
            "Sid": "BedrockInvokeInferenceProfiles",
            "Effect": "Allow",
            "Action": "bedrock:InvokeModel",
            "Resource": [
                "arn:aws:bedrock:us-east-1:TU_ACCOUNT_ID:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
                "arn:aws:bedrock:us-east-1:TU_ACCOUNT_ID:inference-profile/us.anthropic.claude-sonnet-4-6",
                "arn:aws:bedrock:us-east-1:TU_ACCOUNT_ID:inference-profile/us.anthropic.claude-opus-4-6-v1"
            ]
        }
    ]
}

NOTA: Reemplaza TU_ACCOUNT_ID con tu ID de cuenta.
      La región es * en foundation-model porque el cross-region
      inference routing puede enviar la petición a cualquier región US.
      Los inference profiles sí llevan tu account ID y región.

¿Por qué NO usamos bedrock:* con Resource *?
  - Principio de mínimo privilegio: solo permitimos InvokeModel
  - Solo sobre los 3 modelos que usamos, no todos los de Bedrock
  - Si alguien compromete la Lambda, no puede listar modelos,
    crear endpoints, ni invocar otros modelos

═══════════════════════════════════════════════════════════
PASO 4 — Crear la Lambda Function
═══════════════════════════════════════════════════════════

1. Ve a: Lambda → Create function
2. Configuración:
   - Function name:  bedrock-model-comparison
   - Runtime:        Python 3.14
   - Architecture:   x86_64
   - Execution role:  Use an existing role → bedrock-comparison-lambda-role
3. Crea la función

4. En la pestaña "Code":
   - Borra el código por defecto
   - Copia y pega TODO el contenido de lambda_handler.py
   - El archivo en la consola se llama lambda_function.py por defecto
   - Click "Deploy"

5. En Configuration → General configuration → Edit:
   - Handler:   lambda_function.lambda_handler
   - Timeout:   1 min 30 sec  (Opus puede tardar ~15-20s)
   - Memory:    128 MB
   - Guarda

═══════════════════════════════════════════════════════════
PASO 5 — Probar con Test Events
═══════════════════════════════════════════════════════════

En la pestaña "Test" de la Lambda, crea estos test events:

── Test 1: Todos los modelos ──
Nombre: test_todos

{
    "prompt": "Explica qué es AWS Lambda en 2 párrafos cortos."
}

── Test 2: Solo Haiku (rápido y barato) ──
Nombre: test_solo_haiku

{
    "prompt": "¿Qué es serverless?",
    "models": ["Claude Haiku 4.5"]
}

── Test 3: Haiku vs Sonnet ──
Nombre: test_haiku_vs_sonnet

{
    "prompt": "Dame 3 ventajas de la computación en la nube.",
    "models": ["Claude Haiku 4.5", "Claude Sonnet 4.6"]
}

── Test 4: Sin prompt (usa el default) ──
Nombre: test_default

{}

El reporte legible se ve en: Monitor → View CloudWatch Logs

═══════════════════════════════════════════════════════════
💰 COSTOS — CAPA GRATUITA
═══════════════════════════════════════════════════════════

Lambda Free Tier (siempre gratis):
  - 1,000,000 requests/mes          → usarás ~10-50
  - 400,000 GB-segundos/mes         → cada invocación usa ~0.004 GB-s

CloudWatch Logs: 5 GB/mes gratis    → usarás ~KB
IAM: Gratis siempre
Marketplace suscripciones: Gratis (solo pagas por uso de los modelos)

Bedrock (pago por uso, sin free tier):
  - Haiku 4.5:  $1.00 input / $5.00 output por millón de tokens
  - Sonnet 4.6: $3.00 input / $15.00 output por millón de tokens
  - Opus 4.6:   $5.00 input / $25.00 output por millón de tokens
  - Los 3 juntos con prompt corto: ~$0.04 por invocación
  - Para gastar $1 necesitas ~25 invocaciones de los 3 modelos

═══════════════════════════════════════════════════════════
⚠️  TROUBLESHOOTING
═══════════════════════════════════════════════════════════

Error: "AccessDeniedException ... aws-marketplace:ViewSubscriptions"
  → Los modelos no están activados. Ve al Playground de Bedrock y
    haz una pregunta con cada modelo para activar la suscripción.
  → Si usas un usuario IAM, agrega los permisos de Marketplace (Paso 1).

Error: "AccessDeniedException ... bedrock:InvokeModel ... us-east-2"
  → El cross-region routing envía peticiones a otras regiones.
    Asegúrate de que la policy de Bedrock use * en la región
    para foundation-model (ver Paso 3, Policy 2).

Error: "ValidationException ... Retry with inference profile"
  → Usa los model IDs con prefijo us. (inference profiles),
    no los IDs directos. El código ya los tiene configurados.

Error: "Task timed out after X seconds"
  → Aumenta el timeout de la Lambda a 60 segundos mínimo.
    Opus puede tardar ~20s en responder.

═══════════════════════════════════════════════════════════
📋 RESUMEN DE PERMISOS (mejores prácticas)
═══════════════════════════════════════════════════════════

Tu usuario IAM:
  ✅ aws-marketplace:ViewSubscriptions (para activar modelos)
  ✅ aws-marketplace:Subscribe

Rol de la Lambda (bedrock-comparison-lambda-role):
  ✅ logs:CreateLogGroup, CreateLogStream, PutLogEvents
     (solo en el log group de esta Lambda)
  ✅ bedrock:InvokeModel
     (solo en los 3 modelos Claude específicos)
  ❌ NO tiene bedrock:* ni Resource *
  ❌ NO tiene AWSLambdaBasicExecutionRole (usamos policy custom más restrictiva)
  ❌ NO tiene permisos de Marketplace (no los necesita)
"""
