import os
import uuid
import requests
from flask import Flask, Response, request
from ics import Calendar, Event
from datetime import datetime

app = Flask(__name__)
XANO_BASE_URL = os.environ.get("XANO_BASE_URL")

@app.route("/<listing_id>.ics", methods=["GET"])
def generate_ics(listing_id):
    if not XANO_BASE_URL or not listing_id:
        return Response("Missing configuration or listing ID", status=400)

    try:
        res = requests.get(XANO_BASE_URL, params={"listing_id": listing_id})
        res.raise_for_status()
        bookings = res.json()

        calendar = Calendar()
        namespace = uuid.UUID("2f1d3dfc-b806-4542-996c-e6f27f1d9a17")

        for booking in bookings:
            uid = str(uuid.uuid5(namespace, f"{listing_id}-{booking.get('uid')}"))
            platform = (booking.get("source_platform") or "").lower()
            raw_uid = booking.get("uid") or ""
            booking_link = ""

            if "rvshare" in platform and len(raw_uid) > 10 and "booking" not in raw_uid.lower():
                booking_link = "https://rvshare.com/dashboard/reservations"
            elif "outdoorsy" in platform and "booking" in raw_uid.lower():
                import re
                match = re.search(r"(\d{6,})", raw_uid)
                if match:
                    booking_link = f"https://www.outdoorsy.com/dashboard/bookings/{match.group(1)}"
            elif "rvezy" in platform and len(raw_uid) > 10:
                booking_link = f"https://www.rvezy.com/owner/reservations/{raw_uid}"
            elif "airbnb" in platform:
                booking_link = "https://www.airbnb.com/hosting/reservations"
            elif "hipcamp" in platform:
                booking_link = "View this booking by logging into your Hipcamp host dashboard."
            elif "camplify" in platform:
                booking_link = "Log in to your Camplify host dashboard to view booking details."
            elif "yescapa" in platform:
                booking_link = "Log in to your Yescapa dashboard to view booking details."

            event = Event()
            event.name = ", ".join(filter(None, [booking.get("source_platform"), booking.get("summary")])) or "booking"
            event.begin = booking.get("start_date")
            event.end = booking.get("end_date")
            event.uid = uid
            event.description = f"{booking.get('description', '')}\nBooking Link: {booking_link}".strip()
            event.location = booking.get("location", "")
            event.make_all_day()
            calendar.events.add(event)

        return Response(str(calendar), mimetype="text/calendar")

    except Exception as e:
        return Response(f"Server error: {str(e)}", status=500)
