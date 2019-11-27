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

    print(event['sessionAttributes'])

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
                'keyManagerToken':event['sessionAttributes']['kmAuthToken'],
                'sessionToken':event['sessionAttributes']['sessionAuthToken']
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
            Document={'Bytes': r1_imagebytes})

        response2 = client.detect_document_text(
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
