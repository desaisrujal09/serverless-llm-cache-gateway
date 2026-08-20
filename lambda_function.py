import json
import boto3
import os
import hashlib
import time

# Initialize clients outside the handler for connection reuse
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

EXPECTED_API_KEY = os.environ.get('API_KEY', 'default-key')
CACHE_TABLE_NAME = os.environ.get('CACHE_TABLE')

# Model mapping dictionary
MODEL_MAPPING = {
    "gpt-3.5-turbo": "amazon.nova-micro-v1:0",
    "gpt-4": "anthropic.claude-3-sonnet-20240229-v1:0",
    "gpt-4o": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "gpt-4o-mini": "anthropic.claude-3-haiku-20240307-v1:0"
}

def get_cache_key(model_id, messages):
    """Generate a deterministic SHA-256 hash of the request payload."""
    content = json.dumps({"model": model_id, "messages": messages}, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def handler(event, context):
    try:
        # 1. AUTHENTICATION CHECK
        headers = event.get('headers') or {}
        auth_header = headers.get('authorization', headers.get('Authorization', ''))
        
        if auth_header != f"Bearer {EXPECTED_API_KEY}":
            return {
                "statusCode": 401,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Unauthorized. Invalid API Key."})
            }

        # 2. PARSE REQUEST & MAP MODEL
        body = json.loads(event.get('body', '{}'))
        requested_model = body.get('model', 'gpt-3.5-turbo')
        
        # FIX: Define bedrock_model_id BEFORE generating the cache key
        bedrock_model_id = MODEL_MAPPING.get(requested_model, requested_model)
        messages = body.get('messages', [])

        # 3. CHECK CACHE (DynamoDB)
        cache_key = get_cache_key(bedrock_model_id, messages)
        
        if CACHE_TABLE_NAME:
            try:
                table = dynamodb.Table(CACHE_TABLE_NAME)
                cache_response = table.get_item(Key={'PromptHash': cache_key})
                
                if 'Item' in cache_response:
                    print("CACHE HIT! Returning response from DynamoDB.")
                    return {
                        "statusCode": 200,
                        "headers": {
                            "Content-Type": "application/json",
                            "X-Cache": "HIT"
                        },
                        "body": cache_response['Item']['ResponsePayload']
                    }
            except Exception as cache_err:
                print(f"Cache lookup failed (continuing to Bedrock): {str(cache_err)}")

        # 4. CACHE MISS - CONVERT TO BEDROCK CONVERSE API FORMAT
        bedrock_messages = []
        for msg in messages:
            if msg.get('role') != 'system':
                bedrock_messages.append({
                    "role": msg.get('role'),
                    "content": [{"text": msg.get('content', '')}]
                })
                
        system_prompts = [{"text": m.get('content')} for m in messages if m.get('role') == 'system']
        
        kwargs = {
            "modelId": bedrock_model_id,
            "messages": bedrock_messages
        }
        if system_prompts:
            kwargs["system"] = system_prompts
            
        # INVOKE BEDROCK
        response = bedrock.converse(**kwargs)
        output_text = response['output']['message']['content'][0]['text']
        
        response_payload = json.dumps({
            "model": requested_model,
            "choices": [{"message": {"role": "assistant", "content": output_text}}]
        })

        # 5. WRITE RESPONSE TO CACHE
        if CACHE_TABLE_NAME:
            try:
                table = dynamodb.Table(CACHE_TABLE_NAME)
                expiration = int(time.time()) + 86400  # 24-hour TTL
                table.put_item(
                    Item={
                        'PromptHash': cache_key,
                        'ResponsePayload': response_payload,
                        'ExpirationTime': expiration
                    }
                )
            except Exception as write_err:
                print(f"Cache write failed: {str(write_err)}")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Cache": "MISS"
            },
            "body": response_payload
        }

    except Exception as e:
        print(f"CRITICAL GATEWAY ERROR: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }