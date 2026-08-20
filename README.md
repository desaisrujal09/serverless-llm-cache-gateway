# Serverless LLM Gateway (AWS Bedrock & Terraform)

![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![Amazon Bedrock](https://img.shields.io/badge/Amazon_Bedrock-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)

An enterprise-ready, serverless proxy gateway deployed with Terraform that translates standard **OpenAI API** requests into **AWS Bedrock Converse API** calls. 

This project enables existing applications and AI pipelines to seamlessly switch their backend models to AWS Bedrock (e.g., Anthropic Claude 3.5 Sonnet, Amazon Nova) by simply changing their base URL—without requiring any application code rewrites.

---

## Key Features

- **OpenAI API Compatibility:** Exposes a standard `POST /chat/completions` endpoint that adheres to the OpenAI payload specification.
- **Unified Model Translation:** Leverages AWS Bedrock's **Converse API** to standardize communication across all foundation models (Anthropic, Amazon Nova, Meta Llama).
- **Dynamic Model Mapping:** Automatically intercepts OpenAI model requests (`gpt-4o`, `gpt-3.5-turbo`) and maps them to equivalent AWS Bedrock model IDs.
- **Header-Based Authentication:** Enforces API Key authorization via HTTP `Authorization: Bearer <KEY>` headers validated directly at the Lambda boundary.
- **100% Infrastructure as Code:** Provisioned entirely via modular Terraform configuration files, ensuring repeatable zero-touch deployments.
- **Zero-Server Overhead:** Built on AWS HTTP API Gateway and AWS Lambda, paying only per-request with automatically scaled compute.

---

## Architecture Overview

```text
+--------------------+        HTTP POST         +------------------------+
| Client Application | -----------------------> |    AWS API Gateway     |
| (OpenAI Python SDK |   Authorization: Bearer  | (HTTP API - /chat/...) |
|   or curl request) |                          +------------------------+
+--------------------+                                      |
                                                            v
+--------------------+      Invoke Model        +------------------------+
|   Amazon Bedrock   | <----------------------- |   AWS Lambda Function  |
| (Claude 3.5 / Nova)|  (Converse API Payload)  |  (Auth & Translation)  |
+--------------------+                          +------------------------+