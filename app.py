import os
import json
from flask import Flask
from flask_cors import CORS
from services.create_alerts import create_alerts
from services.save_alerts import save_alerts

app = Flask(__name__)

cors = CORS(app, resource={r"/*": {"origins": "*"}})


@app.route("/", methods=["GET"])
def index():
    alerts_list = create_alerts()
    save_alerts(alerts_list)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "alerts sent to teacher",
            "content": alerts_list
        }),
    }


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
