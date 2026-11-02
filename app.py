
from flask import Flask, render_template, request, jsonify
import threading

app = Flask(__name__)

# Create 12 seats
seats = {
    f"A{i}": {
        "status": "Available",
        "passenger": None
    }
    for i in range(1, 13)
}

# Create Mutex Lock
seat_lock = threading.Lock()


# Display dashboard
@app.route("/")
def home():
    return render_template("index.html")


# Get current seat information
@app.route("/api/seats", methods=["GET"])
def get_seats():
    with seat_lock:
        return jsonify(seats)


# Book a seat
@app.route("/api/book", methods=["POST"])
def book_seat():

    data = request.get_json()

    seat_id = data.get("seat")
    passenger = data.get("passenger", "").strip()

    if seat_id not in seats:
        return jsonify({
            "success": False,
            "message": "Invalid seat selected"
        }), 400

    if not passenger:
        return jsonify({
            "success": False,
            "message": "Please enter passenger name"
        }), 400

    # MUTEX PROTECTION
    with seat_lock:

        # Critical Section
        if seats[seat_id]["status"] == "Available":

            seats[seat_id]["status"] = "Booked"
            seats[seat_id]["passenger"] = passenger

            return jsonify({
                "success": True,
                "message": f"{passenger} successfully booked {seat_id}"
            })

        else:
            return jsonify({
                "success": False,
                "message": f"{seat_id} is already booked"
            })


# Cancel a booking
@app.route("/api/cancel", methods=["POST"])
def cancel_booking():

    data = request.get_json()

    seat_id = data.get("seat")

    if seat_id not in seats:
        return jsonify({
            "success": False,
            "message": "Invalid seat selected"
        }), 400

    with seat_lock:

        if seats[seat_id]["status"] == "Booked":

            passenger = seats[seat_id]["passenger"]

            seats[seat_id]["status"] = "Available"
            seats[seat_id]["passenger"] = None

            return jsonify({
                "success": True,
                "message": f"Booking cancelled for {passenger}"
            })

        else:
            return jsonify({
                "success": False,
                "message": "This seat is not booked"
            })
@app.route("/api/simultaneous-test", methods=["POST"])
def simultaneous_test():
    data = request.get_json()

    seat_id = data.get("seat")

    if seat_id not in seats:
        return jsonify({
            "success": False,
            "message": "Invalid seat selected"
        }), 400

    passenger_names = ["Passenger 1", "Passenger 2"]

    results = []
    start_together = threading.Barrier(2)

    def attempt_booking(passenger):
        start_together.wait()

        with seat_lock:
            if seats[seat_id]["status"] == "Available":
                seats[seat_id]["status"] = "Booked"
                seats[seat_id]["passenger"] = passenger

                results.append({
                    "passenger": passenger,
                    "result": "Booking successful"
                })
            else:
                results.append({
                    "passenger": passenger,
                    "result": "Booking rejected - Seat already booked"
                })

    thread1 = threading.Thread(
        target=attempt_booking,
        args=(passenger_names[0],)
    )

    thread2 = threading.Thread(
        target=attempt_booking,
        args=(passenger_names[1],)
    )

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    return jsonify({
        "success": True,
        "seat": seat_id,
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
