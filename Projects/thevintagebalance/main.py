from flask import Flask, render_template
from datetime import datetime
app = Flask(__name__)

@app.route('/')
def index():
    # In a production app, you might fetch these dynamically or store them in a database.
    # For now, we pass a list of curated "vintage watch" aesthetic images to the template.
    
    # NOTE: Replace these URLs with the actual image links from @thevintagebalance 
    # or host the images in your 'static' folder.
    gallery_images = [
        {
            "url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&q=80&w=1000",
            "caption": "The Daily Driver"
        },
        {
            "url": "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?auto=format&fit=crop&q=80&w=1000",
            "caption": "Patina & Precision"
        },
        {
            "url": "https://images.unsplash.com/photo-1542496658-e33a6d0d50f6?auto=format&fit=crop&q=80&w=1000",
            "caption": "Golden Era"
        },
        {
            "url": "https://images.unsplash.com/photo-1509048191080-d2984bad6ae5?auto=format&fit=crop&q=80&w=1000",
            "caption": "Macro Details"
        },
        {
            "url": "https://images.unsplash.com/photo-1523170335258-f5ed11844a49?auto=format&fit=crop&q=80&w=1000",
            "caption": "Timeless Elegance"
        },
        {
            "url": "https://images.unsplash.com/photo-1547996160-81dfa63595aa?auto=format&fit=crop&q=80&w=1000",
            "caption": "The Chronograph"
        }
    ]
    
    yearNow = datetime.now().year
    return render_template('index.html', images=gallery_images, yearNow=yearNow)

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App Engine,
    # a webserver process such as Gunicorn will serve the app.
    app.run(host='127.0.0.1', port=8080, debug=True)