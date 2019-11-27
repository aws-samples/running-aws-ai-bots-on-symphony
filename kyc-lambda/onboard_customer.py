import json
import boto3
import base64
import botocore.vendored.requests as requests

 
def lambda_handler(event, context):
    
    print('received request: ' + str(event))
    
    # "GatherPersonalInfo" intent - success response back to the Lex Bot.
    response_to_bot = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
              "contentType": "PlainText",
              "content": "Congratulations! Your Customer has been onboarded."
            },
        }
    }
    
   # return response_to_bot
    
    print(event['currentIntent']['name'])
    if event['currentIntent']['name'] == "GatherPersonalInfo":
        return response_to_bot
    else:
        firstdocumentURL = event['currentIntent']['slots']['FirstDocument']
        seconddocumentURL = event['currentIntent']['slots']['SecondDocument']
        
        print('received firstdocumentURL: ' + firstdocumentURL)
        print('received seconddocumentURL: ' + seconddocumentURL)
        
        
        #url = 'https://develop2.symphony.com/agent/v1/stream/0FewnZap7KoyFywBghfJHX___pKgW9PadA/attachment?messageId=s6OwnDIc5qiKyASCopfwd3%2F%2F%2FpKVbve8bQ%3D%3D&fileId=internal_349026222348235%2FZKUMkQZBwNIZxWxSw%2FTPgA%3D%3D'
        headers = {
                'content-type': '*/*',
                'keyManagerToken':'01003476f7916de7269df6c8a3251dd91f4b137af557ab1c3fb0e22367e525cf92bc370d691f0ae275d5d9fbdd5a427aebab525ee83bdb00378edca96832c571f08c29ea3bc6d50ce39957c0cce7a760817ca5c0c3b3ad6190ff176eda00117e8d85e10c2f025f8a815b3d1bf9466c60c9ec46ae558b17242dfa9489b724f0dcf84237ed5156193976f761301102d1abdea8a6275321de1c0e24cc5a75ccd589041a11c60123490e350c1e9572c4a1c9b00af4f9541137b606',
                'sessionToken':'eyJhbGciOiJSUzUxMiJ9.eyJzdWIiOiJib3QuYXdzMSIsImlzcyI6InN5bXBob255Iiwic2Vzc2lvbklkIjoiNzlmOTUwZTQ2YzIwYmVjOWRkOGQ4YzM4MzY0NzdiMGExYjY5MmQ4MjczNjY3ZWVlMTRiYzhiYzg0NDUzNzM0MTU4NmIyMWQ0ZGRmMDVkNTJkZDA2YzMzMGE4MjQ2YjhkMDAwMDAxNmRiODNiMWFjYzAwMDEzZDcwMDAwMDBhYmYiLCJ1c2VySWQiOiIzNDkwMjYyMjIzNDQ4OTUifQ.hLoXIX5M9gGw-1sfSEUOJOpOcC4zzWPNDykem4mOP5XYeCu_D_PeHmip8NSvsC0-venJyQStb8B1Eo6yis9fakVDsYllM38lKEQwDCGqJJFL0wgexEkcxPZ5Fb1qO_RKu8G7NjuGb4uI5iZSMOfGlicnpgH5buVQ3ew-MD7CWiCbf4EGLvrndDZcq7YfXXy_VDyXx34Mpt-8_jNst5qIlE2bVLwcaFbS2sZMZJRiw1shE-NiCIeS7saUY38XLbngzM1J494dUSZ4wNas1aS50FvIL9da5Ft3iEIt7rp9FQDutVTcdqv_HEgVdYgW-1qlG8kYAD36mBw4knw1LoeU3Q'
            }
        
        
        r1 = requests.get(firstdocumentURL,headers=headers, stream=True)
        print('r= '+ str(r1))    
        r1_b64_imagebytes = r1.content
        r1_imagebytes = base64.b64decode(r1_b64_imagebytes)
        print('r1_imagebytes= '+str(r1_imagebytes))
        
        r2 = requests.get(seconddocumentURL,headers=headers, stream=True)
        print('r= '+ str(r2))    
        r2_b64_imagebytes = r2.content
        r2_imagebytes = base64.b64decode(r2_b64_imagebytes)
        print('r2_imagebytes= '+str(r2_imagebytes))
        
        
        client = boto3.client('textract')
    
        #process using S3 object or bytes
        response1 = client.detect_document_text(
            #Document={'S3Object': {'Bucket': 'kycdemo', 'Name': 'johndoe_doc1.jpg'}})
            Document={'Bytes': r1_imagebytes})
            
       
        response2 = client.detect_document_text(
            #Document={'S3Object': {'Bucket': 'kycdemo', 'Name': 'johndoe_doc2.jpg'}})
            Document={'Bytes': r2_imagebytes})
        
        #Get the text blocks
        texts1 = set()
        texts1_orig = set()
        for block in response1['Blocks']:
           if block['BlockType'] != 'PAGE':
                    texts1.add(block['BlockType'] + ":" + block['Text'] + "," )
                    texts1_orig.add(block['Text'])
        
        
        
        texts2 = set()
        for block in response2['Blocks']:
            if block['BlockType'] != 'PAGE':
                   texts2.add(block['Text'])
    
        # Verification logic to compare the inputs and the extracted texts. 
        print('texts1_orig= ' + str(texts1_orig))
        print('texts2= ' + str(texts2))
        print('Set intersection= ' + str(texts1_orig & texts2))
        

        if not bool(texts1_orig.intersection(texts2)): 
            print('Empty')
            response_to_bot["dialogAction"]["message"]["content"] = "Customer On-boarding Failed!...Documents do not match."
            return response_to_bot
                   
       
        info_set = dict();
        for num, block in  enumerate(response1['Blocks']):
                  if block['BlockType'] == 'LINE':
                      if block['Text'].startswith('1 '):
                         info_set['first_name'] = block['Text'][2:]
                      if block['Text'].startswith('2 '):
                         info_set['last_name'] = block['Text'][2:]
                      if block['Text'].startswith('8'):
                         info_set['street_address'] = block['Text'][2:] + "," + response1['Blocks'][num +1]['Text']  # little hack to get the second line of the address

        print(info_set)
        
        response_to_bot["dialogAction"]["message"]["content"] = json.dumps(info_set)
        return response_to_bot