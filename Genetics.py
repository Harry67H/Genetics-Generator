from flask import Flask, render_template_string, request, redirect, url_for
from PIL import Image, ImageDraw
import io, base64, random

app = Flask(__name__)
characters = {}  # Stores all characters

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Stickman Genetics Generator</title>
<style>
body { font-family: Arial; margin:0; padding:0; }
.controls { padding:10px; background:#eee; }
#canvasWrapper { position:relative; width:100%; height:600px; overflow:auto; border:1px solid #ccc; }
#canvas { position:relative; width:5000px; height:5000px; background:white; }
.character { position:absolute; cursor:pointer; border:1px solid transparent; }
.character.selected { border:1px solid red; }
</style>
</head>
<body>
<div class="controls">
  <form id="addForm" action="/add_character" method="post" enctype="multipart/form-data">
    Name: <input type="text" name="name" required>
    Upload Shape: <input type="file" name="shape">
    Strength: <input type="number" name="strength" value="5" min="1" max="100">
    Speed: <input type="number" name="speed" value="5" min="1" max="100">
    Height: <input type="number" name="height" value="100" min="10" max="300">
    Skin: <input type="color" name="skin" value="#ffcc99">
    Eye: <input type="color" name="eye" value="#000000">
    Hair: <input type="color" name="hair" value="#000000">
    <button type="submit">Add Character</button>
  </form>
</div>

<div class="controls">
  <form id="babyForm" action="/make_baby" method="post">
    Parent 1: <input type="text" name="parent1" required>
    Parent 2: <input type="text" name="parent2" required>
    Baby Name: <input type="text" name="baby_name" required>
    <button type="submit">Make Baby</button>
  </form>
</div>

<div class="controls">
  <button onclick="ageSelected()">+1 Year (Age Selected Baby)</button>
</div>

<div id="canvasWrapper">
  <div id="canvas">
    {% for name, char in characters.items() %}
    <div class="character" style="left:{{char['x']}}px; top:{{char['y']}}px;" 
      onclick="selectCharacter('{{name}}', event)">
      <img src="data:image/png;base64,{{char['img']}}">
    </div>
    {% endfor %}
  </div>
</div>

<script>
let selectedChar = null;
function selectCharacter(name, event){
  if(selectedChar) selectedChar.classList.remove('selected');
  selectedChar = event.currentTarget;
  selectedChar.classList.add('selected');
  alert('Selected '+name+'!\\nStats:\\nStrength: '+{{characters}}[name]['strength']+
        '\\nSpeed: '+{{characters}}[name]['speed']+
        '\\nHeight: '+{{characters}}[name]['height']);
}

function ageSelected(){
  if(!selectedChar){ alert('Select a baby first'); return; }
  fetch('/age', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name:selectedChar.querySelector('img').alt})
  }).then(()=> location.reload());
}
</script>
</body>
</html>
'''

def image_to_black_silhouette(image):
    image = image.convert("RGBA")
    datas = image.getdata()
    newData = []
    for item in datas:
        if item[3] == 0:
            newData.append((255,255,255,0))
        else:
            newData.append((0,0,0,255))
    image.putdata(newData)
    return image

def pil_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def average_color(color1, color2):
    r = (color1[0]+color2[0])//2
    g = (color1[1]+color2[1])//2
    b = (color1[2]+color2[2])//2
    return (r,g,b)

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

@app.route('/')
def index():
    return render_template_string(HTML, characters=characters)

@app.route('/add_character', methods=['POST'])
def add_character():
    name = request.form['name']
    strength = int(request.form['strength'])
    speed = int(request.form['speed'])
    height = int(request.form['height'])
    skin = request.form['skin']
    eye = request.form['eye']
    hair = request.form['hair']

    x, y = random.randint(50,2000), random.randint(50,2000)

    file = request.files.get('shape')
    if file and file.filename != '':
        img = Image.open(file)
        img = image_to_black_silhouette(img)
    else:
        img = Image.new('RGBA', (50,100), (255,255,255,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((15,0,35,20), fill=hex_to_rgb(skin))
        draw.rectangle((24,20,26,80), fill=hex_to_rgb(skin))
        draw.line((24,40,0,70), fill=hex_to_rgb(skin), width=2)
        draw.line((26,40,50,70), fill=hex_to_rgb(skin), width=2)
        draw.line((24,80,0,100), fill=hex_to_rgb(skin), width=2)
        draw.line((26,80,50,100), fill=hex_to_rgb(skin), width=2)
        draw.ellipse((20,5,23,8), fill=hex_to_rgb(eye))
        draw.ellipse((27,5,30,8), fill=hex_to_rgb(eye))

    characters[name] = {
        'name': name, 'strength': strength, 'speed': speed, 'height': height,
        'skin': skin, 'eye': eye, 'hair': hair,
        'img': pil_to_base64(img), 'x': x, 'y': y, 'age': 0
    }
    return redirect(url_for('index'))

@app.route('/make_baby', methods=['POST'])
def make_baby():
    p1 = request.form['parent1']
    p2 = request.form['parent2']
    baby_name = request.form['baby_name']
    if p1 not in characters or p2 not in characters:
        return "Parent not found!", 400

    parent1 = characters[p1]
    parent2 = characters[p2]

    strength = (parent1['strength'] + parent2['strength'])//2
    speed = (parent1['speed'] + parent2['speed'])//2
    height = (parent1['height'] + parent2['height'])//2

    skin = rgb_to_hex(average_color(hex_to_rgb(parent1['skin']), hex_to_rgb(parent2['skin'])))
    eye = rgb_to_hex(average_color(hex_to_rgb(parent1['eye']), hex_to_rgb(parent2['eye'])))
    hair = rgb_to_hex(average_color(hex_to_rgb(parent1['hair']), hex_to_rgb(parent2['hair'])))

    img1 = Image.open(io.BytesIO(base64.b64decode(parent1['img'])))
    img2 = Image.open(io.BytesIO(base64.b64decode(parent2['img'])))
    max_w = max(img1.width, img2.width)
    max_h = max(img1.height, img2.height)
    baby_img = Image.new('RGBA', (max_w, max_h), (255,255,255,0))
    baby_img.paste(img1, ((max_w - img1.width)//2, (max_h - img1.height)//2), img1)
    baby_img.paste(img2, ((max_w - img2.width)//2, (max_h - img2.height)//2), img2)
    baby_img = image_to_black_silhouette(baby_img)

    x, y = random.randint(50,2000), random.randint(50,2000)

    characters[baby_name] = {
        'name': baby_name, 'strength': strength, 'speed': speed, 'height': height,
        'skin': skin, 'eye': eye, 'hair': hair,
        'img': pil_to_base64(baby_img), 'x': x, 'y': y, 'age': 0
    }
    return redirect(url_for('index'))

@app.route('/age', methods=['POST'])
def age():
    from flask import request
    data = request.get_json()
    name = data['name']
    if name not in characters: return "Not found",400
    char = characters[name]
    char['age'] += 1
    char['strength'] += max(1, char['strength']//10)
    char['speed'] += max(1, char['speed']//10)
    char['height'] += max(1, char['height']//20)
    return '',200

if __name__ == '__main__':
    app.run(debug=True)
