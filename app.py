from flask import Flask
from flask import request
from flask import send_from_directory
from flask import jsonify
import smtplib

app = Flask(__name__, static_url_path='')

from thought import converse

@app.route("/input")
def recieve_input():
	print('GOT REQUEST! ' + request.args.get('chunk'))
	input_chunk = request.args.get('chunk')
	response, final_data = converse(input_chunk)
	return jsonify(response=response, finalData=final_data)

@app.route('/email', methods = ['GET', 'POST'])
def handle_email():
	if request.method == "POST":

		print("Email data")
		print(request.form.to_dict())

		username = 'bhagatsingh2297@gmail.com'
		password = 'Iloveemu22'

		email_id = request.form['email_id']
		message = request.form['message']

		print(email_id)
		print(message)

		server = smtplib.SMTP('smtp.gmail.com', 587)

		server.ehlo()
		server.starttls()
		server.ehlo()

		server.login(username, password)
		server.sendmail(username, email_id, message)

	return send_from_directory('', 'main.html')

@app.route('/main.html')
def render_input():
	return send_from_directory('', 'main.html')

@app.route('/artyom.window.min.js')
def send_js(): return send_from_directory('', 'artyom.window.min.js')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=3000, debug=True)
