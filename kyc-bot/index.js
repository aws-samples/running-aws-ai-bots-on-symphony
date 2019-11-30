const Symphony = require('symphony-api-client-node')
const AWS = require('aws-sdk');

Symphony.setDebugMode(true)
AWS.config.region = 'us-west-2'; // Region
var lexruntime = new AWS.LexRuntime();

const botName = 'CustomerSignUp'
const alias = 'Dev'
var sessionAttributes = {};

// Function to handle message callbacks and pass through to lex runtime
function pushChat(streamId, message) {

  var the_message = message.messageText;
  if (message.attachments) {
    var attachmentId = message.attachments[0].id;
    the_message = "https://develop2.symphony.com/agent/v1/stream/"+streamId+"/attachment?messageId="+message.messageId+"&fileId="+attachmentId;
    //console.log(the_message);
  }

  // attaching a symphony session with the bot.
  // We probably need to have a mechanism to reset the conversation once a lex transaction is done
  var lexUserId = streamId ;

  // send it to the Lex runtime
  var params = {
    botAlias: alias,
    botName: botName,
    inputText: the_message,
    userId: lexUserId,
    sessionAttributes: sessionAttributes
  };

  console.log("Started = "+params.inputText);
  
  lexruntime.postText(params, function(err, data) {
      console.log("response came back")
      if (err) {
        console.log(err, err.stack);
        sendMessage('Oops! Something happened  ' + err.message + ' (Can you send message again?)')
      }
      if (data) {
        console.log(data.message);
        // capture the sessionAttributes for the next cycle
        sessionAttributes = data.sessionAttributes;
        // show response and/or error/dialog status
        const message = { 'streamId': streamId, 'payload' : data.message }
        if (!data.message.includes('Failed') && data.intentName && data.intentName.includes('Document')&& data.dialogState && data.dialogState.includes('Fulfilled'))
        {
            var jsonText = JSON.parse(message.payload);
            var final_message = "Congratulations your customer is onboarded! Here is what we extracted First Name : "
                                + jsonText["first_name"] + " , Last Name : " + jsonText["last_name"]
                                + ", Address : " + jsonText["street_address"];
            message.payload = final_message;
            sendMessage(message);
        }
        else {
          sendMessage(message);
        }
      }
    })
    console.log("Finished = " + params.inputText);
}

// function to send messages back to symphony
const sendMessage = (message) =>{
  Symphony.sendMessage(message.streamId, message.payload, null, Symphony.MESSAGEML_FORMAT);
};

// function to pass handle message callback 
const onMessage = (event, messages) => {
  messages.forEach((message, index) => {
      logmessage(message);
      //pushChat(message.stream.streamId,message);
  })
}

// function to log console messages
const logmessage =  (message) => {
    console.log(message.messageText);
    if (message.attachments) console.log(message.attachments[0].id);
}

// function to handle error from symphony bot
const onError = error => {
  console.error('Error reading data feed', error)
}

// Initialize connection to bot
Symphony.initBot(__dirname + '/config.json')
  .then((symAuth) => {
    console.log(symAuth);
    sessionAttributes.sessionAuthToken = symAuth.sessionAuthToken;
    sessionAttributes.kmAuthToken = symAuth.kmAuthToken;
    Symphony.getDatafeedEventsService(onMessage, onError);
  })
