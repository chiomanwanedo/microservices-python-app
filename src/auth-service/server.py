import jwt, datetime, os, sys
import psycopg2
from flask import Flask, request, jsonify
from flask_cors import CORS

server = Flask(__name__)
CORS(server)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DATABASE_HOST'),
        database=os.getenv('DATABASE_NAME'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        port=int(os.getenv('DATABASE_PORT', 5432))
    )

def CreateJWT(username, secret, authz):
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.now(tz=datetime.timezone.utc),
            "admin": authz,
        },
        secret,
        algorithm="HS256"
    )

@server.route('/login', methods=['POST'])
def login():
    try:
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({"error": "Missing auth headers"}), 401

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT email, password FROM {os.getenv('AUTH_TABLE')} WHERE email = %s", (auth.username,))
        row = cur.fetchone()

        if not row or row[1] != auth.password:
            return jsonify({"error": "Invalid credentials"}), 401

        token = CreateJWT(auth.username, os.environ['JWT_SECRET'], True)
        return token if isinstance(token, str) else token.decode('utf-8')
    except Exception as e:
        sys.stderr.write(f"🔥 Exception in /login: {e}\n")
        return jsonify({"error": "Internal server error"}), 500

@server.route('/validate', methods=['GET', 'POST'])
def validate():
    token = request.headers.get('Authorization')
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = token.split()[1]
    try:
        decoded = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=["HS256"])
        return jsonify(decoded), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@server.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = token.split()[1]
    try:
        decoded = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=["HS256"])
        return jsonify({
            "message": "✅ Protected route accessed!",
            "user": decoded.get("username"),
            "admin": decoded.get("admin", False)
        }), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

@server.route('/notify', methods=['POST'])
def notify():
    token = request.headers.get('Authorization')
    if not token or not token.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = token.split()[1]
    try:
        jwt.decode(token, os.environ['JWT_SECRET'], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.get_json()
    email = data.get("email")
    message = data.get("message")

    if not email or not message:
        return jsonify({"error": "Missing email or message"}), 400

    print(f"📢 Notifying {email}: {message}")
    return jsonify({"status": "Notification sent!", "email": email}), 200

if __name__ == '__main__':
    sys.stderr.write("🚨 Auth service is starting with DEBUG LOGGING ENABLED\n")
    server.run(host='0.0.0.0', port=5000, debug=True)
