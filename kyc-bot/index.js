const Symphony = require('symphony-api-client-node')
// Symphony.setDebugMode(true)
const AWS = require('aws-sdk');

AWS.config.region = 'us-west-2'; // Region
//var credentials = new AWS.SharedIniFileCredentials({profile: 'bot'});
//AWS.config.credentials = credentials;

var lexruntime = new AWS.LexRuntime();

const formMessage = "<messageML><form id='form_id'><h4>Personal Information</h4><text-field name='name_01' required='true' placeholder='Name'/><button name='submit_button' type='action'>Submit</button></form></messageML>";

const botName = 'CustomerSignUp'
const alias = 'Dev'
var sessionAttributes = {};

function pushChat(streamId, message) {

  var the_message = message.messageText;
  if (message.attachments) {
    attachmentId=message.attachments[0].id;
    the_message = "https://develop2.symphony.com/agent/v1/stream/"+streamId+"/attachment?messageId="+message.messageId+"&fileId="+attachmentId;
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

  console.log("Started :"+ params.inputText);


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
          jsonText = JSON.parse(message.payload);
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

const sendMessage = (message) =>{
  Symphony.sendMessage(message.streamId, message.payload, null, Symphony.MESSAGEML_FORMAT);
};

const logMessage = (message) =>{
  if (message)
    console.log(message);
}

const onMessage = (event, messages) => {
  messages.forEach((message, index) => {

      logMessage(message.stream.streamId,message.messageText);
      // pushChat(message.stream.streamId,message);
  })
}



const elementsHandler = (event, actions) => {
  actions.forEach((action, index) => {
    console.log(action)
  })
}

const onError = error => {
  console.error('Error reading data feed', error)
}

const sessionToken = '';
const keymanagerToken = '';
Symphony.initBot(__dirname + '/config.json')
  .then((symAuth) => {
    Symphony.getDatafeedEventsService(onMessage, onError);
  })
