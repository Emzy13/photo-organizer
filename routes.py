import cv2
from flask import Flask, request, jsonify, send_file, render_template, Blueprint, redirect, url_for
import os
from models import db, Album, Photo
from werkzeug.utils import secure_filename
from pathlib import Path
from PIL import Image, ImageEnhance
from moviepy.editor import ImageSequenceClip
from fpdf import FPDF 

routes = Blueprint('routes', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@routes.route('/')
def home():
    albums = Album.query.all()
    return render_template('index.html', albums=albums)

@routes.route('/upload', methods=['POST'])
def upload_photo():
    album_name = request.form['album']
    user_id = 1  
    files = request.files.getlist('photos')

    album = Album.query.filter_by(name=album_name, user_id=user_id).first()
    if not album:
        album = Album(name=album_name, user_id=user_id)
        db.session.add(album)
        db.session.commit()

    for file in files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        photo = Photo(filename=filename, filepath=filepath, album_id=album.id)
        db.session.add(photo)

    db.session.commit()
    return jsonify({'message': 'Photos uploaded successfully', 'album': album_name}), 201

@routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@routes.route('/export/pdf', methods=['POST'])
def export_album_pdf():
    album_name = request.form.get('album')
    layout = request.form.get('layout')
    
    if not album_name or not layout:
        return jsonify({'message': 'Album name or layout not provided'}), 400

    album = Album.query.filter_by(name=album_name).first()
    if not album:
        return jsonify({'message': 'Album not found'}), 404

    photos = album.photos
    if not photos:
        return jsonify({'message': 'No photos in the album'}), 404

    pdf = FPDF()
    pdf.add_page()
    
    if layout == "single":
        for photo in photos:
            pdf.add_page()
            pdf.image(photo.filepath, x=10, y=10, w=190)  
            
    elif layout == "grid":
        x, y = 10, 10
        for i, photo in enumerate(photos):
            pdf.image(photo.filepath, x=x, y=y, w=90, h=60)  
            x += 95
            if x > 100:
                x = 10
                y += 65

    elif layout == "mosaic":
        if len(photos) > 0:
            pdf.image(photos[0].filepath, x=10, y=10, w=90)
        if len(photos) > 1:
            pdf.image(photos[1].filepath, x=110, y=60, w=90)
        if len(photos) > 2:
            pdf.image(photos[2].filepath, x=60, y=130, w=90)

    pdf_output_path = os.path.join("output", f"{album_name}.pdf")
    pdf.output(pdf_output_path)

    return send_file(pdf_output_path, as_attachment=True, download_name=f"{album_name}.pdf")

@routes.route('/export/video', methods=['POST'])
def export_album_video():
    album_name = request.form.get('album')
    
    if not album_name:
        return jsonify({'message': 'No album name provided'}), 400

    album = Album.query.filter_by(name=album_name).first()
    
    if not album:
        return jsonify({'message': 'Album not found'}), 404

    photos = album.photos
    
    if not photos:
        return jsonify({'message': 'No photos in the album'}), 404

    target_size = (640, 360)  
    resized_images = []

    for photo in photos:
        image_path = os.path.join('uploads', photo.filename)
        image = cv2.imread(image_path)
        
        if image is None:
            continue
        
        resized_image = cv2.resize(image, target_size)
        temp_image_path = os.path.join('uploads', f"resized_{photo.filename}")
        cv2.imwrite(temp_image_path, resized_image)
        resized_images.append(temp_image_path)

    video_output_path = os.path.join("output", f"{album_name}.mp4")
    clip = ImageSequenceClip(resized_images, fps=1) 
    clip.write_videofile(video_output_path, codec="libx264", audio=False)

    for temp_image_path in resized_images:
        os.remove(temp_image_path)

    return send_file(video_output_path, as_attachment=True, download_name=f"{album_name}.mp4")

@routes.route('/delete/album', methods=['POST'])
def delete_album():
    album_name = request.form.get('album_name')
    
    if not album_name:
        return jsonify({'message': 'No album name provided'}), 400
    
    album = Album.query.filter_by(name=album_name).first()
    if not album:
        return jsonify({'message': 'Album not found'}), 404
    
    photos = Photo.query.filter_by(album_id=album.id).all()
    for photo in photos:
        db.session.delete(photo)
 
    db.session.delete(album)
    db.session.commit()
    
    return redirect(url_for('routes.home'))

@routes.route('/delete/photo/<filename>', methods=['DELETE'])
def delete_photo(filename):
    photo = Photo.query.filter_by(filename=filename).first()
    if not photo:
        return jsonify({'message': 'Photo not found'}), 404

    if os.path.exists(photo.filepath):
        os.remove(photo.filepath)

    db.session.delete(photo)
    db.session.commit()

    return jsonify({'message': f'Photo {filename} has been deleted successfully'}), 200


@routes.route('/edit/<filename>', methods=['POST'])
def edit_photo(filename):
    filepath = os.path.join('uploads', filename)
    if not os.path.exists(filepath):
        return jsonify({'message': 'Photo not found'}), 404
    
    image = Image.open(filepath)
    
    action = request.args.get('action')
    if action == 'crop':
        left = int(request.args['left'])
        top = int(request.args['top'])
        right = int(request.args['right'])
        bottom = int(request.args['bottom'])
        image = image.crop((left, top, right, bottom))
    elif action == 'rotate':
        degrees = int(request.args['degrees'])
        image = image.rotate(degrees)
    elif action == 'brightness':
        factor = float(request.args['factor'])
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(factor)

    image.save(filepath)

    return jsonify({'message': 'Photo edited successfully'}), 200

app = Flask(__name__)
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)