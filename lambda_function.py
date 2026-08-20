import json
import boto3
import os
import hashlib
import time

bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
cache_table = dynamodb.Table(os.environ.get('CACHE_TABLE', 'LLMPromptCache'))

# Helper function to create a unique ID for a prompt
def get_cache_key(model_id, messages):
    # Sort keys to ensure {"a":1, "b":2} hashes identically to {"b":2, "a":1}
    content = json.dumps({"model": model_id, "messages": messages}, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def handler(event, context):
    # ... (Auth checks and Bedrock Converse formatting here) ...
    
    # 1. Generate the hash for the incoming request
    cache_key = get_cache_key(bedrock_model_id, messages)

    # 2. CHECK DYNAMODB CACHE
    try:
        cache_response = cache_table.get_item(Key={'PromptHash': cache_key})
        if 'Item' in cache_response:
            print("CACHE HIT! Saved Bedrock inference cost.")
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": cache_response['Item']['ResponsePayload']
            }
    except Exception as e:
        print(f"Cache read bypassed due to error: {e}")

    # 3. CACHE MISS - Call Bedrock as normal
    response = bedrock.converse(**kwargs)
    output_text = response['output']['message']['content'][0]['text']
    
    # Format the fake OpenAI response
    final_response_body = json.dumps({
        "model": requested_model,
        "choices": [{"message": {"role": "assistant", "content": output_text}}]
    })

    # 4. SAVE TO DYNAMODB CACHE
    try:
        # Set Time-To-Live for 24 hours (86,400 seconds)
        expiration_time = int(time.time()) + 86400
        cache_table.put_item(
            Item={
                'PromptHash': cache_key,
                'ResponsePayload': final_response_body,
                'ExpirationTime': expiration_time
            }
        )
    except Exception as e:
        print(f"Failed to write to cache: {e}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": final_response_body
    }