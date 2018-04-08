##
# Title: Alexa endpoint skill to handle requests between alexa and the
# ethereum blockchain via helper functions.
# Version: v00_01
# Author: Nzwisisa Chidembo <nzwisisa@gmail.com>
##

import os
import requests

settings = {
    'ethAPIEndPoint': os.environ['ethAPIEndPoint'],
    'bufferAPIEndPoint': os.environ['bufferAPIEndPoint'],
    'debug': os.environ['debug']
}

#######################Sample Trigger Events###################################
"""
addPatientEvent = {'response': {'type': 'success', 'data': {'transactionHash': '0x77e4f72848ae2a60f90f1cf67079ae23bbeefa1f0f1783dedeb8d728244a2b87'}}}

event = {
	"version": "1.0",
	"session": {
		"new": "false",
		"sessionId": "00000000000000000",
		"application": {
			"applicationId": "00000000000000000000000"
		},
		"user": {
			"userId": "00000000000000000000"
		}
	},
	"context": {
		"AudioPlayer": {
			"playerActivity": "IDLE"
		},
		"Display": {
			"token": ""
		},
		"System": {
			"application": {
				"applicationId": "000000000000000000000000000"
			},
			"user": {
				"userId": "000000000000000000000000000000"
			},
			"device": {
				"deviceId": "0000000000000000000000000000000000000000",
				"supportedInterfaces": {
					"AudioPlayer": {},
					"Display": {
						"templateVersion": "1.0",
						"markupVersion": "1.0"
					}
				}
			},
			"apiEndpoint": "https://api.amazonalexa.com",
			"apiAccessToken": "000000000000000000000000000000000000"
		}
	},
	"request": {
		"type": "IntentRequest",
		"requestId": "0000000000000000000000000000000000000",
		"timestamp": "2018-04-04T10:37:21Z",
		"locale": "en-US",
		"intent": {
			"name": "DraftSickNote",
			"confirmationStatus": "CONFIRMED",
			"slots": {
				"practiceNo": {
					"name": "practiceNo",
					"value": "1",
					"confirmationStatus": "CONFIRMED"
				},
				"patientId": {
					"name": "patientId",
					"value": "00000000000000000",
					"confirmationStatus": "CONFIRMED"
				},
				"illnessDescription": {
					"name": "illnessDescription",
					"value": "zzzzzzzzzzzzzzzz",
					"confirmationStatus": "CONFIRMED"
				},
				"patientFirstName": {
					"name": "patientFirstName",
					"value": "zzzzzzzzzzzzzzzzzzzzz",
					"confirmationStatus": "CONFIRMED"
				},
				"mobileNo": {
					"name": "mobileNo",
					"value": "00000000000000000000000000",
					"confirmationStatus": "CONFIRMED"
				},
				"sickDays": {
					"name": "sickDays",
					"value": "000000000000000",
					"confirmationStatus": "CONFIRMED"
				},
				"patientLastName": {
					"name": "patientLastName",
					"value": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
					"confirmationStatus": "CONFIRMED"
				}
			}
		},
		"dialogState": "IN_PROGRESS"
	}
}
"""
# --------------------- Blockchain and Buffer Helpers --------------------------

def build_add_patient_response(event_request):
    req = {
        "request": {
            "type": "AddPatient",
            "data": {
                "practiceNo": int(event_request['intent']['slots']['practiceNo']['value']),
                "patientId": int(event_request['intent']['slots']['patientId']['value']),
                "firstName": event_request['intent']['slots']['patientFirstName']['value'],
                "lastName": event_request['intent']['slots']['patientLastName']['value']
            }
        }
    }

    url = settings['ethAPIEndPoint']

    #Be sure to add your api-key for AWS API Gateway
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    }

    res = requests.post(url,json=req,headers=headers).json()
    return res['response']['data']['transactionHash']

def build_sick_note_request(event_request, tx_hash):
    req = {
        "request": {
            "type": "AddNote",
            "data": {
                "practiceNo": int(event_request['intent']['slots']['practiceNo']['value']),
                "patientId": int(event_request['intent']['slots']['patientId']['value']),
                "sickDays": int(event_request['intent']['slots']['sickDays']['value']),
                "illnessDescription": event_request['intent']['slots']['illnessDescription']['value'],
                "mobileNo": event_request['intent']['slots']['mobileNo']['value'],
                "addPatientTxHash": tx_hash
            }
        }
    }

    url = settings['bufferAPIEndPoint']
    #Be sure to add your api-key for AWS API Gateway
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    }

    res = requests.post(url,json=req,headers=headers).json()
    if bool(os.environ['debug']):
        print(res)

def initiate_blockchain_tx(event_request):

    tx_hash = build_add_patient_response(event_request)
    build_sick_note_request(event_request, tx_hash)

# --------------- Helper to build responses ----------------------

def build_confirm_dialog_response(event_request, should_end_session):
    updatedSlots = {}

    for i in event_request['intent']['slots']:
        if i == 'patientLastName' or i == 'patientFirstName':
            editedValue = event_request['intent']['slots'][i]['value'].replace(" ", "").title()
        else:
            editedValue = event_request['intent']['slots'][i]['value']

        updatedSlots[i] = {
            'name': i,
            'value': editedValue,
            'confirmationStatus': 'CONFIRMED'
        }

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>Let\'s see if I got this right! Your practice number is, <say-as interpret-as='digits'>{}</say-as>. and {} {}'s identification number is <say-as interpret-as='digits'>{}</say-as>. {} will be away from work for {} days and the illness description is, {}. Lastly, the patient will receive their sick note reference number on the following mobile number, <say-as interpret-as='digits'>{}</say-as>. Is that correct Doctor?</speak>".format(updatedSlots['practiceNo']['value'],updatedSlots['patientFirstName']['value'],updatedSlots['patientLastName']['value'],updatedSlots['patientId']['value'],updatedSlots['patientFirstName']['value'],updatedSlots['sickDays']['value'],updatedSlots['illnessDescription']['value'],updatedSlots['mobileNo']['value'])
        },
        "directives": [
            {
                "type": "Dialog.ConfirmIntent",
                "updatedIntent": {
                    "name": event_request['intent']['name'],
                    "confirmationStatus": event_request['intent']['confirmationStatus'],
                    "slots": updatedSlots,

                }
            }
        ],
        "shouldEndSession": should_end_session
    }

def build_in_progress_dialog_response(event_request, should_end_session):
    return {
        "directives": [
            {
                "type": "Dialog.Delegate"
            }
        ],
        "shouldEndSession": should_end_session
    }

def build_on_start_dialog_response(event_request, should_end_session):
    return {
        "directives": [
            {
                "type": "Dialog.Delegate",
                "updatedIntent": {
                    "name": event_request['intent']['name'],
                    "confirmationStatus": event_request['intent']['confirmationStatus'],
                    "slots": event_request['intent']['slots'],

                }
            }
        ],
        "shouldEndSession": should_end_session
    }

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# ------------------- Functions to control skill's behavior --------------------

def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome Doctor, to the sick note blockchain skill. You can ask to draft a new sick note or learn more about this skill."
    reprompt_text = "How can I help you today?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def confirmed_response():
    session_attributes = {}
    card_title = "Good Bye"
    speech_output = "Thank you Doctor. The patient will receive the sick note reference number via SMS. Goodbye."
    reprompt_text = ""
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def dialog_response(event_request):
    session_attributes = {}
    should_end_session = False
    if event_request['dialogState'] == 'STARTED':
        return build_response(session_attributes, build_on_start_dialog_response(event_request, should_end_session))
    elif event_request['dialogState'] == 'IN_PROGRESS':
        if event_request['intent']['confirmationStatus'] == 'CONFIRMED':
            initiate_blockchain_tx(event_request)
            return confirmed_response()
        else:
            if 'value' in event_request['intent']['slots']['mobileNo']:
                return build_response(session_attributes, build_confirm_dialog_response(event_request, should_end_session))
            else:
                return build_response(session_attributes, build_in_progress_dialog_response(event_request, should_end_session))

# --------------- Events ------------------

def on_launch(launch_request, session):
    res = get_welcome_response()
    if bool(os.environ['debug']):
        print(res)

    return res

def dialog(event_request, session):
    res = dialog_response(event_request)
    if bool(os.environ['debug']):
        print(res)

    return res

# --------------- Main handler ------------------

def lambda_handler(event, context):

    if bool(os.environ['debug']):
        print(event['request'])
        print(event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        if event['request']['dialogState'] == 'STARTED' or event['request']['dialogState'] == 'IN_PROGRESS':
            return dialog(event['request'], event['session'])
