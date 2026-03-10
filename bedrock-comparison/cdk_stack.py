"""
🏗️  CDK Stack — Bedrock Model Comparison Lambda
================================================
Despliega:
  - Lambda Function (Python 3.12, 30s timeout, 256MB)
  - IAM Role con permisos bedrock:InvokeModel
  - Function URL pública (auth=NONE) para probar desde curl/Postman
  - CloudWatch Log Group con retención de 7 días

Uso:
  pip install aws-cdk-lib constructs
  cdk deploy
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class BedrockComparisonStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ── IAM Role ──────────────────────────────────────────────────────────
        lambda_role = iam.Role(
            self, "BedrockLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Permiso para invocar los 3 modelos Claude en Bedrock
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockInvokeModels",
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    # Haiku 4.5
                    f"arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
                    # Sonnet 4.6
                    f"arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-6",
                    # Opus 4.6
                    f"arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-opus-4-6-v1",
                    # Cross-region inference profiles (prefijo us.)
                    f"arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
                    f"arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-sonnet-4-6",
                    f"arn:aws:bedrock:us-east-1:*:inference-profile/us.anthropic.claude-opus-4-6-v1",
                ],
            )
        )

        # ── CloudWatch Log Group ──────────────────────────────────────────────
        log_group = logs.LogGroup(
            self, "BedrockComparisonLogs",
            log_group_name="/aws/lambda/bedrock-model-comparison",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # ── Lambda Function ───────────────────────────────────────────────────
        fn = _lambda.Function(
            self, "BedrockComparisonFn",
            function_name="bedrock-model-comparison",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset("lambda"),   # carpeta con lambda_handler.py
            role=lambda_role,
            timeout=Duration.seconds(60),             # Opus puede tardar ~10-15s
            memory_size=256,
            log_group=log_group,
            environment={
                "AWS_REGION_NAME": "us-east-1",       # evita conflicto con la var reservada
            },
        )

        # ── Function URL (sin auth — solo para demo/post) ─────────────────────
        fn_url = fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[_lambda.HttpMethod.POST],
            ),
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(
            self, "FunctionUrl",
            value=fn_url.url,
            description="URL pública para invocar la comparación (solo demo)",
        )
        cdk.CfnOutput(
            self, "FunctionName",
            value=fn.function_name,
            description="Nombre de la Lambda para invocar desde CLI",
        )


# ── App entry point ────────────────────────────────────────────────────────────

app = cdk.App()

BedrockComparisonStack(
    app, "BedrockComparisonStack",
    env=cdk.Environment(region="us-east-1"),
)

app.synth()
