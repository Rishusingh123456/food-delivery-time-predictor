from flask import Flask, render_template, request
import pickle
import requests

app = Flask(__name__)

# ✅ Load model
model = pickle.load(open("model.pkl", "rb"))

# 🔥 Add your API key
API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImZlZmQxMDQ2ZjdkNzRhOTViNWM1Y2IzZTRkYWMxODAzIiwiaCI6Im11cm11cjY0In0="


# 🚀 DISTANCE FUNCTION (FULLY FIXED)
def get_distance(origin, destination):
    try:
        geo_url = "https://api.openrouteservice.org/geocode/search"

        # 🔹 ORIGIN
        res1 = requests.get(geo_url, params={
            "api_key": API_KEY,
            "text": origin.strip() + ", India"
        }).json()

        if not res1.get("features"):
            print("❌ Origin not found")
            return None, None, None, None, None, None

        start = res1["features"][0]["geometry"]["coordinates"]

        # 🔹 DESTINATION
        res2 = requests.get(geo_url, params={
            "api_key": API_KEY,
            "text": destination.strip() + ", India"
        }).json()

        if not res2.get("features"):
            print("❌ Destination not found")
            return None, None, None, None, None, None

        end = res2["features"][0]["geometry"]["coordinates"]

        # 🔍 DEBUG (see real coordinates)
        print("ORIGIN:", origin, "→", start)
        print("DESTINATION:", destination, "→", end)

        # 🔥 FIX: HANDLE SAME / VERY CLOSE LOCATIONS
        if abs(start[0] - end[0]) < 0.001 and abs(start[1] - end[1]) < 0.001:
            print("⚠ Locations too close → adjusting")
            end = [end[0] + 0.01, end[1] + 0.01]

        # 🔥 ROUTE API
        route = requests.post(
            "https://api.openrouteservice.org/v2/directions/driving-car",
            json={"coordinates": [start, end]},
            headers={
                "Authorization": API_KEY,
                "Content-Type": "application/json"
            }
        )

        if route.status_code != 200:
            print("❌ Route API Error:", route.text)
            return None, None, None, None, None, None

        data = route.json()
        print("🛣 ROUTE DATA:", data)

        # 🔥 SAFE CHECK
        if "routes" not in data or len(data["routes"]) == 0:
            print("❌ No routes found")
            return None, None, None, None, None, None

        summary = data["routes"][0].get("summary", {})

        distance = summary.get("distance")
        duration = summary.get("duration")

        if distance is None or duration is None:
            print("❌ distance/duration missing:", summary)
            return None, None, None, None, None, None

        distance = distance / 1000   # km
        duration = duration / 60     # minutes

        lat1, lon1 = start[1], start[0]
        lat2, lon2 = end[1], end[0]

        return round(distance, 2), round(duration, 2), lat1, lon1, lat2, lon2

    except Exception as e:
        print("❌ ERROR:", e)
        return None, None, None, None, None, None


# 🏠 HOME
@app.route("/")
def home():
    return render_template("index.html")


# 🚀 PREDICT
@app.route("/predict", methods=["POST"])
def predict():
    try:
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        prep_time = request.form.get("prep_time")
        traffic = request.form.get("traffic")

        print("📥 INPUT:", origin, destination, prep_time, traffic)

        # ✅ VALIDATION
        if not origin or not destination or not prep_time:
            return render_template(
                "index.html",
                result="⚠ Please fill all fields",
                distance="--",
                travel_time="--"
            )

        prep_time = float(prep_time)
        traffic = int(traffic)

        # 🔥 GET DISTANCE
        distance, travel_time, lat1, lon1, lat2, lon2 = get_distance(origin, destination)

        if distance is None:
            return render_template(
                "index.html",
                result="❌ Invalid location or API error",
                distance="--",
                travel_time="--"
            )

        # 🔥 LIMIT DISTANCE (REALISTIC LIKE SWIGGY)
        if distance > 50:
            return render_template(
                "index.html",
                result="⚠ Delivery not available (Too far)",
                distance=distance,
                travel_time=travel_time,
                lat1=lat1,
                lon1=lon1,
                lat2=lat2,
                lon2=lon2
            )

        # ✅ MODEL PREDICTION
        try:
            prediction = model.predict([[distance, prep_time, traffic]])[0]
        except:
            prediction = prep_time

        total_time = prediction + travel_time

        return render_template(
            "index.html",
            result=round(total_time, 2),
            distance=distance,
            travel_time=travel_time,
            lat1=lat1,
            lon1=lon1,
            lat2=lat2,
            lon2=lon2
        )

    except Exception as e:
        print("❌ ERROR:", e)
        return render_template(
            "index.html",
            result="❌ Something went wrong",
            distance="--",
            travel_time="--"
        )


# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)