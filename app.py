from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont, ImageOps
import io, base64

app = Flask(__name__)

def process_image(image, data):
    # 1. CROP LOGIC (Ithu thaan mukkiyam)
    if data.get('crop_x'):
        w, h = image.size
        cx = float(data.get('crop_x')) * w
        cy = float(data.get('crop_y')) * h
        cw = float(data.get('crop_w')) * w
        ch = float(data.get('crop_h')) * h
        image = image.crop((cx, cy, cx + cw, cy + ch))

    # 2. FILTERS (Working now)
    f = data.get('filter', 'none')
    if f == 'grayscale': image = ImageOps.grayscale(image).convert("RGB")
    elif f == 'sepia': image = ImageOps.colorize(ImageOps.grayscale(image), "#704214", "#C0A080").convert("RGB")
    elif f == 'invert': image = ImageOps.invert(image)

    # 3. BRIGHTNESS & CONTRAST
    b = float(data.get('brightness', 1.0))
    c = float(data.get('contrast', 1.0))
    image = ImageEnhance.Brightness(image).enhance(b)
    image = ImageEnhance.Contrast(image).enhance(c)

    # 4. TEXT SCALING & COLOR
    txt = data.get('text', '')
    if txt:
        draw = ImageDraw.Draw(image)
        iw, ih = image.size
        f_size = int((int(data.get('text_size', 40)) / 800) * iw)
        try:
            font = ImageFont.truetype("arial.ttf", f_size)
        except:
            font = ImageFont.load_default()
        
        tx = float(data.get('text_x', 0.2)) * iw
        ty = float(data.get('text_y', 0.2)) * ih
        draw.text((tx, ty), txt, fill=data.get('text_color', 'white'), font=font)
    
    return image

@app.route('/')
def index(): return render_template('index.html')

@app.route('/process', methods=['POST'])
def edit_image():
    file = request.files.get('image')
    if not file: return "Error", 400
    img = Image.open(file.stream).convert("RGB")
    mode = request.form.get('mode', 'preview')
    
    # Process original settings
    img = process_image(img, request.form)
    
    if mode == 'preview': img.thumbnail((800, 800))
    
    img_io = io.BytesIO()
    if mode == 'download':
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='edited.jpg')
    
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return jsonify({'image': base64.b64encode(img_io.getvalue()).decode('utf-8')})

if __name__ == '__main__': app.run(debug=True)