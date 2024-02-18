from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import hashlib
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
class RequestHandler(BaseHTTPRequestHandler):
    # Post request configuration
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            json_data = json.loads(post_data.decode('utf-8'))
            x = json_data.get('x')
            y = json_data.get('y')
            color = json_data.get('color')

            if x is not None and y is not None and color is not None:
                # Save to file
                loc_data = {"x": {x}, "y": {y}, "color": {color}}
                id = self.generate_unique_id(loc_data)
                self.writejson(f'x: {x}, y: {y}, color: {color}, state: Task queued\n')
                data = {
                    "id": id,
                    "color": color,
                    "state": "Task queued"
                }
                try:
                    # missions.child("mission_teknofest").push(data)
                    missions.child("id").push(data)
                    print("Data saved successfully")
                except:
                    print("Data not saved")
                # Send response to client
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                response_message = f'Post data saved successfully. Your id={id}\n'
                self.wfile.write(response_message.encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'Incorrect post data.\n')

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Incorrect JSON format.\n')
    
    # Create log file
    def writejson(self,girdi, dosya_adı="log.txt"):
        try:
            with open(dosya_adı, 'a') as dosya:
                dosya.write(girdi)
            print(f'writing process completed successfully.')
        except Exception as err:
            print(f"Writing file error: {err}")
            
    # Hash code generated from location data
    def generate_unique_id(self,location_data):
        # location_data içindeki bilgilerden benzersiz bir id oluştur
        id_str = f"{location_data['x']}_{location_data['y']}"
        
        # id'yi hashlib kullanarak özel bir hash değerine dönüştür
        unique_id = hashlib.sha1(id_str.encode()).hexdigest()
        
        return unique_id
    
if __name__ == '__main__':
    cred = credentials.Certificate("deneme.json")
    # firebase_admin.initialize_app(cred,{"databaseURL":"https://missions-balsa-default-rtdb.firebaseio.com/"})
    firebase_admin.initialize_app(cred,{"databaseURL":"https://fir-deneme-5067f-default-rtdb.firebaseio.com/"})
    missions = db.reference()
    PORT = 8000
    server = HTTPServer(('localhost', PORT), RequestHandler)
    print(f'Serving on port {PORT}')
    server.serve_forever()
