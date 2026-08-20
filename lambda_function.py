import json
import boto3

# Initialize outside the handler for connection reuse
bedrock = boto3.client('bedrock-runtime')

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        model_id = body.get('model', 'amazon.nova-micro-v1:0')
        messages = body.get('messages', [])
        
        # Bedrock requires system prompts to be separated from user/assistant messages
        bedrock_messages = []
        for msg in messages:
            if msg.get('role') != 'system':
                bedrock_messages.append({
                    "role": msg.get('role'),
                    "content": [{"text": msg.get('content', '')}]
                })
                
        system_prompts = [{"text": m.get('content')} for m in messages if m.get('role') == 'system']
        
        # Build Converse API payload
        kwargs = {
            "modelId": model_id,
            "messages": bedrock_messages
        }
        if system_prompts:
            kwargs["system"] = system_prompts
            
        # Invoke the model
        response = bedrock.converse(**kwargs)
        output_text = response['output']['message']['content'][0]['text']
        
        # Return OpenAI-compatible response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "choices": [{"message": {"role": "assistant", "content": output_text}}]
            })
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}