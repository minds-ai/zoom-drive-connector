"""

The webhook will initiate the download. 
The webhook has to listen on port 80 or 443 according to 
the zoom documentation.



"""


from flask import Flask, request, abort

import threading

app = Flask(__name__)


def handle_response(data):
  print("Going to work on: ", data)
  
  return


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print(request.json)
        
        # Verification of the incoming json/ID
        
        # Take async follow up actions
        t = threading.Thread(target=handle_response, args=(request.json,))
        t.start()

        
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    app.run(port=12399, debug=True,host='0.0.0.0')
    
   #threaded = True