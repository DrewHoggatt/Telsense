import os
import csv
from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io

# 1. Setup your client
client = genai.Client(api_key="AIzaSyBpcdyqLdICnHsHhAu9XVefPCznk1uqhzg")

# 2. Load door locations from CSV
door_locations = []
csv_path = "locations.csv"
try:
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            door_locations.append({
                "name": row["Door Name"],
                "x": float(row["x"]),
                "y": float(row["y"])
            })
    print(f"Loaded {len(door_locations)} door locations from {csv_path}")
except FileNotFoundError:
    print(f"Warning: {csv_path} not found. Continuing without door markers.")
except Exception as e:
    print(f"Error reading {csv_path}: {e}")

# 3. Load your 2D Floor Plan image
# Replace 'floorplan.png' with your local file path
image_path = "floorplan.jpg"

image = Image.open(image_path)
iWidth = image.width
iHeight = image.height

for location in door_locations:
    location['x'] = location['x'] * iWidth
    location['y'] = location['y'] * iHeight

# Draw red squares on the image for each door location
image_rgb = image.convert('RGB')  # Ensure RGB mode for drawing
draw = ImageDraw.Draw(image_rgb)

for location in door_locations:
    x = int(location['x'])
    y = int(location['y'])
    # Draw a 10x10 red square centered on the coordinates
    # Top-left corner: (x-5, y-5), Bottom-right corner: (x+5, y+5)
    draw.rectangle([x-5, y-5, x+5, y+5], fill='red', outline='red')
    draw.text((x+10, y -5), location['name'], fill='blue')

# Save the image with red squares as step1.png
image_rgb.save("step1.png")
print(f"Saved image with {len(door_locations)} door markers to step1.png")
with open("step1.png", "rb") as f:
    image_bytes = f.read()

# 4. Create the prompt
# We instruct the model to act as a 3D artist
prompt = """
The file is a 2d floor plan image with a red square at each door location. 
Remove borders and any excess white space around the edges of the image.
Increase the image to high resolution.
** IT IS CRITICAL THAT THE FINAL IMAGE HAS THE SAME RED BLOCKS LABELLED WITH THE SAME TEXT CONTENT **
For each red square with a blue label, make the label look nice.
Useack text to label the same red block avoiding clashing with 
drawing lines or other text.

  """

prompt = """
The file is a 2d floor plan.
Generate a 3d render of the floor plan.
Ensure that the floor covering is white and the walls are grey.
Highlight colours can be tints of html colour #fed103

"""

# 5. Send the request
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"]
        )
    )

    # 6. Save the result
    # Check if response contains image data
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                img_data = part.inline_data.data
                img = Image.open(io.BytesIO(img_data))
                img.save("render_output.png")
                print("Success! Saved to render_output.png")
                break
            elif hasattr(part, 'text') and part.text:
                # If model returns text instead of image, save it for debugging
                print("Model returned text response:")
                print(part.text)
                print("\nNote: Gemini models analyze images but don't generate them.")
                print("For image generation, consider using OpenAI DALL-E, Stable Diffusion, or similar services.")
    else:
        print("No response content received from the model.")

except Exception as e:
    print(f"Error: {e}")