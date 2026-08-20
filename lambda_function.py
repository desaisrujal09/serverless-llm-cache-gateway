import json
import boto3
import os

bedrock = boto3.client('bedrock-runtime')
# Pull the expected key from the Terraform environment variables
EXPECTED_API_KEY = os.environ.get('API_KEY', 'default-key')

def handler(event, context):
    try:
        # 1. AUTHENTICATION CHECK
        headers = event.get('headers', {})
        # API Gateway sometimes lowercases headers, so we check for 'authorization'
        auth_header = headers.get('authorization', headers.get('Authorization', ''))
        
        if auth_header != f"Bearer {EXPECTED_API_KEY}":
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unauthorized. Invalid API Key."})
            }

        # 2. ORIGINAL BEDROCK LOGIC
        body = json.loads(event.get('body', '{}'))
        model_id = body.get('model', 'amazon.nova-micro-v1:0')
        messages = body.get('messages', [])
        
        bedrock_messages = []
        for msg in messages:
            if msg.get('role') != 'system':
                bedrock_messages.append({
                    "role": msg.get('role'),
                    "content": [{"text": msg.get('content', '')}]
                })
                
        system_prompts = [{"text": m.get('content')} for m in messages if m.get('role') == 'system']
        
        kwargs = {
            "modelId": model_id,
            "messages": bedrock_messages
        }
        if system_prompts:
            kwargs["system"] = system_prompts
            
        response = bedrock.converse(**kwargs)
        output_text = response['output']['message']['content'][0]['text']
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "choices": [{"message": {"role": "assistant", "content": output_text}}]
            })
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}