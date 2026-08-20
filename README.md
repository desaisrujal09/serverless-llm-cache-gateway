# Serverless LLM Gateway (AWS Bedrock & Terraform)

![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon Bedrock](https://img.shields.io/badge/Amazon_Bedrock-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon DynamoDB](https://img.shields.io/badge/Amazon_DynamoDB-4053D6?style=for-the-badge&logo=Amazon%20DynamoDB&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)

An enterprise-ready, serverless proxy gateway deployed with Terraform that translates standard **OpenAI API** requests into **AWS Bedrock Converse API** calls. 

This project enables existing applications and AI pipelines to seamlessly switch their backend models to AWS Bedrock (e.g., Anthropic Claude 3.5 Sonnet, Amazon Nova) by simply changing their base URL—without requiring any application code rewrites. It features a built-in caching layer to eliminate redundant LLM inference costs.

---

## Key Features

- **OpenAI API Compatibility:** Exposes a standard `POST /chat/completions` endpoint that adheres to the OpenAI payload specification.
- **Cost-Optimized Prompt Caching:** Uses **Amazon DynamoDB** to cache deterministic SHA-256 hashes of incoming prompts. Repetitive prompts bypass Bedrock entirely, saving 100% of inference costs and returning in <100ms. Includes a 24-hour Time-To-Live (TTL).
- **Dynamic Model Mapping:** Automatically intercepts OpenAI model requests (e.g., `gpt-4o`) and maps them to equivalent AWS Bedrock model IDs.
- **Unified Model Translation:** Leverages AWS Bedrock's **Converse API** to standardize communication across all foundation models.
- **Header-Based Authentication:** Enforces API Key authorization via HTTP `Authorization: Bearer <KEY>` headers validated directly at the Lambda boundary.
- **100% Infrastructure as Code:** Provisioned entirely via modular Terraform configuration files, ensuring repeatable zero-touch deployments.

---

## Architecture Overview

```text
+--------------------+        HTTP POST         +------------------------+
| Client Application | -----------------------> |    AWS API Gateway     |
| (OpenAI SDK, curl, |   Authorization: Bearer  | (HTTP API - /chat/...) |
|   or PowerShell)   |                          +------------------------+
+--------------------+                                      |
                                                            v
+--------------------+                            +------------------------+
|  Amazon DynamoDB   | <--- 1. Check Cache ------ |   AWS Lambda Function  |
|  (Prompt Cache)    | ---- 2. Cache Hit (200ms)->|  (Auth & Translation)  |
+--------------------+                            +------------------------+
          ^                                                 |
          |                                          3. Cache Miss
          |                                                 |
          | 5. Save Response                                v
+--------------------+      4. Invoke Model     +------------------------+
|   Amazon Bedrock   | <----------------------- |  AWS Bedrock Converse  |
| (Claude 3.5 / Nova)|                          |      API Payload       |
+--------------------+                          +------------------------+
